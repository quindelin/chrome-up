"""Gesture bus -> HUD menu control.

The Meta Neural Band does not expose a public API yet, so this accepts gesture
names from anything that can reach the server:

  POST /api/gesture        {"gesture": "pinch"}          (Stream Deck, hotkeys,
                                                          band bridge app)
  WS   /ws/gesture         {"gesture": "swipe_right"}    (phone/wearable bridge)
  dashboard gesture pad    (click/drag, or M / arrow keys)

Default mapping (edit `gestures.mapping` in config.yaml):
  tap / pinch / double_tap  toggle menu
  swipe_left / swipe_right  change tab
  swipe_up / swipe_down     scroll
  rotate_cw / rotate_ccw    scroll
  spread                    close menu
"""
from __future__ import annotations

import time
from typing import Dict, Optional

TABS = ["Skills", "Stats", "Objectives"]


class GestureBus:
    def __init__(self, cfg: dict):
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.mapping: Dict[str, str] = {
            str(k): str(v) for k, v in (cfg.get("mapping") or {}).items()
        }
        self.repeat_ms = float(cfg.get("repeat_ms", 220))
        self.state = {"open": False, "tab": 0, "scroll": 0, "last": None}
        self._last_seen: Dict[str, float] = {}

    # ------------------------------------------------------------------ ingest
    def handle(self, gesture: str, source: str = "unknown") -> Optional[dict]:
        if not self.enabled or not gesture:
            return None
        gesture = str(gesture).strip().lower()
        now = time.time()
        last = self._last_seen.get(gesture, 0.0)
        if (now - last) * 1000.0 < self.repeat_ms:
            return None
        self._last_seen[gesture] = now

        action = self.mapping.get(gesture)
        if not action:
            return {"type": "gesture", "gesture": gesture, "action": "unmapped"}

        self._apply(action)
        self.state["last"] = gesture
        return {"type": "gesture", "gesture": gesture, "action": action, "source": source}

    def _apply(self, action: str) -> None:
        if action == "toggle_menu":
            self.state["open"] = not self.state["open"]
        elif action == "open_menu":
            self.state["open"] = True
        elif action == "close_menu":
            self.state["open"] = False
        elif action == "next_tab":
            if not self.state["open"]:
                self.state["open"] = True
            self.state["tab"] = (self.state["tab"] + 1) % len(TABS)
            self.state["scroll"] = 0
        elif action == "prev_tab":
            if not self.state["open"]:
                self.state["open"] = True
            self.state["tab"] = (self.state["tab"] - 1) % len(TABS)
            self.state["scroll"] = 0
        elif action == "scroll_down":
            self.state["scroll"] = min(6, self.state["scroll"] + 1)
        elif action == "scroll_up":
            self.state["scroll"] = max(-6, self.state["scroll"] - 1)

    # ------------------------------------------------------------------ output
    def ui(self) -> dict:
        return {
            "open": bool(self.state["open"]),
            "tab": int(self.state["tab"]),
            "tabs": list(TABS),
            "scroll": int(self.state["scroll"]),
            "last": self.state["last"],
        }
