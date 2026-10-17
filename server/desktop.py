"""Figure out what app/window is in the foreground so the HUD can award
Intelligence XP for reading and Enchanting XP for coding.

Out of the box on macOS via osascript. Linux needs `xdotool` (apt). On Windows
or when neither works, push the frontmost app from another tool via
`POST /api/desktop {"app": "...", "title": "..."}` (Stream Deck, Hammerspoon,
a tiny AutoHotkey script, etc.).
"""
from __future__ import annotations

import shutil
import subprocess
import threading
import time

from .state import DesktopSnapshot

BROWSERS = {"safari", "chrome", "chromium", "firefox", "arc", "brave", "edge",
            "opera", "vivaldi", "chromium"}


class DesktopActivity:
    def __init__(self, cfg: dict):
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.poll_s = float(cfg.get("poll_s", 2.0))
        self.coding = [w.lower() for w in (cfg.get("coding_apps") or [])]
        self.reading = [w.lower() for w in (cfg.get("reading_apps") or [])]
        self.hints = [w.lower() for w in (cfg.get("browser_doc_hints") or [])]
        self.state = DesktopSnapshot()
        self._last_poll = 0.0
        self._lock = threading.Lock()
        self._os = self._detect_os()

    def _detect_os(self) -> str:
        if shutil.which("osascript"):
            return "macos"
        if shutil.which("xdotool"):
            return "linux"
        return "unknown"

    def set(self, app: str, title: str) -> None:
        kind = self._classify(app, title)
        with self._lock:
            self.state = DesktopSnapshot(app=app or "", title=title or "", kind=kind, source="agent")

    def tick(self, dt: float) -> DesktopSnapshot:
        if not self.enabled:
            return self.state
        now = time.time()
        if now - self._last_poll < self.poll_s:
            return self.state
        self._last_poll = now

        if self._os == "macos":
            res = self._probe_macos()
        elif self._os == "linux":
            res = self._probe_linux()
        else:
            return self.state

        if not res:
            return self.state
        app, title = res
        kind = self._classify(app, title)
        with self._lock:
            self.state = DesktopSnapshot(app=app, title=title, kind=kind, source=self._os)
        return self.state

    # ------------------------------------------------------------------ probes
    def _probe_macos(self):
        try:
            script = (
                'tell application "System Events" to get {'
                'name of first application process whose frontmost is true, '
                'name of first window of (first application process whose frontmost is true)}'
            )
            out = subprocess.run(["osascript", "-e", script],
                                 capture_output=True, text=True, timeout=3)
            if out.returncode != 0 or not out.stdout.strip():
                return None
            text = out.stdout.strip()
            if ", " in text:
                app, title = text.split(", ", 1)
            else:
                app, title = text, ""
            return app, title
        except Exception:
            return None

    def _probe_linux(self):
        try:
            win = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                                 capture_output=True, text=True, timeout=2)
            if win.returncode != 0:
                return None
            title = win.stdout.strip()
            pid = subprocess.run(["xdotool", "getactivewindow", "getwindowpid"],
                                 capture_output=True, text=True, timeout=2).stdout.strip()
            app = "?"
            if pid.isdigit():
                cmd = subprocess.run(["cat", f"/proc/{pid}/comm"],
                                     capture_output=True, text=True, timeout=1).stdout.strip()
                if cmd:
                    app = cmd
            return app, title
        except Exception:
            return None

    # ------------------------------------------------------------------ classify
    def _classify(self, app: str, title: str) -> str:
        a = (app or "").lower()
        t = (title or "").lower()
        if any(w in a for w in self.coding):
            return "coding"
        if any(w in a for w in self.reading):
            if a in BROWSERS:
                return "reading" if any(h in t for h in self.hints) else "other"
            return "reading"
        return "other"
