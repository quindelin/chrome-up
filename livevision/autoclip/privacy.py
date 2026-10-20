"""Privacy blur: find faces and blur them, togglable by voice.

Two drivers, one switch:

  clip  — every clip autoclip renders gets its faces blurred (ffmpeg
          `crop` + `boxblur` + `overlay`, one patch per tracked face).
  obs   — the live OBS program output gets blurred faces too. OBS has no
          "blur this rectangle" primitive, so we build one: a second scene
          (`PrivacyBlur`) holds one cropped copy of the *same* video source
          per face, positioned exactly over the face, and that scene carries
          a single built-in Blur filter. One extra scene, one blur pass, no
          duplicate decoders and no plugins.

The switch is a single boolean, persisted to `privacy.json` in the workdir.
It is flipped by voice ("blur faces" / "unblur" / "toggle face blur"), by
REST / MCP / CLI, or by the HUD. Every change publishes a `privacy_status`
event on the bus so the overlay can badge it.

Guardrails, same spirit as the rest of autoclip:

  * `privacy.enabled: false` (default) -> nothing runs: no cv2, no ffmpeg
    scan, no obs-websocket connection, no thread.
  * OpenCV is optional. Missing cv2 degrades to "detector unavailable";
    clips still render, just unblurred.
  * The OBS driver touches *only* a scene it created itself. Unknown
    sources, missing RPCs and OBS refusals all come back as
    `{"ok": false, "message": ...}` — never an exception.

Coordinates are handled in one place: face boxes are always produced in the
same pixel space they will be painted in. For clips that means "after the
reframe filter" (we decode the clip *through* the reframe chain before
detecting), so the boxes land correctly on the vertical crop.
"""
from __future__ import annotations

import base64
import json
import math
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None

try:
    import cv2
except Exception:  # pragma: no cover - optional dependency
    cv2 = None

from .util import clamp, ensure_dir, run

# Spoken targets that mean "the privacy blur", for `toggle <target>`.
PRIVACY_TARGETS = {"face", "faces", "faceblur", "face blur", "faceblurring",
                   "privacy", "privacymode", "privacy mode", "privacyblur",
                   "privacy blur", "blur", "blurring", "facesblur"}

# obs-websocket input kinds we consider "the video" when autodetecting.
VIDEO_KINDS = ("ffmpeg_source", "vlc_source", "dshow_input", "av_capture",
               "av_capture_input_v2", "v4l2_input", "window_capture",
               "monitor_capture", "game_capture", "browser_source")


def is_privacy_target(target: str) -> bool:
    """True when `toggle <target>` / `<intent> <target>` means privacy blur."""
    t = " ".join((target or "").lower().replace("-", " ").replace("_", " ").split())
    if not t:
        return False
    if t in PRIVACY_TARGETS:
        return True
    words = set(t.split())
    return bool(words & {"face", "faces", "privacy", "blur"})


# --------------------------------------------------------------------------- boxes
@dataclass
class FaceBox:
    """One detected face, in the pixel space it was detected in."""
    x: int
    y: int
    w: int
    h: int
    score: float = 1.0


@dataclass
class BlurBox:
    """A face patch plus the time window it is painted in (clip seconds)."""
    t0: float
    t1: float
    x: int
    y: int
    w: int
    h: int

    def to_dict(self) -> dict:
        return {"t0": round(self.t0, 3), "t1": round(self.t1, 3),
                "x": self.x, "y": self.y, "w": self.w, "h": self.h}


def privacy_chain(boxes: List[BlurBox], strength: int = 20) -> str:
    """ffmpeg filtergraph fragment that blurs `boxes`.

    Appended to the reframe chain, so it consumes whatever that produced. The
    final `overlay` is deliberately left unlabelled — the caller owns the
    output label (it may still need to burn captions on top).
    Empty input -> empty string, and the caller uses the stream as-is.

    Each patch is `crop` the region out of a fresh copy of the frame, `boxblur`
    it, then `overlay` it back at the same coordinates for its time window.
    Disabled overlays pass straight through, so patches outside their window
    cost nothing but a crop.
    """
    if not boxes:
        return ""
    n = len(boxes)
    parts = [f"split={n + 1}[b]" + "".join(f"[s{i}]" for i in range(n))]
    cur = "b"
    for i, b in enumerate(boxes):
        radius = int(clamp(strength, 2, max(2, min(b.w, b.h) // 2)))
        parts.append(f"[s{i}]crop={b.w}:{b.h}:{b.x}:{b.y},boxblur={radius}:2[p{i}]")
        last = i == n - 1
        nxt = f"v{i}"
        parts.append(
            f"[{cur}][p{i}]overlay={b.x}:{b.y}:"
            f"enable='between(t,{max(0.0, b.t0):.3f},{max(0.0, b.t1):.3f})'"
            + ("" if last else f"[{nxt}]")
        )
        cur = nxt
    return ";".join(parts)


# --------------------------------------------------------------------------- detector
class FaceDetector:
    """Haar cascades by default (they ship with cv2, nothing to download).

    `yunet` is the YuNet DNN from opencv_zoo: far better than Haar on profile
    and half-occluded faces, which is most of a POV stream. It needs a ~230 KB
    ONNX model, fetched once into `<workdir>/models/` unless you point
    `yunet_model` at your own copy.

    `auto` (the default) is: YuNet if a model is available, else Haar if this
    cv2 still ships cascades (OpenCV 4.x), else fetch YuNet. OpenCV 5 removed
    `CascadeClassifier`, so on a modern install `auto` == YuNet.
    """

    MODEL_NAME = "face_detection_yunet_2023mar.onnx"
    MODEL_URL = ("https://github.com/opencv/opencv_zoo/raw/main/models/"
                 "face_detection_yunet/face_detection_yunet_2023mar.onnx")

    def __init__(self, cfg: dict | None = None, model_dir: Optional[Path] = None):
        cfg = dict(cfg or {})
        self.kind = str(cfg.get("detector", "auto") or "auto").lower()
        self.min_px = int(cfg.get("min_face_px", 24))
        self.scale = float(cfg.get("scale_factor", 1.15))
        self.neighbors = int(cfg.get("min_neighbors", 5))
        self.score_threshold = float(cfg.get("score_threshold", 0.6))
        self.auto_download = bool(cfg.get("auto_download_model", True))
        self.model_dir = ensure_dir(Path(model_dir or (Path.home() / ".cache" / "autoclip")))
        self.model_path = Path(str(cfg.get("yunet_model", "") or "").strip()
                               or (self.model_dir / self.MODEL_NAME))
        self._cascades: List[Any] = []
        self._yunet = None
        self.error: Optional[str] = None
        if cv2 is None:
            self.error = "opencv (cv2) not installed"
            return
        self._init_backend()

    # ------------------------------------------------------------------ setup
    def _init_backend(self) -> None:
        want_haar = self.kind == "haar"
        if not want_haar and self._load_yunet():
            return
        if self._load_cascades():
            return
        if want_haar and not self._load_yunet():
            # cascades are gone (OpenCV 5) — YuNet is the only route left
            if not (self.auto_download and self.fetch_model() and self._load_yunet()):
                self.error = ("this cv2 has no Haar cascades and no YuNet model; "
                              f"set privacy.yunet_model or drop {self.MODEL_NAME} "
                              f"in {self.model_dir}")
            return
        if self.auto_download and self.fetch_model():
            self._load_yunet()
            return
        self.error = (f"no face detector available; put {self.MODEL_NAME} in "
                      f"{self.model_dir} or set privacy.yunet_model")

    def _load_yunet(self) -> bool:
        if not hasattr(cv2, "FaceDetectorYN") or not self.model_path.exists():
            return False
        try:
            self._yunet = cv2.FaceDetectorYN.create(
                str(self.model_path), "", (320, 320),
                self.score_threshold, 0.3, 5000)
            self.error = None
            return self._yunet is not None
        except Exception as exc:  # pragma: no cover - model dependent
            self.error = f"yunet unavailable: {exc}"
            self._yunet = None
            return False

    def _load_cascades(self) -> bool:
        if not hasattr(cv2, "CascadeClassifier"):
            return False
        try:
            for name in ("haarcascade_frontalface_default.xml",
                         "haarcascade_profileface.xml"):
                c = cv2.CascadeClassifier(cv2.data.haarcascades + name)
                if not c.empty():
                    self._cascades.append(c)
        except Exception:  # pragma: no cover
            pass
        if self._cascades:
            self.error = None
            return True
        return False

    def fetch_model(self, url: str | None = None) -> bool:
        """Download the YuNet ONNX model once. Returns False when offline."""
        import urllib.request

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(url or self.MODEL_URL, timeout=60) as r:
                data = r.read()
            if len(data) < 10_000:
                return False
            self.model_path.write_bytes(data)
            return True
        except Exception as exc:  # pragma: no cover - network dependent
            self.error = f"could not fetch {self.MODEL_NAME}: {exc}"
            return False

    @property
    def available(self) -> bool:
        return bool(self._yunet is not None or self._cascades)

    @property
    def backend(self) -> str:
        if self._yunet is not None:
            return "yunet"
        return "haar" if self._cascades else "none"

    def detect(self, bgr) -> List[FaceBox]:
        if bgr is None or not self.available:
            return []
        h, w = bgr.shape[:2]
        out: List[FaceBox] = []
        try:
            if self._yunet is not None:
                self._yunet.setInputSize((w, h))
                _, faces = self._yunet.detect(bgr)
                for f in (faces or []):
                    x, y, fw, fh = [int(v) for v in f[:4]]
                    out.append(FaceBox(x, y, fw, fh, float(f[-1])))
            else:
                gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                for cascade in self._cascades:
                    for (x, y, fw, fh) in cascade.detectMultiScale(
                            gray, scaleFactor=self.scale,
                            minNeighbors=self.neighbors,
                            minSize=(self.min_px, self.min_px)):
                        out.append(FaceBox(int(x), int(y), int(fw), int(fh)))
        except Exception:  # pragma: no cover - detection is best-effort
            return []
        return self._dedupe(out)

    @staticmethod
    def _dedupe(boxes: List[FaceBox]) -> List[FaceBox]:
        """Kill overlapping duplicates (frontal + profile often both fire)."""
        out: List[FaceBox] = []
        for b in sorted(boxes, key=lambda b: b.w * b.h, reverse=True):
            if any(_iou(b, o) > 0.35 for o in out):
                continue
            out.append(b)
        return out


def _iou(a: FaceBox, b: FaceBox) -> float:
    ix1, iy1 = max(a.x, b.x), max(a.y, b.y)
    ix2, iy2 = min(a.x + a.w, b.x + b.w), min(a.y + a.h, b.y + b.h)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union else 0.0


# --------------------------------------------------------------------------- tracking
class FaceTracker:
    """Turns per-frame detections into a handful of stable patches.

    Detection jitters frame to frame; painting that directly looks like
    television static. So: match by centre distance, smooth with an EMA, hold
    a face for `hold_seconds` after it disappears (a blink must not un-blur
    someone), and collapse each track into as few time-windows as possible.
    """

    def __init__(self, max_faces: int = 4, hold_seconds: float = 0.8,
                 smoothing: float = 0.45, split_ratio: float = 0.45):
        self.max_faces = max(1, int(max_faces))
        self.hold = float(hold_seconds)
        self.alpha = 1.0 - clamp(smoothing, 0.0, 0.95)
        self.split_ratio = float(split_ratio)
        self.tracks: List[dict] = []

    def update(self, t: float, boxes: List[FaceBox]) -> None:
        used = set()
        for b in boxes:
            cx, cy = b.x + b.w / 2, b.y + b.h / 2
            best, best_d = None, 1e9
            for i, tr in enumerate(self.tracks):
                if i in used:
                    continue
                d = math.hypot(cx - tr["cx"], cy - tr["cy"])
                tol = 0.8 * max(tr["w"], tr["h"])
                if d < tol and d < best_d:
                    best, best_d = i, d
            if best is None:
                if len(self.tracks) >= self.max_faces:
                    continue
                self.tracks.append({"cx": cx, "cy": cy, "w": float(b.w),
                                    "h": float(b.h), "last": t, "samples": []})
                best = len(self.tracks) - 1
            tr = self.tracks[best]
            used.add(best)
            tr["cx"] = tr["cx"] * (1 - self.alpha) + cx * self.alpha
            tr["cy"] = tr["cy"] * (1 - self.alpha) + cy * self.alpha
            tr["w"] = tr["w"] * (1 - self.alpha) + b.w * self.alpha
            tr["h"] = tr["h"] * (1 - self.alpha) + b.h * self.alpha
            tr["last"] = t
            tr["samples"].append((t, tr["cx"], tr["cy"], tr["w"], tr["h"]))
        # drop stale tracks
        self.tracks = [tr for tr in self.tracks if t - tr["last"] <= self.hold]

    def segments(self, padding: float = 0.25, frame_w: int = 0,
                 frame_h: int = 0, tail: float = 0.0) -> List[BlurBox]:
        out: List[BlurBox] = []
        for tr in self.tracks:
            for seg in self._split(tr["samples"]):
                box = self._box(seg, padding, frame_w, frame_h)
                if box.w <= 2 or box.h <= 2:
                    continue
                box.t1 += tail
                out.append(box)
        return out

    def _split(self, samples: List[tuple]) -> List[List[tuple]]:
        """Group samples into runs that one static rectangle can cover."""
        segs: List[List[tuple]] = []
        cur: List[tuple] = []
        for s in samples:
            if not cur:
                cur = [s]
                continue
            _, ax, ay, aw, ah = cur[0]
            moved = (abs(s[1] - ax) > self.split_ratio * max(aw, 1.0)
                     or abs(s[2] - ay) > self.split_ratio * max(ah, 1.0))
            grew = (s[3] > 1.8 * aw or s[4] > 1.8 * ah)
            if moved or grew:
                segs.append(cur)
                cur = [s]
            else:
                cur.append(s)
        if cur:
            segs.append(cur)
        return segs

    @staticmethod
    def _box(seg: List[tuple], padding: float, fw: int, fh: int) -> BlurBox:
        xs = [s[1] - s[3] / 2 for s in seg]
        ys = [s[2] - s[4] / 2 for s in seg]
        xe = [s[1] + s[3] / 2 for s in seg]
        ye = [s[2] + s[4] / 2 for s in seg]
        x0, y0 = min(xs), min(ys)
        x1, y1 = max(xe), max(ye)
        pad_x = (x1 - x0) * padding
        pad_y = (y1 - y0) * padding
        x0, y0 = x0 - pad_x, y0 - pad_y
        x1, y1 = x1 + pad_x, y1 + pad_y
        if fw:
            x0, x1 = clamp(x0, 0, fw), clamp(x1, 0, fw)
        if fh:
            y0, y1 = clamp(y0, 0, fh), clamp(y1, 0, fh)
        return BlurBox(t0=seg[0][0], t1=seg[-1][0],
                       x=int(round(x0)), y=int(round(y0)),
                       w=int(round(x1 - x0)), h=int(round(y1 - y0)))


# --------------------------------------------------------------------------- OBS driver
class OBSPrivacyDriver:
    """Live face blur on the OBS program output, plugin-free.

    Builds (once) and then drives:

        Live scene
          ├─ Camera            (your existing source, untouched)
          └─ PrivacyBlur       (scene we create)
               ├─ Camera  crop=face0  pos=face0     <- same source, cropped
               ├─ Camera  crop=face1  pos=face1
               └─ [filter] Blur

    Because every item in `PrivacyBlur` references the *same* source, OBS
    renders it N times from one decoder and one blur pass covers them all.
    Toggling off just hides the one item in the live scene.
    """

    def __init__(self, client, cfg: dict | None = None):
        self.client = client
        cfg = dict(cfg or {})
        self.scene = str(cfg.get("scene", "") or "")
        self.source = str(cfg.get("source", "") or "")
        self.patch_scene = str(cfg.get("patch_scene", "PrivacyBlur"))
        self.blur_type = str(cfg.get("blur_type", "box") or "box")
        self.blur_size = int(cfg.get("blur_size", 25))
        self.screenshot_width = int(cfg.get("screenshot_width", 640) or 640)
        self.last_error: Optional[str] = None
        self._patch_ids: Dict[str, List[int]] = {}   # scene -> [item ids]
        self._base: Dict[str, Any] = {}              # scene -> base item info
        self._ready = False

    # ------------------------------------------------------------------ setup
    def _req(self, kind: str, data: dict | None = None):
        try:
            return self.client.request(kind, data or {})
        except Exception as exc:  # pragma: no cover - transport dependent
            self.last_error = f"{kind}: {exc}"
            return None

    def _target_scene(self) -> str:
        if self.scene:
            return self.scene
        cur = self._req("GetCurrentProgramScene") or {}
        return str(cur.get("currentProgramSceneName") or "")

    def _find_base(self, scene: str) -> Optional[dict]:
        items = (self._req("GetSceneItemList", {"sceneName": scene}) or {}).get("sceneItems") or []
        wanted = (self.source or "").strip().lower()
        fallback = None
        for it in items:
            name = str(it.get("sourceName") or "")
            if not name or str(it.get("sourceType", "")).lower().endswith("group"):
                continue
            kind = str(it.get("inputKind") or "").lower()
            if wanted:
                if name.lower() == wanted:
                    return it
                continue
            if any(k in kind for k in VIDEO_KINDS):
                return it
            if fallback is None and "audio" not in kind:
                fallback = it
        return fallback

    def _base_geometry(self, scene: str, item: dict) -> Optional[dict]:
        name = str(item.get("sourceName") or "")
        iid = item.get("sceneItemId")
        if iid is None:
            iid = (self._req("GetSceneItemId",
                             {"sceneName": scene, "sourceName": name}) or {}).get("sceneItemId")
        if iid is None:
            self.last_error = f"no scene item id for '{name}'"
            return None
        tr = self._req("GetSceneItemTransform",
                       {"sceneName": scene, "sceneItemId": int(iid)}) or {}
        tr = tr.get("sceneItemTransform") or tr
        src_w = int(tr.get("sourceWidth") or item.get("sourceWidth") or 0)
        src_h = int(tr.get("sourceHeight") or item.get("sourceHeight") or 0)
        if src_w <= 0 or src_h <= 0:
            self.last_error = f"cannot read source size for '{name}'"
            return None
        return {"name": name, "id": int(iid), "src_w": src_w, "src_h": src_h,
                "x": float(tr.get("positionX", 0.0)),
                "y": float(tr.get("positionY", 0.0)),
                "sx": float(tr.get("scaleX", 1.0) or 1.0),
                "sy": float(tr.get("scaleY", 1.0) or 1.0)}

    def ensure(self, max_faces: int) -> Optional[dict]:
        """Create the patch scene (once) and return base geometry, or None."""
        if self._ready and self._base:
            return self._base
        if not self.client.connect():
            self.last_error = f"obs unreachable: {self.client.last_error}"
            return None
        scene = self._target_scene()
        if not scene:
            self.last_error = "no target scene (set privacy.obs.scene)"
            return None
        item = self._find_base(scene)
        if item is None:
            self.last_error = (f"no video source in scene '{scene}' "
                               f"(set privacy.obs.source)")
            return None
        geo = self._base_geometry(scene, item)
        if geo is None:
            return None
        geo["scene"] = scene

        if self.patch_scene not in (self.client.scene_names() or []):
            if self._req("CreateScene", {"sceneName": self.patch_scene}) is None:
                self.last_error = f"could not create scene '{self.patch_scene}'"
                return None

        # one item per face slot, all referencing the same source
        existing = (self._req("GetSceneItemList",
                              {"sceneName": self.patch_scene}) or {}).get("sceneItems") or []
        ids = [int(i["sceneItemId"]) for i in existing if i.get("sceneItemId") is not None]
        while len(ids) < max_faces:
            d = self._req("CreateSceneItem", {"sceneName": self.patch_scene,
                                              "sourceName": geo["name"],
                                              "sceneItemEnabled": False})
            if d is None:
                self.last_error = "obs refused CreateSceneItem (needs obs-websocket 5.x)"
                break
            ids.append(int(d.get("sceneItemId")))
        geo["patch_ids"] = ids
        for iid in ids:
            self._req("SetSceneItemEnabled", {"sceneName": self.patch_scene,
                                              "sceneItemId": iid,
                                              "sceneItemEnabled": False})

        # one blur filter on the scene itself
        self._ensure_filter()
        # and the patch scene composited over the live scene
        self._ensure_composited(scene)
        self._base = geo
        self._ready = True
        return geo

    def _ensure_filter(self) -> None:
        try:
            lst = (self._req("GetSourceFilterList",
                             {"sourceName": self.patch_scene}) or {}).get("filters") or []
        except Exception:
            lst = []
        settings = {"Filter.Blur.Type": self.blur_type,
                    "Filter.Blur.Size": int(self.blur_size)}
        if any(str(f.get("filterName")) == "PrivacyBlur" for f in lst):
            self._req("SetSourceFilterSettings", {"sourceName": self.patch_scene,
                                                  "filterName": "PrivacyBlur",
                                                  "filterSettings": settings})
            return
        self._req("CreateSourceFilter", {"sourceName": self.patch_scene,
                                         "filterName": "PrivacyBlur",
                                         "filterKind": "blur_filter",
                                         "filterSettings": settings})

    def _ensure_composited(self, scene: str) -> None:
        items = (self._req("GetSceneItemList", {"sceneName": scene}) or {}).get("sceneItems") or []
        for it in items:
            if str(it.get("sourceName")) == self.patch_scene:
                return
        d = self._req("CreateSceneItem", {"sceneName": scene,
                                          "sourceName": self.patch_scene,
                                          "sceneItemEnabled": False})
        if d is None:
            self.last_error = f"could not add '{self.patch_scene}' to '{scene}'"
            return
        # draw it above everything else (best effort)
        self._req("SetSceneItemIndex", {"sceneName": scene,
                                        "sceneItemId": int(d["sceneItemId"]),
                                        "sceneItemIndex": 999})

    # ------------------------------------------------------------------ frame
    def grab(self, geo: dict):
        """Downscaled BGR frame of the base source via GetSourceScreenshot."""
        w = self.screenshot_width
        h = max(2, int(round(w * geo["src_h"] / max(1, geo["src_w"]) / 2) * 2))
        d = self._req("GetSourceScreenshot", {"inputName": geo["name"],
                                              "imageFormat": "jpeg",
                                              "imageWidth": w, "imageHeight": h})
        if not d or not d.get("imageData"):
            self.last_error = "GetSourceScreenshot failed"
            return None, 0.0
        raw = str(d["imageData"])
        if "," in raw and raw.startswith("data:"):
            raw = raw.split(",", 1)[1]
        try:
            buf = base64.b64decode(raw)
            if np is None or cv2 is None:
                return None, 0.0
            arr = np.frombuffer(buf, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception:  # pragma: no cover
            return None, 0.0
        scale = geo["src_w"] / float(w) if w else 1.0
        return img, scale

    # ------------------------------------------------------------------ paint
    def paint(self, geo: dict, faces: List[FaceBox]) -> int:
        """Crop/position one patch per face. Returns how many were shown."""
        ids = geo.get("patch_ids") or []
        if not ids:
            return 0
        sx, sy = geo["sx"], geo["sy"]
        shown = 0
        for i, iid in enumerate(ids):
            if i >= len(faces):
                self._req("SetSceneItemEnabled", {"sceneName": self.patch_scene,
                                                  "sceneItemId": iid,
                                                  "sceneItemEnabled": False})
                continue
            f = faces[i]
            self._req("SetSceneItemTransform", {
                "sceneName": self.patch_scene, "sceneItemId": int(iid),
                "sceneItemTransform": {
                    "cropLeft": int(f.x), "cropTop": int(f.y),
                    "cropRight": int(max(0, geo["src_w"] - f.x - f.w)),
                    "cropBottom": int(max(0, geo["src_h"] - f.y - f.h)),
                    "positionX": geo["x"] + f.x * sx,
                    "positionY": geo["y"] + f.y * sy,
                    "scaleX": sx, "scaleY": sy,
                }})
            self._req("SetSceneItemEnabled", {"sceneName": self.patch_scene,
                                              "sceneItemId": iid,
                                              "sceneItemEnabled": True})
            shown += 1
        return shown

    def hide_all(self, geo: dict) -> None:
        for iid in (geo.get("patch_ids") or []):
            self._req("SetSceneItemEnabled", {"sceneName": self.patch_scene,
                                              "sceneItemId": int(iid),
                                              "sceneItemEnabled": False})

    def set_visible(self, on: bool) -> bool:
        scene = self._base.get("scene") or self._target_scene()
        items = (self._req("GetSceneItemList", {"sceneName": scene}) or {}).get("sceneItems") or []
        ok = False
        for it in items:
            if str(it.get("sourceName")) == self.patch_scene:
                ok = self._req("SetSceneItemEnabled", {
                    "sceneName": scene, "sceneItemId": int(it["sceneItemId"]),
                    "sceneItemEnabled": bool(on)}) is not None
        return ok

    def teardown(self) -> None:
        """Remove the patch scene from every scene and drop it (best effort)."""
        try:
            for scene in (self.client.scene_names() or []):
                items = (self._req("GetSceneItemList",
                                   {"sceneName": scene}) or {}).get("sceneItems") or []
                for it in items:
                    if str(it.get("sourceName")) == self.patch_scene:
                        self._req("RemoveSceneItem", {
                            "sceneName": scene,
                            "sceneItemId": int(it["sceneItemId"])})
            self._req("RemoveScene", {"sceneName": self.patch_scene})
        except Exception:  # pragma: no cover
            pass
        self._ready = False
        self._base = {}


# --------------------------------------------------------------------------- manager
class PrivacyManager:
    """Owns the on/off switch and both drivers."""

    STATE_FILE = "privacy.json"

    def __init__(self, cfg: dict, workdir: Path, bus=None, obs_client=None):
        pcfg = dict(cfg.get("privacy", {}) or {})
        self.cfg = pcfg
        self.workdir = ensure_dir(Path(workdir))
        self.bus = bus
        self.enabled = bool(pcfg.get("enabled", False))
        self.mode = str(pcfg.get("mode", "clip") or "clip").lower()
        ocfg = dict(pcfg.get("obs", {}) or {})
        self.obs_cfg = ocfg

        self.detector = FaceDetector(pcfg, model_dir=self.workdir / "models")
        self.strength = int(pcfg.get("strength", 20))
        self.padding = float(pcfg.get("padding", 0.25))
        self.max_faces = int(pcfg.get("max_faces", 4))
        self.sample_fps = float(pcfg.get("sample_fps", 2.0))
        self.scan_width = int(pcfg.get("scan_width", 640))
        self.persist = bool(pcfg.get("persist", True))
        self.hold_seconds = float(pcfg.get("hold_seconds", 0.8))
        self.update_hz = float(ocfg.get("update_hz", 3.0))

        self.on = bool(pcfg.get("default_on", True)) if self.enabled else False
        self._load()
        self.last_faces = 0
        self.last_error: Optional[str] = self.detector.error
        self.last_scan: List[BlurBox] = []
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.obs: Optional[OBSPrivacyDriver] = None
        if obs_client is not None:
            self.obs = OBSPrivacyDriver(obs_client, ocfg)

    # ------------------------------------------------------------------ state
    @property
    def state_path(self) -> Path:
        return self.workdir / self.STATE_FILE

    def _load(self) -> None:
        if not self.persist or not self.state_path.exists():
            return
        try:
            self.on = bool(json.loads(self.state_path.read_text(encoding="utf-8")).get("on"))
        except Exception:
            pass

    def _save(self) -> None:
        if not self.persist:
            return
        try:
            self.state_path.write_text(json.dumps({"on": bool(self.on)}), encoding="utf-8")
        except Exception:
            pass

    @property
    def clips_blurred(self) -> bool:
        return self.enabled and self.on and self.mode in ("clip", "both")

    @property
    def obs_blurred(self) -> bool:
        return self.enabled and self.on and self.mode in ("obs", "both")

    def set(self, on: bool, source: str = "manual") -> dict:
        with self._lock:
            if not self.enabled:
                return {"ok": False, "on": False, "action": "privacy",
                        "message": "privacy disabled (set privacy.enabled)"}
            changed = bool(on) != bool(self.on)
            self.on = bool(on)
            self._save()
            if self.on:
                self._start_obs()
            else:
                self._stop_obs()
        self._emit(source, changed)
        return {"ok": True, "on": self.on, "action": "privacy",
                "changed": changed,
                "message": "faces blurred" if self.on else "faces visible",
                "mode": self.mode}

    def toggle(self, source: str = "manual") -> dict:
        return self.set(not self.on, source=source)

    def wants(self, intent: str, target: str = "") -> bool:
        """True when this manager owns the intent (lets the dispatcher skip)."""
        i = (intent or "").lower().strip()
        if i in ("blur", "unblur"):
            return True
        return i in ("toggle", "set") and is_privacy_target(target)

    def handle(self, intent: str, target: str = "", value: str = "") -> dict:
        """Entry point for the voice dispatcher."""
        i = (intent or "").lower().strip()
        if i in ("blur", "unblur"):
            return self.set(i == "blur", source="voice")
        if i == "toggle" and is_privacy_target(target):
            return self.toggle(source="voice")
        if i == "set" and is_privacy_target(target):
            return self.set(str(value).strip().lower() in ("on", "true", "1", "yes"),
                            source="voice")
        return {"ok": False, "action": "privacy", "on": self.on,
                "message": f"privacy cannot handle intent '{i}'"}

    def _emit(self, source: str, changed: bool) -> None:
        if self.bus is None:
            return
        from .voice import StreamEvent

        self.bus.publish(StreamEvent(
            type="privacy_status", ts=time.time(), window_t=0.0,
            text=f"privacy {'on' if self.on else 'off'}",
            intent="privacy", target="faces",
            value="on" if self.on else "off",
            confidence=1.0, source=source,
            extra={"on": bool(self.on), "mode": self.mode,
                   "changed": bool(changed), "faces": self.last_faces},
        ))

    # ------------------------------------------------------------------ clips
    def scan(self, path: Path, start: float, end: float, pre_chain: str = "",
             width: int = 0, height: int = 0) -> List[BlurBox]:
        """Detect faces in `start..end` of `path`, in post-`pre_chain` pixels."""
        if not self.detector.available or np is None:
            self.last_error = self.detector.error or "detector unavailable"
            return []
        duration = max(0.5, float(end) - float(start))
        w = int(width or self.scan_width)
        h = int(height) if height else max(2, int(round(w * 16 / 9 / 2) * 2))
        vf = ",".join([p for p in (pre_chain, f"fps={self.sample_fps:g}",
                                   f"scale={w}:{h}") if p])
        try:
            proc = run(["ffmpeg", "-v", "error", "-ss", f"{start:.3f}",
                        "-t", f"{duration:.3f}", "-i", str(path),
                        "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       timeout=max(60, duration * 4), check=False)
            raw = proc.stdout or b""
        except Exception as exc:  # pragma: no cover
            self.last_error = f"privacy scan failed: {exc}"
            return []
        frame_bytes = w * h * 3
        count = len(raw) // frame_bytes
        if count == 0:
            self.last_error = "privacy scan produced no frames"
            return []
        tracker = FaceTracker(max_faces=self.max_faces,
                              hold_seconds=self.hold_seconds)
        step = 1.0 / max(0.1, self.sample_fps)
        for i in range(count):
            off = i * frame_bytes
            frame = np.frombuffer(raw[off:off + frame_bytes], dtype=np.uint8)
            frame = frame.reshape(h, w, 3)
            bgr = frame[:, :, ::-1]
            faces = self.detector.detect(bgr)
            if faces:
                tracker.update(i * step, faces)
        boxes = tracker.segments(padding=self.padding, frame_w=w, frame_h=h,
                                 tail=step)
        # cap the filtergraph: too many patches and ffmpeg crawls
        if len(boxes) > 60:
            boxes = sorted(boxes, key=lambda b: b.t1 - b.t0, reverse=True)[:60]
        self.last_faces = len(tracker.tracks)
        self.last_scan = boxes
        self.last_error = None
        return boxes

    def clip_chain(self, path: Path, start: float, end: float,
                   pre_chain: str = "", width: int = 0, height: int = 0) -> str:
        """Filtergraph fragment blurring faces in one clip ("" when inactive)."""
        if not self.clips_blurred:
            return ""
        boxes = self.scan(path, start, end, pre_chain, width, height)
        return privacy_chain(boxes, self.strength)

    # ------------------------------------------------------------------ obs
    def _start_obs(self) -> None:
        if not self.obs_blurred or self.obs is None:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._obs_loop,
                                        name="privacy-obs", daemon=True)
        self._thread.start()

    def _stop_obs(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        if self.obs is not None and self.obs._base:
            self.obs.hide_all(self.obs._base)
            self.obs.set_visible(False)

    def _obs_loop(self) -> None:
        geo = None
        tracker = FaceTracker(max_faces=self.max_faces,
                              hold_seconds=self.hold_seconds)
        interval = 1.0 / max(0.2, self.update_hz)
        while not self._stop.is_set():
            try:
                if geo is None:
                    geo = self.obs.ensure(self.max_faces)
                    if geo is None:
                        self.last_error = self.obs.last_error
                        time.sleep(5.0)   # OBS not up (yet) — retry slowly
                        continue
                    self.obs.set_visible(True)
                img, scale = self.obs.grab(geo)
                if img is None:
                    self.last_error = self.obs.last_error
                    time.sleep(interval)
                    continue
                faces = [FaceBox(int(f.x * scale), int(f.y * scale),
                                 int(f.w * scale), int(f.h * scale))
                         for f in self.detector.detect(img)]
                tracker.update(time.time(), faces)
                live = []
                for tr in tracker.tracks:
                    if time.time() - tr["last"] <= self.hold_seconds:
                        live.append(FaceBox(int(tr["cx"] - tr["w"] / 2),
                                            int(tr["cy"] - tr["h"] / 2),
                                            int(tr["w"]), int(tr["h"])))
                # grow a little so hair/chin are covered too
                for f in live:
                    px, py = int(f.w * self.padding), int(f.h * self.padding)
                    f.x = max(0, f.x - px)
                    f.y = max(0, f.y - py)
                    f.w = min(geo["src_w"] - f.x, f.w + 2 * px)
                    f.h = min(geo["src_h"] - f.y, f.h + 2 * py)
                self.obs.paint(geo, live)
                self.last_faces = len(live)
                self.last_error = None
            except Exception as exc:  # noqa: BLE001
                self.last_error = f"privacy obs loop: {exc}"
            time.sleep(interval)
        if self.obs is not None and geo is not None:
            self.obs.hide_all(geo)
            self.obs.set_visible(False)

    def start(self) -> None:
        """Called once by the pipeline: begin the OBS loop if it is switched on."""
        if self.enabled and self.on:
            self._start_obs()

    def shutdown(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None

    # ------------------------------------------------------------------ status
    def status(self) -> dict:
        out: Dict[str, Any] = {
            "enabled": self.enabled,
            "on": bool(self.on),
            "mode": self.mode,
            "clips_blurred": self.clips_blurred,
            "obs_blurred": self.obs_blurred,
            "detector": self.detector.backend,
            "detector_available": bool(self.detector.available),
            "model": str(self.detector.model_path),
            "model_present": bool(self.detector.model_path.exists()),
            "strength": self.strength,
            "padding": self.padding,
            "max_faces": self.max_faces,
            "sample_fps": self.sample_fps,
            "faces": self.last_faces,
            "last_boxes": [b.to_dict() for b in self.last_scan[:8]],
            "error": self.last_error or self.detector.error,
            "obs": {
                "configured": self.obs is not None,
                "scene": self.obs_cfg.get("scene", ""),
                "source": self.obs_cfg.get("source", ""),
                "patch_scene": self.obs_cfg.get("patch_scene", "PrivacyBlur"),
                "update_hz": self.update_hz,
                "running": bool(self._thread and self._thread.is_alive()),
                "error": self.obs.last_error if self.obs else None,
            },
        }
        if not self.enabled:
            out["message"] = "privacy.enabled is false"
        elif not self.detector.available:
            out["message"] = ("face detection unavailable (pip install "
                              "opencv-python-headless)")
        return out


def build_privacy(cfg: dict, workdir: Path, bus=None, obs_client=None) -> PrivacyManager:
    return PrivacyManager(cfg, workdir, bus=bus, obs_client=obs_client)
