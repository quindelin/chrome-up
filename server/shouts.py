"""Skyrim Thu'um: shout on a loud onset, with a cooldown meter."""
from __future__ import annotations

import random
import time
from typing import Dict

from .state import World


class Shouts:
    def __init__(self, cfg: dict):
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.threshold = float(cfg.get("threshold", 0.82))
        self.cooldown_s = float(cfg.get("cooldown_s", 60))
        self.words = list(cfg.get("words") or ["Fus Ro Dah"])
        self._cooldown = 0.0
        self._last = self.words[0] if self.words else "Fus Ro Dah"
        self._last_t = 0.0

    def update(self, dt: float, audio, world: World) -> None:
        if not self.enabled:
            return
        if self._cooldown > 0:
            self._cooldown = max(0.0, self._cooldown - dt)
        if self._cooldown > 0:
            return
        if audio.onset and audio.level >= self.threshold:
            self._cooldown = self.cooldown_s
            self._last = random.choice(self.words)
            self._last_t = time.time()
            world.events.append({
                "type": "shout",
                "text": self._last,
                "shout": self._last,
            })

    def state(self) -> Dict[str, object]:
        return {
            "ready": self._cooldown <= 0,
            "cooldown": round(self._cooldown, 2),
            "cooldown_max": self.cooldown_s,
            "last": self._last,
        }
