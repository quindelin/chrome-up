"""Steadies the walking / running label the avatar animates.

The glasses camera is on your head, so its motion energy rises with every head
turn: on its own it called a seated, looking-around wearer "running". This
gate sits after the camera / IMU merge in main.py and

  - drops camera-only walking / running while posture says sitting, or while
    the head is turning fast (glasses head pose): that flow is the head, not
    your feet,
  - shows walking / running only once it has held for `hold_s`, and goes back
    to idle after `release_s`, so a glance or one step doesn't start a gait.

IMU-sourced labels (phone in a pocket, which feels footfalls) skip the
sitting / head-turn check but still go through the hold.
"""
from __future__ import annotations

import math
from typing import Dict, Optional

LOCOMOTION = ("walking", "running")


class LocomotionGate:
    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.hold_s = float(cfg.get("hold_s", 2.0))
        self.release_s = float(cfg.get("release_s", 1.0))
        self.head_turn_dps = float(cfg.get("head_turn_dps", 45.0))
        self.head_quiet_s = float(cfg.get("head_quiet_s", 0.8))   # after a turn
        self._shown = "idle"
        self._cand, self._since = "idle", 0.0
        self._prev_head: Optional[Dict[str, float]] = None
        self._prev_t = 0.0
        self._turn_until = 0.0
        self.head_speed = 0.0            # deg/s, last measured (status / tests)

    def _head(self, now: float, head: Optional[dict]) -> bool:
        """True while the head is turning (or just was)."""
        if not head or not head.get("fresh"):
            self._prev_head = None
            return now < self._turn_until
        cur = {k: float(head.get(k) or 0.0) for k in ("yaw", "pitch")}
        if self._prev_head is not None and now > self._prev_t:
            dy = (cur["yaw"] - self._prev_head["yaw"] + 180.0) % 360.0 - 180.0
            dp = cur["pitch"] - self._prev_head["pitch"]
            self.head_speed = math.hypot(dy, dp) / (now - self._prev_t)
            if self.head_speed > self.head_turn_dps:
                self._turn_until = now + self.head_quiet_s
        self._prev_head, self._prev_t = cur, now
        return now < self._turn_until

    def update(self, now: float, activity: str, *, from_camera: bool,
               sitting: bool = False, head: Optional[dict] = None) -> str:
        turning = self._head(now, head)
        raw = activity or "idle"
        if raw in LOCOMOTION and from_camera and (sitting or turning):
            raw = "idle"
        if raw not in LOCOMOTION and self._shown not in LOCOMOTION:
            self._shown = self._cand = raw       # boxing / lifting / idle: no hold
            self._since = now
            return self._shown
        if raw != self._cand:
            self._cand, self._since = raw, now
        need = self.hold_s if raw in LOCOMOTION else self.release_s
        if raw != self._shown and now - self._since >= need:
            self._shown = raw
        return self._shown
