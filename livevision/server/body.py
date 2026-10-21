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

      "heart_rate": 96,                               # bpm, Apple Watch workout

      # one punch, sent the moment the Watch / Neural Band detects it
      "punch": {"side": "left", "kind": "straight" | "hook" | "uppercut",
                "strength": 0.8, "source": "watch" | "neural_band"}
    }}

Punches come out of snapshot() as `punches` (the last PUNCH_SHOW_S seconds,
each with an increasing `id`) so every overlay plays each one exactly once,
and `punching` while they keep coming (the avatar holds its guard).

Every signal goes stale on its own (a hand leaving the camera's view, the
watch dropping its connection), and the avatar eases that part back to
animation instead of freezing it.
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from typing import Dict, List, Optional

from .arms import Arms
from .headpose import HeadPose

SIDES = ("left", "right")
PUNCH_KINDS = ("straight", "hook", "uppercut")
PUNCH_SHOW_S = 1.5        # how long a punch stays in the payload (overlays dedupe by id)
PUNCH_SAME_S = 0.15       # Watch + band on one wrist both see the same punch


class Body:
    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.hand_stale_s = float(cfg.get("hand_stale_s", 0.6))   # out of view quickly
        self.stale_s = float(cfg.get("stale_s", 2.0))
        self.hand_smooth = float(cfg.get("hand_smooth", 0.45))     # 0..1, higher = snappier
        # phone-in-pocket thigh angle from vertical: below sit_lo standing, above
        # sit_hi sitting, in between keep the last answer (hysteresis). Measured
        # on stream: a front-pocket phone reads ~42-49 deg standing (the pocket
        # tilts it) and ~84 sitting
        self.sit_lo = float(cfg.get("sit_below_deg", 62))
        self.sit_hi = float(cfg.get("sit_above_deg", 72))
        self._lock = threading.Lock()
        self._posture, self._posture_src, self._posture_ts = "standing", "none", 0.0
        self._thigh_deg: Optional[float] = None
        self._hands: Dict[str, dict] = {}
        # wrist orientation: relative to the first sample, like the head (the
        # watch's and the band's frames differ). That first sample is often the
        # arm raised to tap Start, so every axis drifts back to neutral over
        # wrist_level_s: the hand rests straight and quick turns still show
        lvl = float(cfg.get("wrist_level_s", 8.0))
        self._wrists = {s: HeadPose({"recenter_s": lvl, "pitch_level_s": lvl, "roll_level_s": lvl,
                                     "stale_s": self.stale_s}) for s in SIDES}
        self._hr, self._hr_ts = None, 0.0
        self.arms = Arms(cfg.get("arms") or {})
        self.guard_s = float(cfg.get("punch_guard_s", 2.5))       # guard stays up this long
        self._punches: deque = deque(maxlen=16)
        self._punch_id = 0

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

            punches = data.get("punches") if isinstance(data.get("punches"), list) else [data.get("punch")]
            for p in punches:
                used = self._punch(p, now, source) or used

            hr = data.get("heart_rate")
            if isinstance(hr, (int, float)) and 25 <= hr <= 250:
                self._hr, self._hr_ts = float(hr), now
                used = True

        for side, w in (data.get("wrists") or {}).items():      # HeadPose locks itself
            if side in SIDES and isinstance(w, dict):
                src = str(w.get("source") or source)
                used = self._wrists[side].ingest(w, source=src) or used
                # absolute orientation -> where the arm points (server/arms.py)
                used = self.arms.ingest_wrist(side, w.get("q"), src, w.get("g")) or used
        pelvis = data.get("pelvis")
        if isinstance(pelvis, dict):
            used = self.arms.ingest_pelvis(pelvis.get("q"), data.get("gravity")) or used
        if data.get("calibrate") in ("down", "tpose"):
            self.arms.calibrate(data["calibrate"])
            used = True
        return used

    def _punch(self, p, now: float, source: str) -> bool:
        if not isinstance(p, dict) or p.get("side") not in SIDES:
            return False
        try:
            strength = max(0.0, min(1.0, float(p.get("strength", 0.7))))
        except (TypeError, ValueError):
            strength = 0.7
        last = self._punches[-1] if self._punches else None
        if last and last["side"] == p["side"] and now - last["ts"] < PUNCH_SAME_S:
            last["strength"] = max(last["strength"], strength)   # same punch, second sensor
            return True
        kind = p.get("kind") if p.get("kind") in PUNCH_KINDS else "straight"
        self._punch_id += 1
        self._punches.append({"id": self._punch_id, "side": p["side"], "kind": kind,
                              "strength": strength, "source": str(p.get("source") or source), "ts": now})
        print(f"[body] punch #{self._punch_id} {p['side']} {kind} {strength:.2f} ({p.get('source') or source})",
              flush=True)
        return True

    def punching(self) -> bool:
        """A punch landed recently: the wearer is boxing."""
        with self._lock:
            return bool(self._punches) and time.time() - self._punches[-1]["ts"] < self.guard_s

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
                "punches": [{"id": p["id"], "side": p["side"], "kind": p["kind"],
                             "strength": round(p["strength"], 2), "source": p["source"],
                             "age": round(now - p["ts"], 3)}
                            for p in self._punches if now - p["ts"] < PUNCH_SHOW_S],
                "punching": bool(self._punches) and now - self._punches[-1]["ts"] < self.guard_s,
            }
        out["wrists"] = {s: self._wrists[s].snapshot() for s in SIDES}
        out["arms"] = self.arms.snapshot()
        return out
