"""OPTIONAL face-attribute inference used only by the gender-keyed rizz rule.

This is off by default and stays off unless BOTH are true:
  * `attributes.enabled: true` in config.yaml
  * the server is started with `--optin-attributes`

Face-attribute inference is imperfect and biased; it is your call to run it,
and the overlay always shows `attributes: opt-in` in the control panel so you
know it is live before you stream.

Backends:
  onnx     - point `attributes.model` at any ImageNet-normalised ONNX
             classifier whose outputs line up with `attributes.labels`
             (needs `pip install onnxruntime opencv-python-headless`)
  deepface - uses DeepFace's gender model (needs `pip install deepface`)
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

import numpy as np


class AttributeClassifier:
    def __init__(self, cfg: dict, optin: bool = False):
        self.cfg = cfg or {}
        self.enabled = bool(self.cfg.get("enabled")) and bool(optin)
        self.backend = (self.cfg.get("backend") or "").lower() or None
        self.labels: List[str] = list(self.cfg.get("labels") or ["female", "male"])
        self.input_size = int(self.cfg.get("input_size", 224))
        self.every_s = float(self.cfg.get("every_s", 1.0))
        self.counts: Dict[str, int] = {label: 0 for label in self.labels}
        self.counts["unknown"] = 0
        self.status = "off"
        self._session = None
        self._last_run = 0.0

        if self.enabled:
            print("[attributes] OPT-IN ENABLED — face-attribute inference is running")
            self._load()

    def _load(self) -> None:
        if self.backend == "onnx":
            try:
                import onnxruntime as ort  # type: ignore
                model = self.cfg.get("model")
                if not model:
                    self.status = "onnx: no model path configured"
                    return
                self._session = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
                self.status = f"onnx: {model}"
            except Exception as exc:
                self.status = f"onnx unavailable ({exc})"
        elif self.backend == "deepface":
            try:
                import deepface  # noqa: F401
                self.status = "deepface"
            except Exception as exc:
                self.status = f"deepface unavailable ({exc})"
        else:
            self.status = "no backend configured (attributes.backend: onnx|deepface)"

    # ------------------------------------------------------------------ run
    def update(self, frame, faces: List[tuple]) -> Dict[str, int]:
        """Reclassify at most every `every_s` seconds. `faces` are (x,y,w,h)."""
        if not self.enabled or frame is None:
            return {k: 0 for k in self.counts}
        now = time.time()
        if now - self._last_run < self.every_s:
            return dict(self.counts)
        self._last_run = now

        counts = {label: 0 for label in self.labels}
        counts["unknown"] = 0
        for (x, y, w, h) in faces[:6]:
            label = self._predict(frame, x, y, w, h)
            counts[label if label in counts else "unknown"] += 1
        self.counts = counts
        return dict(counts)

    def _predict(self, frame, x: int, y: int, w: int, h: int) -> str:
        try:
            import cv2
        except Exception:
            return "unknown"
        fh, fw = frame.shape[:2]
        pad = int(max(w, h) * 0.35)
        x0, y0 = max(0, x - pad), max(0, y - pad)
        x1, y1 = min(fw, x + w + pad), min(fh, y + h + pad)
        crop = frame[y0:y1, x0:x1]
        if crop.size == 0:
            return "unknown"

        if self.backend == "deepface":
            return self._predict_deepface(crop)
        if self._session is None:
            return "unknown"

        try:
            import cv2
            img = cv2.resize(crop, (self.input_size, self.input_size)).astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img = (img - mean) / std
            if img.ndim == 2:
                img = np.stack([img] * 3, axis=-1)
            tensor = np.transpose(img, (2, 0, 1))[None, ...].astype(np.float32)
            name = self._session.get_inputs()[0].name
            out = self._session.run(None, {name: tensor})[0]
            idx = int(np.argmax(np.squeeze(out)))
            if idx < len(self.labels):
                return self.labels[idx]
        except Exception:
            return "unknown"
        return "unknown"

    def _predict_deepface(self, crop) -> str:
        try:
            from deepface import DeepFace  # type: ignore
            res = DeepFace.analyze(crop, actions=["gender"], enforce_detection=False,
                                   silent=True)
            res = res[0] if isinstance(res, list) else res
            dom = str(res.get("dominant_gender", "")).lower()
            if "woman" in dom:
                return "female"
            if "man" in dom:
                return "male"
        except Exception:
            return "unknown"
        return "unknown"

    def snapshot(self) -> Dict[str, object]:
        return {"enabled": self.enabled, "status": self.status, "counts": dict(self.counts)}
