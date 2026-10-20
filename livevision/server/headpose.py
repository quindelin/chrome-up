"""Head orientation for the avatar: where you look, it looks.

Accepts orientation from whatever can send it, on /ws/phone (key "head") or
POST /api/head:

    {"head": {"q": [w, x, y, z]}}                 Meta glasses Motion (DAT): the fused
                                                  orientation quaternion, w = scalar
    {"head": {"w":..., "x":..., "y":..., "z":...}}  same, as fields
    {"head": {"yaw": 12, "pitch": -5, "roll": 2}}   degrees, already relative
    optional: "source": "glasses" | "phone", "recenter": true

DAT does not document the quaternion's axes, so nothing here depends on an
absolute frame. The first sample (or a "recenter") is taken as "looking at
the camera"; everything after is the rotation since then, decomposed as yaw
about the device's up axis, pitch about its side axis, roll about its forward
axis (config `axes`, if a device's frame comes out swapped or mirrored).
Yaw then drifts back to centre with a slow time constant, so after you turn
a corner the avatar is not left staring sideways.
"""
from __future__ import annotations

import math
import threading
import time
from typing import Dict, Optional, Tuple

Quat = Tuple[float, float, float, float]          # (w, x, y, z)


def _qmul(a: Quat, b: Quat) -> Quat:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def _qconj(q: Quat) -> Quat:
    return (q[0], -q[1], -q[2], -q[3])


def _qnorm(q: Quat) -> Optional[Quat]:
    n = math.sqrt(sum(c * c for c in q))
    return None if n < 1e-9 else tuple(c / n for c in q)  # type: ignore[return-value]


def euler_yxz(q: Quat) -> Tuple[float, float, float]:
    """(yaw about Y, pitch about X, roll about Z), degrees, for a y-up frame."""
    w, x, y, z = q
    # rotation matrix entries needed for YXZ
    m02 = 2 * (x * z + w * y)
    m12 = 2 * (y * z - w * x)
    m22 = 1 - 2 * (x * x + y * y)
    m10 = 2 * (x * y + w * z)
    m11 = 1 - 2 * (x * x + z * z)
    pitch = math.asin(max(-1.0, min(1.0, -m12)))
    if abs(m12) < 0.9999:
        yaw = math.atan2(m02, m22)
        roll = math.atan2(m10, m11)
    else:                                   # looking straight up/down: gimbal lock
        yaw, roll = math.atan2(-2 * (x * z - w * y), 1 - 2 * (y * y + z * z)), 0.0
    return math.degrees(yaw), math.degrees(pitch), math.degrees(roll)


def _wrap(deg: float) -> float:
    return (deg + 180.0) % 360.0 - 180.0


class HeadPose:
    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.stale_s = float(cfg.get("stale_s", 1.5))
        self.recenter_s = float(cfg.get("recenter_s", 20.0))    # yaw drift-back time constant
        # which decomposed angle feeds which avatar axis, and its sign
        #   axes:   {yaw: pitch, ...}  feed avatar yaw from the decomposed pitch
        #   invert: {roll: true}       mirror one axis
        axes = cfg.get("axes") or {}
        inv = cfg.get("invert") or {}
        self.map = {k: (str(axes.get(k, k)), -1.0 if inv.get(k) else 1.0)
                    for k in ("yaw", "pitch", "roll")}
        self._lock = threading.Lock()
        self._ref: Optional[Quat] = None
        self._yaw_center = 0.0
        self._pose = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
        self._ts = 0.0
        self._source = "none"

    # ------------------------------------------------------------------ input
    def ingest(self, data: dict, source: str = "phone") -> bool:
        if not isinstance(data, dict):
            return False
        src = str(data.get("source") or source)
        now = time.time()
        with self._lock:
            if data.get("recenter"):
                self._ref, self._yaw_center = None, 0.0
            q = self._quat(data)
            if q is not None:
                if self._ref is None or now - self._ts > 10 * self.stale_s:
                    self._ref = q                   # (re)starting: this is "straight ahead"
                    self._yaw_center = 0.0
                rel = _qmul(_qconj(self._ref), q)
                raw = dict(zip(("yaw", "pitch", "roll"), euler_yxz(rel)))
            elif any(k in data for k in ("yaw", "pitch", "roll")):
                try:
                    raw = {k: float(data.get(k, 0.0)) for k in ("yaw", "pitch", "roll")}
                except (TypeError, ValueError):
                    return False
            else:
                return False
            pose = {}
            for out_axis, (in_axis, sign) in self.map.items():
                pose[out_axis] = sign * raw.get(in_axis, 0.0)
            # slow re-centre of yaw: the avatar faces the camera on average
            dt = max(0.0, min(1.0, now - self._ts)) if self._ts else 0.0
            if self.recenter_s > 0 and dt:
                k = 1.0 - math.exp(-dt / self.recenter_s)
                self._yaw_center += _wrap(pose["yaw"] - self._yaw_center) * k
            pose["yaw"] = _wrap(pose["yaw"] - self._yaw_center)
            self._pose = {k: round(v, 2) for k, v in pose.items()}
            self._ts = now
            self._source = src
        return True

    @staticmethod
    def _quat(d: dict) -> Optional[Quat]:
        q = d.get("q") or d.get("quaternion") or d.get("orientation")
        try:
            if isinstance(q, (list, tuple)) and len(q) == 4:
                return _qnorm(tuple(float(c) for c in q))    # [w, x, y, z]
            if isinstance(q, dict):
                d = q
            if all(k in d for k in ("w", "x", "y", "z")):
                return _qnorm((float(d["w"]), float(d["x"]), float(d["y"]), float(d["z"])))
        except (TypeError, ValueError):
            return None
        return None

    # ------------------------------------------------------------------ output
    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            fresh = bool(self._ts) and (time.time() - self._ts) < self.stale_s
            return {**self._pose, "fresh": fresh,
                    "source": self._source if fresh else "stale"}
