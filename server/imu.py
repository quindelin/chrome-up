"""Phone IMU hub.

Accepts `devicemotion` samples from the paired phone over HTTP POST
(`/api/imu`, batched) or WebSocket (`/ws/imu`, or piggy-backed onto
`/ws/phone`) and turns them into the same kind of activity labels the
camera-based classifier emits: `idle | walking | running | boxing | lifting`.

A treadmill, a stationary bike, or shadowboxing all look like a still frame
to the camera but show up clearly in the accelerometer / gyroscope. Merging
the two signals makes the **Agility / Strength / Combat** skills work in
those situations.

Payload (any of these fields may be missing; gravity is in m/s^2, rotation
in rad/s):

    {
      "t":  12345.67,            // monotonic timestamp in ms or seconds
      "ax": 0.10, "ay": 0.02, "az": 9.81,   // acceleration (with gravity)
      "gx": 0.001, "gy": 0.0, "gz": 0.0     // rotation rate
    }

The phone page throttles to 25 Hz and sends one sample per WS frame.
"""
from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Tuple


G = 9.80665


@dataclass
class IMUSample:
    t: float
    amag: float        # acceleration magnitude (with gravity)
    az: float          # vertical acceleration (with gravity)
    gmag: float        # rotation magnitude
    lin_amag: float    # acceleration magnitude minus gravity (linear)


class IMUHub:
    """Thread-safe ring buffer + per-tick feature extractor + activity override."""

    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.window = float(cfg.get("window_s", 4.0))
        self.max_samples = int(cfg.get("max_samples", 512))
        self.stale_s = float(cfg.get("stale_s", 2.0))
        # activity thresholds
        th = cfg.get("thresholds") or {}
        self.running_z_var = float(th.get("running_z_var", 1.5))
        self.running_cadence = (float(th.get("running_cadence_lo", 2.4)),
                                 float(th.get("running_cadence_hi", 4.0)))
        self.lifting_cadence = (float(th.get("lifting_cadence_lo", 0.2)),
                                float(th.get("lifting_cadence_hi", 0.8)))
        self.lifting_z_var = float(th.get("lifting_z_var", 1.2))
        self.boxing_cadence = (float(th.get("boxing_cadence_lo", 1.4)),
                                float(th.get("boxing_cadence_hi", 3.4)))
        self.boxing_gyro = float(th.get("boxing_gyro", 0.6))
        self.walking_cadence = (float(th.get("walking_cadence_lo", 1.5)),
                                 float(th.get("walking_cadence_hi", 2.6)))

        self._buf: Deque[IMUSample] = deque(maxlen=self.max_samples)
        self._last_seen = 0.0
        self._source = "none"
        self._samples_seen = 0
        self._activity = "idle"
        self._cadence = 0.0
        self._features: Dict[str, float] = {}

    # ------------------------------------------------------------------ ingest
    def ingest(self, sample: dict, source: str = "phone") -> bool:
        """Accept a single sample from an external source. Returns True if
        the sample looked sane enough to be stored."""
        if not self.enabled:
            return False
        try:
            ax = float(sample.get("ax", 0.0))
            ay = float(sample.get("ay", 0.0))
            az = float(sample.get("az", G))
            gx = float(sample.get("gx", 0.0))
            gy = float(sample.get("gy", 0.0))
            gz = float(sample.get("gz", 0.0))
        except (TypeError, ValueError):
            return False
        amag = math.sqrt(ax * ax + ay * ay + az * az)
        gmag = math.sqrt(gx * gx + gy * gy + gz * gz)
        lin = max(0.0, amag - G)
        t_raw = sample.get("t", time.time())
        try:
            t = float(t_raw)
            if t > 1e12:        # ms since epoch → seconds
                t /= 1000.0
        except (TypeError, ValueError):
            t = time.time()
        self._buf.append(IMUSample(t=t, amag=amag, az=az, gmag=gmag, lin_amag=lin))
        self._last_seen = time.time()
        self._source = source or "phone"
        self._samples_seen += 1
        return True

    def ingest_batch(self, samples: List[dict], source: str = "phone") -> int:
        n = 0
        for s in samples or []:
            if isinstance(s, dict) and self.ingest(s, source=source):
                n += 1
        return n

    # ------------------------------------------------------------------ features
    def _window_samples(self) -> List[IMUSample]:
        cutoff = time.time() - self.window
        return [s for s in self._buf if s.t >= cutoff]

    def _calc_cadence(self, series: List[Tuple[float, float]]) -> float:
        """Zero-crossing rate (Hz) on a (t, value) series."""
        if len(series) < 6:
            return 0.0
        vals = [v for _, v in series]
        mean = sum(vals) / len(vals)
        signed = [1 if v > mean else -1 for _, v in series]
        crossings = 0
        for a, b in zip(signed, signed[1:]):
            if a != b:
                crossings += 1
        duration = max(0.5, series[-1][0] - series[0][0])
        # each full cycle is 2 zero-crossings
        return crossings / (2.0 * duration)

    def compute(self) -> Dict[str, object]:
        """Recompute features + activity for the current window."""
        if not self.enabled or not self._buf:
            return self._result("idle", 0.0, fresh=False)
        age = time.time() - self._last_seen
        fresh = age <= self.stale_s
        window = self._window_samples()
        if len(window) < 8:
            return self._result("idle", 0.0, fresh=fresh)
        amag = [s.amag for s in window]
        az = [s.az for s in window]
        lin = [s.lin_amag for s in window]
        gmag = [s.gmag for s in window]
        amag_var = self._var(amag)
        az_var = self._var(az)
        lin_mean = sum(lin) / len(lin)
        gyro_mean = sum(gmag) / len(gmag)
        cadence_a = self._calc_cadence([(s.t, s.amag) for s in window])
        cadence_z = self._calc_cadence([(s.t, s.az) for s in window])
        # pick the cadence channel that has more energy
        cadence = cadence_z if az_var > amag_var else cadence_a

        activity = "idle"
        # Running: high vertical accel variance + footfall cadence
        if (az_var >= self.running_z_var
                and self.running_cadence[0] <= cadence <= self.running_cadence[1]):
            activity = "running"
        # Lifting: low cadence, vertical bursts (reps)
        elif (self.lifting_cadence[0] <= cadence <= self.lifting_cadence[1]
              and az_var >= self.lifting_z_var and gyro_mean < self.boxing_gyro):
            activity = "lifting"
        # Boxing / shadowboxing: arm rotation without much vertical motion
        elif (self.boxing_cadence[0] <= cadence <= self.boxing_cadence[1]
              and gyro_mean >= self.boxing_gyro and az_var < self.running_z_var):
            activity = "boxing"
        # Walking: low-energy cadence
        elif (self.walking_cadence[0] <= cadence <= self.walking_cadence[1]
              and az_var > 0.4 and lin_mean < 1.5):
            activity = "walking"

        if not fresh:
            # we have old data but no fresh samples — let the camera take over
            activity = "idle"

        return self._result(activity, cadence, fresh=fresh,
                            amag_var=amag_var, az_var=az_var,
                            lin_mean=lin_mean, gyro_mean=gyro_mean)

    def _result(self, activity: str, cadence: float, fresh: bool, **kw) -> Dict[str, object]:
        feats = {
            "amag_var": round(float(kw.get("amag_var", 0.0)), 4),
            "az_var": round(float(kw.get("az_var", 0.0)), 4),
            "lin_mean": round(float(kw.get("lin_mean", 0.0)), 4),
            "gyro_mean": round(float(kw.get("gyro_mean", 0.0)), 4),
            "cadence": round(float(cadence), 3),
        }
        out = {
            "activity": activity,
            "cadence": round(float(cadence), 3),
            "fresh": bool(fresh),
            "age_s": round(time.time() - self._last_seen, 2) if self._last_seen else None,
            "source": self._source if fresh else "stale",
            "samples": self._samples_seen,
            "features": feats,
        }
        self._activity = activity
        self._cadence = cadence
        self._features = feats
        return out

    @staticmethod
    def _var(vals: List[float]) -> float:
        if len(vals) < 2:
            return 0.0
        m = sum(vals) / len(vals)
        return sum((v - m) ** 2 for v in vals) / len(vals)

    # ------------------------------------------------------------------ public access
    def to_snapshot(self) -> Dict[str, object]:
        return {
            "activity": self._activity,
            "cadence": round(self._cadence, 3),
            "fresh": (time.time() - self._last_seen) <= self.stale_s,
            "age_s": round(time.time() - self._last_seen, 2) if self._last_seen else None,
            "source": self._source,
            "samples": self._samples_seen,
            "features": dict(self._features),
        }

    def is_fresh(self) -> bool:
        return self._last_seen > 0 and (time.time() - self._last_seen) <= self.stale_s
