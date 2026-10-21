"""Where your arms point, from the wrist sensors, for the avatar's arms.

A wrist IMU knows its own orientation in a world frame whose z axis is up
(Apple Watch CMAttitude, the phone's GyroAttitude for the Neural Band). The
forearm runs along one device axis, so its world direction is that axis
rotated by the orientation: gravity makes elevation exact (hand overhead,
T-pose, arm hanging), and azimuth needs a reference for "the body's side".

Calibration, two short holds (the companion app's Calibrate button):
  down   arms hanging at your sides: the device axis that points at the floor
         is the forearm (the Neural Band's axes aren't documented; this also
         catches a Watch worn the other way round)
  tpose  arms straight out: each wrist's azimuth now is "outward", and the
         phone in your pocket (pelvis) records which way the body faced

Afterwards an arm's azimuth is relative to that outward reference, minus how
far the pelvis has turned since, so turning your whole body doesn't swing the
avatar's arms. Before a T-pose the arm stays in the body's side plane:
overhead, out or down is still right, forward/back isn't.

Output per side, in the body frame (x = your right, y = up, z = forward):
    {"dir": [x, y, z], "elev": deg, "calibrated": bool, "fresh": bool}
"""
from __future__ import annotations

import json
import math
import threading
import time
from collections import deque
from pathlib import Path
from typing import Dict, Optional, Tuple

SIDES = ("left", "right")
Vec = Tuple[float, float, float]
Quat = Tuple[float, float, float, float]            # (w, x, y, z)

# Apple Watch: +x points from the crown side toward the hand when worn on the
# left wrist with the crown toward the hand (Apple's default)
DEFAULT_AXIS = {"watch": (1.0, 0.0, 0.0)}


def rotate(q: Quat, v: Vec) -> Vec:
    w, x, y, z = q
    vx, vy, vz = v
    # t = 2 * cross(q.xyz, v); v' = v + w t + cross(q.xyz, t)
    tx = 2 * (y * vz - z * vy)
    ty = 2 * (z * vx - x * vz)
    tz = 2 * (x * vy - y * vx)
    return (vx + w * tx + (y * tz - z * ty),
            vy + w * ty + (z * tx - x * tz),
            vz + w * tz + (x * ty - y * tx))


def conj(q: Quat) -> Quat:
    return (q[0], -q[1], -q[2], -q[3])


def norm(v: Vec) -> Optional[Vec]:
    n = math.sqrt(sum(c * c for c in v))
    return None if n < 1e-9 else (v[0] / n, v[1] / n, v[2] / n)


def yaw_of(q: Quat) -> float:
    """Heading (deg, CCW about world z) of the device's x axis."""
    f = rotate(q, (1.0, 0.0, 0.0))
    return math.degrees(math.atan2(f[1], f[0]))


def _wrap(d: float) -> float:
    return (d + 180.0) % 360.0 - 180.0


def _quat(v) -> Optional[Quat]:
    try:
        if isinstance(v, (list, tuple)) and len(v) == 4:
            q = tuple(float(c) for c in v)
            n = math.sqrt(sum(c * c for c in q))
            return None if n < 1e-9 else tuple(c / n for c in q)   # type: ignore[return-value]
    except (TypeError, ValueError):
        pass
    return None


class Arms:
    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.stale_s = float(cfg.get("stale_s", 1.0))
        self.path = Path(cfg.get("calibration_path", "data/arms_calibration.json"))
        self._lock = threading.Lock()
        self._q: Dict[str, Tuple[Quat, str, float]] = {}            # side -> (q, source, ts)
        self._recent: Dict[str, deque] = {s: deque(maxlen=30) for s in SIDES}
        self._pelvis: Optional[Tuple[float, float]] = None          # (yaw deg, ts)
        # side -> {"source", "axis": [x,y,z], "out_yaw": deg|None, "pelvis_yaw": deg|None}
        self._cal: Dict[str, dict] = {}
        # source -> True if its quaternions rotate device -> world as sent,
        # False if world -> device (Apple doesn't say which CMAttitude is):
        # decided from a gravity reading sent alongside
        self._dev_to_world: Dict[str, bool] = {"neural_band": True}
        self._load()

    def _orient(self, q: Quat, source: str, gravity) -> Optional[Quat]:
        """q as device -> world, z up. `gravity` (device frame, pointing down)
        settles the convention the first time a source sends one."""
        g = None
        if isinstance(gravity, (list, tuple)) and len(gravity) == 3:
            try:
                g = norm(tuple(float(c) for c in gravity))
            except (TypeError, ValueError):
                g = None
        if g is not None:
            as_is = rotate(q, g)[2]                      # want -1: gravity is world down
            flipped = rotate(conj(q), g)[2]
            # a turn about the vertical looks the same both ways: decide only
            # when the two disagree clearly
            if min(as_is, flipped) < -0.9 and abs(as_is - flipped) > 0.5:
                self._dev_to_world[source] = as_is < flipped
        conv = self._dev_to_world.get(source)
        if conv is None:
            return None                                  # not until we know
        return q if conv else conj(q)

    # ------------------------------------------------------------------ input
    def ingest_wrist(self, side: str, q, source: str, gravity=None) -> bool:
        qq = _quat(q)
        if side not in SIDES or qq is None:
            return False
        now = time.time()
        with self._lock:
            qq = self._orient(qq, source, gravity)
            if qq is None:
                return False
            self._q[side] = (qq, source, now)
            self._recent[side].append((now, qq))
        return True

    def ingest_pelvis(self, q, gravity=None) -> bool:
        qq = _quat(q)
        if qq is None:
            return False
        with self._lock:
            qq = self._orient(qq, "phone", gravity)
            if qq is None:
                return False
            self._pelvis = (yaw_of(qq), time.time())
        return True

    def calibrate(self, phase: str) -> Dict[str, object]:
        """`down` (arms hanging) or `tpose` (arms out). Uses the last ~0.5 s."""
        now = time.time()
        done = {}
        with self._lock:
            for side in SIDES:
                qs = [q for t, q in self._recent[side] if now - t < 0.6]
                cur = self._q.get(side)
                if not qs or not cur:
                    continue
                source = cur[1]
                cal = self._cal.get(side)
                if not cal or cal.get("source") != source:
                    cal = {"source": source, "axis": None, "out_yaw": None, "pelvis_yaw": None}
                if phase == "down":
                    # world "down" seen from the device: the forearm axis
                    acc = [0.0, 0.0, 0.0]
                    for q in qs:
                        d = rotate(conj(q), (0.0, 0.0, -1.0))
                        acc = [a + b for a, b in zip(acc, d)]
                    axis = norm(tuple(acc))
                    if axis is None:
                        continue
                    cal["axis"] = list(axis)
                    cal["out_yaw"] = None                 # a new axis needs a new T-pose
                elif phase == "tpose":
                    axis = cal.get("axis") or DEFAULT_AXIS.get(source)
                    if axis is None:
                        continue
                    ys = [math.atan2(*reversed(rotate(q, tuple(axis))[:2])) for q in qs]
                    cal["axis"] = list(axis)
                    cal["out_yaw"] = math.degrees(math.atan2(sum(math.sin(y) for y in ys),
                                                             sum(math.cos(y) for y in ys)))
                    p = self._pelvis
                    cal["pelvis_yaw"] = p[0] if p and now - p[1] < 2.0 else None
                else:
                    return {"ok": False, "error": f"phase must be down or tpose, not {phase!r}"}
                self._cal[side] = cal
                done[side] = True
            self._save()
        return {"ok": bool(done), "phase": phase, "sides": sorted(done)}

    # ------------------------------------------------------------------ output
    def snapshot(self) -> Dict[str, dict]:
        now = time.time()
        out = {}
        with self._lock:
            pelvis = self._pelvis if self._pelvis and now - self._pelvis[1] < 2.0 else None
            for side in SIDES:
                cur = self._q.get(side)
                if not cur or now - cur[2] > self.stale_s:
                    out[side] = {"fresh": False}
                    continue
                q, source, _ = cur
                cal = self._cal.get(side) if (self._cal.get(side) or {}).get("source") == source else None
                axis = (cal or {}).get("axis") or DEFAULT_AXIS.get(source)
                if axis is None:                          # Neural Band before an arms-down hold
                    out[side] = {"fresh": False, "needs": "calibration"}
                    continue
                f = norm(rotate(q, tuple(axis)))
                if f is None:
                    out[side] = {"fresh": False}
                    continue
                elev = math.asin(max(-1.0, min(1.0, f[2])))
                horiz = math.cos(elev)
                calibrated = bool(cal and cal.get("out_yaw") is not None)
                if calibrated:
                    rel = _wrap(math.degrees(math.atan2(f[1], f[0])) - cal["out_yaw"])
                    if pelvis and cal.get("pelvis_yaw") is not None:
                        rel = _wrap(rel - _wrap(pelvis[0] - cal["pelvis_yaw"]))
                    r = math.radians(rel)
                else:
                    r = 0.0                               # in the side plane: out / up / down
                # body frame: outward is -x on the left, +x on the right;
                # turning CCW (from above) from outward goes back on the left
                # and forward on the right
                if side == "left":
                    x, z = -math.cos(r) * horiz, -math.sin(r) * horiz
                else:
                    x, z = math.cos(r) * horiz, math.sin(r) * horiz
                out[side] = {"dir": [round(x, 3), round(math.sin(elev), 3), round(z, 3)],
                             "elev": round(math.degrees(elev), 1), "calibrated": calibrated,
                             "source": source, "fresh": True}
        return out

    # ------------------------------------------------------------------ disk
    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text())
            self._cal = {s: c for s, c in data.items() if s in SIDES and isinstance(c, dict)}
        except Exception:
            self._cal = {}

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self._cal, indent=1))
        except Exception as exc:              # pragma: no cover - read-only disk
            print(f"[arms] could not save calibration: {exc}")
