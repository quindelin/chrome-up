"""Body tracking for the avatar: posture, hands, wrists, heart rate.

A small "VR-style" model: measure the few points the wearables can see and
let the avatar infer the rest. The phone sends one `body` message (on
/ws/phone, or POST /api/body for tests), any subset of:

    {"body": {
      # posture - the phone in a front pocket lies along the thigh
      "posture": "standing" | "sitting",             # if the phone decides, or
      "gravity": [gx, gy, gz],                       # its CoreMotion gravity (any units)

      # hands seen by the glasses camera (iOS Vision hand pose), head-relative
      # metres: x = wearer's right, y = up, z = forward from the face
      "hands": {"left":  {"x": -0.18, "y": -0.30, "z": 0.35, "conf": 0.8},
                "right": {"x":  0.20, "y": -0.25, "z": 0.40}},

      # wrist orientation: Apple Watch (CMDeviceMotion attitude) on one wrist,
      # Meta Neural Band (DAT Motion, source neuralBand) on the other
      "wrists": {"left":  {"q": [w, x, y, z], "source": "watch"},
                 "right": {"q": [w, x, y, z], "source": "neural_band"}},

      "heart_rate": 96                                # bpm, Apple Watch workout
    }}

Every signal goes stale on its own (a hand leaving the camera's view, the
watch dropping its connection), and the avatar eases that part back to
animation instead of freezing it.
"""
from __future__ import annotations

import math
import threading
import time
from typing import Dict, Optional

from .headpose import HeadPose

SIDES = ("left", "right")


class Body:
    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.hand_stale_s = float(cfg.get("hand_stale_s", 0.6))   # out of view quickly
        self.stale_s = float(cfg.get("stale_s", 2.0))
        self.hand_smooth = float(cfg.get("hand_smooth", 0.45))     # 0..1, higher = snappier
        # phone-in-pocket thigh angle from vertical: below sit_lo standing, above
        # sit_hi sitting, in between keep the last answer (hysteresis)
        self.sit_lo = float(cfg.get("sit_below_deg", 40))
        self.sit_hi = float(cfg.get("sit_above_deg", 60))
        self._lock = threading.Lock()
        self._posture, self._posture_src, self._posture_ts = "standing", "none", 0.0
        self._thigh_deg: Optional[float] = None
        self._hands: Dict[str, dict] = {}
        # wrist orientation: relative to the first sample, like the head (the
        # watch's and the band's frames differ; "arm relaxed at your side" is
        # the reference when data starts)
        self._wrists = {s: HeadPose({"recenter_s": 0, "stale_s": self.stale_s}) for s in SIDES}
        self._hr, self._hr_ts = None, 0.0

    # ------------------------------------------------------------------ input
    def ingest(self, data: dict, source: str = "phone") -> bool:
        if not isinstance(data, dict):
            return False
        now = time.time()
        used = False
        with self._lock:
            p = data.get("posture")
            if p in ("standing", "sitting"):
                self._posture, self._posture_src, self._posture_ts = p, source, now
                used = True
            elif isinstance(data.get("gravity"), (list, tuple)) and len(data["gravity"]) == 3:
                used = self._from_gravity(data["gravity"], now, source) or used

            for side, h in (data.get("hands") or {}).items():
                if side not in SIDES or not isinstance(h, dict):
                    continue
                try:
                    pos = [float(h[k]) for k in ("x", "y", "z")]
                except (KeyError, TypeError, ValueError):
                    continue
                prev = self._hands.get(side)
                if prev and now - prev["ts"] < self.hand_stale_s:
                    a = self.hand_smooth
                    pos = [prev["pos"][i] + (pos[i] - prev["pos"][i]) * a for i in range(3)]
                self._hands[side] = {"pos": pos, "conf": float(h.get("conf", 1.0) or 0), "ts": now}
                used = True

            hr = data.get("heart_rate")
            if isinstance(hr, (int, float)) and 25 <= hr <= 250:
                self._hr, self._hr_ts = float(hr), now
                used = True

        for side, w in (data.get("wrists") or {}).items():      # HeadPose locks itself
            if side in SIDES and isinstance(w, dict):
                used = self._wrists[side].ingest(w, source=str(w.get("source") or source)) or used
        return used

    def _from_gravity(self, g, now: float, source: str) -> bool:
        try:
            gx, gy, gz = (float(c) for c in g)
        except (TypeError, ValueError):
            return False
        n = math.sqrt(gx * gx + gy * gy + gz * gz)
        if n < 1e-6:
            return False
        # angle between the phone's long axis and vertical; a phone can sit in
        # the pocket either way up, hence abs()
        deg = math.degrees(math.acos(min(1.0, abs(gy) / n)))
        self._thigh_deg = deg
        if deg <= self.sit_lo:
            self._posture = "standing"
        elif deg >= self.sit_hi:
            self._posture = "sitting"
        self._posture_src, self._posture_ts = source, now
        return True

    # ------------------------------------------------------------------ output
    def snapshot(self) -> Dict[str, object]:
        now = time.time()
        with self._lock:
            posture_fresh = bool(self._posture_ts) and now - self._posture_ts < self.stale_s * 3
            hands = {}
            for side in SIDES:
                h = self._hands.get(side)
                fresh = bool(h) and now - h["ts"] < self.hand_stale_s
                hands[side] = ({"x": round(h["pos"][0], 3), "y": round(h["pos"][1], 3),
                                "z": round(h["pos"][2], 3), "conf": round(h["conf"], 2), "fresh": True}
                               if fresh else {"fresh": False})
            hr_fresh = self._hr is not None and now - self._hr_ts < 10.0
            out = {
                "posture": self._posture if posture_fresh else "unknown",
                "thigh_deg": round(self._thigh_deg, 1) if (posture_fresh and self._thigh_deg is not None) else None,
                "posture_source": self._posture_src if posture_fresh else "stale",
                "hands": hands,
                "heart_rate": round(self._hr) if hr_fresh else None,
            }
        out["wrists"] = {s: self._wrists[s].snapshot() for s in SIDES}
        return out
