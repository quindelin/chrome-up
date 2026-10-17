"""Live multi-streaming: re-broadcast one source to N platform RTMP endpoints.

The pipeline already pulls a live POV stream from the glasses (phone -> MediaMTX
or phone -> OBS). This module takes that single source and republishes it to any
number of platforms (YouTube Live, Twitch, Kick, X, Facebook, custom RTMP, …)
in parallel, with `-c copy` so A/V sync survives.

Each active platform runs its own ffmpeg subprocess. The manager:
  - holds a list of `Target` configs (name + url + key + enabled)
  - spawns ffmpeg per active target, capturing logs
  - watches the processes; if one dies, marks it `error` and restarts (up to 5x)
  - exposes start(name) / stop(name) / start_all() / stop_all() / status()

Voice commands route here via the dispatcher: "go live on twitch" calls
start("twitch"), "stop youtube" calls stop("youtube"), "go live everywhere"
calls start_all().

The manager is **independent of the rest of autoclip**: it only needs ffmpeg
and a source RTMP URL. It does not own the rolling window, the clip pipeline,
or any of the publishers. If the pipeline is stopped, live streams keep running
until explicitly stopped. If autoclip is restarted, the manager is told to
remember its active set in `var/autoclip/live/state.json`.
"""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .util import ensure_dir, expand_env, require_ffmpeg


# Common ingest URLs for popular live platforms. The stream key is provided
# by the platform and stored in an env var (never committed).
PLATFORM_INGESTS = {
    "youtube":     "rtmp://a.rtmp.youtube.com/live2",
    "youtube_alt": "rtmp://b.rtmp.youtube.com/live2?backup=1",
    "twitch":      "rtmp://live.twitch.tv/app",
    "kick":        "rtmp://ingest.kick.com/app",
    "x":           "rtmp://ingest.pscp.tv:80/x/",
    "facebook":    "rtmp://live-api-s.facebook.com:80/rtmp/",
    "instagram":   "rtmp://live-upload.instagram.com:80/rtmp/",
    "tiktok":      "rtmp://push-rtmp-l11-va01.tiktok.com:80/live/",
}


@dataclass
class Target:
    name: str
    url: str
    key: str = ""
    enabled: bool = False
    extra_args: List[str] = field(default_factory=list)   # extra ffmpeg flags

    def to_dict(self) -> dict:
        return {"name": self.name, "url": self.url, "enabled": self.enabled,
                "key_set": bool(self.key), "extra_args": list(self.extra_args)}


# Aliases for fuzzy platform names coming from voice commands
_ALIASES = {
    "yt": "youtube", "ytlive": "youtube",
    "twitch.tv": "twitch", "ttv": "twitch",
    "twitter": "x", "x.com": "x",
    "fb": "facebook", "insta": "instagram", "ig": "instagram",
    "tt": "tiktok",
    "*": "all", "everything": "all", "everywhere": "all",
}


def resolve_name(name: str) -> str:
    """Normalize a spoken platform name to a target name. Unknown -> original."""
    if not name:
        return ""
    n = re.sub(r"\s+", "", name.lower().strip(" .,!"))
    if n in PLATFORM_INGESTS or n == "all":
        return n
    if n in _ALIASES:
        return _ALIASES[n]
    return n


class LiveStreamManager:
    """Spawn ffmpeg per active target, watchdog, persistence."""

    def __init__(self, cfg: dict, workdir: Path):
        self.cfg = cfg
        self.workdir = ensure_dir(workdir)
        self.log_dir = ensure_dir(self.workdir / "logs")
        self.state_path = self.workdir / "state.json"
        self.source_url = expand_env(str(cfg.get("source", "")))
        self.max_restarts = int(cfg.get("max_restarts", 5))
        self.restart_backoff = float(cfg.get("restart_backoff_seconds", 5))
        self.targets: Dict[str, Target] = self._load_targets(cfg)
        self._procs: Dict[str, subprocess.Popen] = {}
        self._restart_counts: Dict[str, int] = {}
        self._last_error: Dict[str, str] = {}
        self._started_at: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._watchdog: Optional[threading.Thread] = None
        # restore previous "enabled" so a restart resumes live sessions
        self._restore_state()
        self._start_watchdog()

    # ------------------------------------------------------------------ config
    def _load_targets(self, cfg: dict) -> Dict[str, Target]:
        out: Dict[str, Target] = {}
        for t in cfg.get("targets", []) or []:
            name = str(t.get("name", "")).strip().lower()
            if not name:
                continue
            url = expand_env(str(t.get("url", "")))
            key = expand_env(str(t.get("key", "")))
            if not url and name in PLATFORM_INGESTS:
                url = PLATFORM_INGESTS[name]
            out[name] = Target(
                name=name, url=url, key=key,
                enabled=bool(t.get("enabled", False)),
                extra_args=list(t.get("extra_args", [])),
            )
        return out

    def _restore_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            for name, was_enabled in data.get("active", {}).items():
                if name in self.targets and was_enabled:
                    self.targets[name].enabled = True
        except Exception:
            pass

    def _save_state(self) -> None:
        try:
            data = {"active": {n: bool(t.enabled) for n, t in self.targets.items()}}
            self.state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ------------------------------------------------------------------ lifecycle
    def start(self, name: str) -> dict:
        name = resolve_name(name)
        with self._lock:
            t = self.targets.get(name)
            if t is None:
                return {"ok": False, "platform": name, "message": "unknown target"}
            if not t.url or not t.key:
                return {"ok": False, "platform": name,
                        "message": f"missing url or stream key for {name!r}"}
            if name in self._procs and self._procs[name].poll() is None:
                return {"ok": True, "platform": name, "message": "already live",
                        "pid": self._procs[name].pid}
            t.enabled = True
            self._restart_counts[name] = 0
            self._last_error.pop(name, None)
            self._spawn_locked(t)
            self._save_state()
        return {"ok": True, "platform": name, "message": "started",
                "pid": self._procs.get(name, None) and self._procs[name].pid}

    def stop(self, name: str) -> dict:
        name = resolve_name(name)
        with self._lock:
            t = self.targets.get(name)
            if t:
                t.enabled = False
            proc = self._procs.pop(name, None)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self._save_state()
        return {"ok": True, "platform": name, "message": "stopped"}

    def start_all(self) -> List[dict]:
        return [self.start(n) for n in self.targets]

    def stop_all(self) -> List[dict]:
        return [self.stop(n) for n in list(self._procs.keys())]

    def shutdown(self) -> None:
        self._stop.set()
        with self._lock:
            for n in list(self._procs.keys()):
                self._stop_one_locked(n)
            self._procs.clear()
        if self._watchdog and self._watchdog.is_alive():
            self._watchdog.join(timeout=2)

    def _stop_one_locked(self, name: str) -> None:
        proc = self._procs.pop(name, None)
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    # ------------------------------------------------------------------ spawn
    def _spawn_locked(self, t: Target) -> None:
        require_ffmpeg()
        log_path = self.log_dir / f"{t.name}.log"
        full = f"{t.url.rstrip('/')}/{t.key.lstrip('/')}"
        # No `-re`: that flag is for throttling *file* input. On a live network
        # source ffmpeg already paces itself, and `-re` can stall the relay.
        # `-c copy` is what preserves the phone's PTS all the way to the
        # platform — never re-encode here.
        cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "warning",
               "-i", self.source_url,
               "-c", "copy", "-f", "flv",
               *t.extra_args,
               full]
        log_fh = open(log_path, "ab", buffering=0)
        try:
            proc = subprocess.Popen(
                cmd, stdin=subprocess.DEVNULL,
                stdout=log_fh, stderr=log_fh,
                start_new_session=True,
            )
        except FileNotFoundError:
            log_fh.close()
            raise
        self._procs[t.name] = proc
        self._started_at[t.name] = time.time()

    # ------------------------------------------------------------------ watchdog
    def _start_watchdog(self) -> None:
        self._watchdog = threading.Thread(
            target=self._watchdog_loop, name="livestream-watchdog", daemon=True
        )
        self._watchdog.start()

    def _watchdog_loop(self) -> None:
        while not self._stop.is_set():
            time.sleep(2)
            with self._lock:
                for name in list(self.targets.keys()):
                    t = self.targets[name]
                    if not t.enabled:
                        continue
                    proc = self._procs.get(name)
                    if proc is None:
                        # not running but should be — try to start
                        if name in self.targets and self._restart_counts.get(name, 0) < self.max_restarts:
                            self._restart_counts[name] = self._restart_counts.get(name, 0) + 1
                            try:
                                self._spawn_locked(t)
                            except Exception as exc:
                                self._last_error[name] = str(exc)
                        continue
                    if proc.poll() is not None:
                        # died — record error, possibly restart
                        self._last_error[name] = (self._read_tail(name) or
                                                  f"exit code {proc.returncode}")
                        self._procs.pop(name, None)
                        if self._restart_counts.get(name, 0) < self.max_restarts:
                            self._restart_counts[name] = self._restart_counts.get(name, 0) + 1
                            time.sleep(self.restart_backoff)
                            try:
                                self._spawn_locked(t)
                            except Exception as exc:
                                self._last_error[name] = str(exc)

    def _read_tail(self, name: str, n: int = 8) -> str:
        try:
            text = (self.log_dir / f"{name}.log").read_text(encoding="utf-8", errors="replace")
            lines = [ln for ln in text.splitlines() if ln.strip()]
            return "\n".join(lines[-n:])
        except Exception:
            return ""

    # ------------------------------------------------------------------ status
    def status(self) -> dict:
        with self._lock:
            targets = []
            for n, t in self.targets.items():
                proc = self._procs.get(n)
                running = bool(proc and proc.poll() is None)
                targets.append({
                    **t.to_dict(),
                    "active": running,
                    "pid": proc.pid if running else None,
                    "uptime_seconds": round(time.time() - self._started_at[n], 1)
                                       if (running and n in self._started_at) else 0,
                    "restart_count": self._restart_counts.get(n, 0),
                    "last_error": self._last_error.get(n, ""),
                })
        return {
            "source": self.source_url,
            "log_dir": str(self.log_dir),
            "targets": targets,
            "active_count": sum(1 for t in targets if t["active"]),
        }
