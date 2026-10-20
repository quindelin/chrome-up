"""Camera-only focus recognition for the Intelligence (reading) and Enchanting
(coding) skills.

Decides whether the wearer is looking at a **book / PDF / article** or a
**code editor** purely from what the lenses see — no OS / window-manager help
required, so it works on devices (Meta Ray-Ban Display, Quest Link, phone-as-POV)
where we cannot ask the OS which app is in the foreground.

Approach (heuristic, no model required):

1.  Downsample the frame to 160x120 and run a vertical Sobel → count the
    number of horizontal "text rows" (consecutive runs of high-gradient rows).
2.  Compute the mean brightness, the mean saturation and the fraction of
    saturated coloured pixels — code editors tend to be dark with syntax
    highlights, books tend to be bright and achromatic.
3.  Compute the Canny edge density — both text-rich scenes have a lot of
    edges, but a code editor usually has more and a more regular layout.
4.  Combine the features into `{reading | coding | other}` with a confidence
    and smooth the label with an EMA so it doesn't flicker.

A real book + a real editor in front of any 5MP-ish camera are easy to tell
apart. A blank page or a code editor scrolled to a black region will be
classified as "other" and award no skill — the user can then either keep
reading or move the camera so something text-like fills the view.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

try:
    import cv2  # type: ignore
    _HAS_CV = True
except Exception:  # pragma: no cover
    _HAS_CV = False


KINDS = ("reading", "coding", "other")


class FocusRecognizer:
    def __init__(self, cfg: dict | None = None):
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.min_text_rows = int(cfg.get("min_text_rows", 6))
        self.dark_brightness = int(cfg.get("dark_brightness", 95))
        self.bright_brightness = int(cfg.get("bright_brightness", 145))
        self.syntax_blob_ratio = float(cfg.get("syntax_blob_ratio", 0.0025))
        # EMA smoothing — protects against per-frame flicker
        self._ema_kind = "other"
        self._ema_conf = 0.0
        # run counters for diagnostics
        self._stats = {"frames": 0, "coding": 0, "reading": 0, "other": 0}

    # ------------------------------------------------------------------ public
    def classify(self, frame, motion: float = 0.0) -> Dict[str, object]:
        if not self.enabled or frame is None or not _HAS_CV or frame.size == 0:
            return self._result(self._ema_kind, self._ema_conf, motion,
                                {"text_rows": 0, "source": "no_frame"})
        feats = self._features(frame)
        text_rows = int(feats.get("text_rows", 0))
        sat = float(feats.get("mean_saturation", 0.0))
        bright = float(feats.get("mean_brightness", 0.0))
        edge = float(feats.get("edge_density", 0.0))
        syntax = float(feats.get("syntax_ratio", 0.0))
        spacing_std = float(feats.get("row_spacing_std", 0.0))
        feats["source"] = "camera"

        kind, conf = "other", 0.0
        if text_rows >= self.min_text_rows:
            # Colourful text → code (syntax highlighting on any background)
            if syntax > self.syntax_blob_ratio and sat > 25:
                kind = "coding"
                conf = 0.55 + min(0.4, syntax * 60.0)
            # Dark editor with dense edges
            elif bright <= self.dark_brightness and edge > 0.05:
                kind = "coding"
                conf = 0.55 + min(0.35, edge * 2.0)
            # Bright page with low colour
            elif bright >= self.bright_brightness and sat < 35:
                kind = "reading"
                conf = 0.55 + min(0.35, (bright - self.bright_brightness) / 200.0)
            # Achromatic text → book / PDF
            elif sat < 30 and edge > 0.04 and text_rows >= 7:
                kind = "reading"
                conf = 0.5 + min(0.3, text_rows / 80.0)
            else:
                kind, conf = "other", 0.2

        # A bit of regular spacing pushes us towards "real text layout"
        if conf > 0.0 and spacing_std > 0 and spacing_std < 3.5:
            conf = min(1.0, conf + 0.05)
        # High motion usually means the wearer is not looking at a static page
        if motion > 0.4 and kind != "other":
            conf = max(0.0, conf - 0.2)
            if conf < 0.25:
                kind = "other"

        return self._smooth(kind, conf, motion, feats)

    def reset(self) -> None:
        self._ema_kind, self._ema_conf = "other", 0.0

    def stats(self) -> Dict[str, int]:
        return dict(self._stats)

    # ----------------------------------------------------------------- features
    def _features(self, frame) -> Dict[str, float]:
        small = cv2.resize(frame, (160, 120), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        # text-row count from a vertical Sobel
        edges = cv2.Sobel(gray, cv2.CV_8U, 0, 1, ksize=3)
        row = edges.mean(axis=1)
        m = float(row.mean())
        s = float(row.std())
        thr = m + s * 0.8
        runs, in_run, cur = 0, False, 0
        positions = []
        for i, v in enumerate(row):
            if v > thr:
                if not in_run:
                    in_run = True
                    cur = 0
                cur += 1
            else:
                if in_run and cur >= 2:
                    runs += 1
                    positions.append(i - cur // 2)
                in_run = False
        spacing_std = 0.0
        if len(positions) >= 3:
            gaps = np.diff(positions)
            spacing_std = float(np.std(gaps))

        mean_s = float(hsv[..., 1].mean())
        mean_v = float(hsv[..., 2].mean())
        std_v = float(hsv[..., 2].std())
        syntax_mask = (hsv[..., 1] > 100) & (hsv[..., 2] > 100)
        syntax_ratio = float(syntax_mask.mean())
        c = cv2.Canny(gray, 80, 160)
        edge_density = float((c > 0).mean())

        return {
            "text_rows": runs,
            "row_spacing_std": spacing_std,
            "mean_brightness": mean_v,
            "std_brightness": std_v,
            "mean_saturation": mean_s,
            "syntax_ratio": syntax_ratio,
            "edge_density": edge_density,
        }

    # ------------------------------------------------------------------ helpers
    def _smooth(self, kind, conf, motion, feats):
        if kind not in KINDS:
            kind = "other"
        prev_kind, prev_conf = self._ema_kind, self._ema_conf
        if conf >= prev_conf - 0.05:
            if prev_kind == kind:
                new_conf = prev_conf * 0.55 + conf * 0.45
                new_kind = kind
            else:
                blend = prev_conf * 0.7 + conf * 0.3
                new_kind = kind if blend > prev_conf * 0.6 else prev_kind
                new_conf = blend
        else:
            new_kind, new_conf = kind, conf
        self._ema_kind, self._ema_conf = new_kind, max(0.0, min(1.0, new_conf))
        self._stats["frames"] += 1
        self._stats[new_kind] = self._stats.get(new_kind, 0) + 1
        return self._result(new_kind, self._ema_conf, motion, feats)

    def _result(self, kind, conf, motion, feats):
        feats = {k: (round(v, 3) if isinstance(v, float) else int(v) if isinstance(v, (bool, np.integer)) else v)
                 for k, v in feats.items()}
        return {
            "kind": kind,
            "confidence": round(float(min(1.0, max(0.0, conf))), 3),
            "motion": round(float(motion), 3),
            "features": feats,
            "stats": self._stats,
        }
