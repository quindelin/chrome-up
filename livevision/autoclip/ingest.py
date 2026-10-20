"""Source adapters: where footage comes from before it becomes a rolling window.

  replay_buffer : OBS writes the last N seconds on demand (cheapest, best quality)
  watch_dir     : tail OBS's recording / auto-split directory
  stream_url    : ffmpeg pulls SRT/RTMP/HLS from OBS and segments it locally
  rtmp          : ffmpeg subscribes to a live RTMP feed (cloud: phone -> MediaMTX)
  file          : one local video file (offline testing, no OBS needed)

Every source yields `Segment`s stamped with wall-clock start times, so the
pipeline above it never knows or cares which one is active.
"""
from __future__ import annotations

import shutil
import subprocess
import time
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .buffer import RollingWindow, Segment, scan_new_files
from .obs import OBSClient
from .util import duration_of, ensure_dir, expand_env, require_ffmpeg

OBS_REPLAY_REQUEST = "GetLastReplayBufferReplay"


class Source:
    """Base class: poll() returns segments discovered since the last call."""

    name = "source"

    def poll(self) -> List[Segment]:
        return []

    def close(self) -> None:
        pass

    def status(self) -> dict:
        return {"mode": self.name}


class WatchDirSource(Source):
    """Tail a directory OBS writes to (recording, or auto-split recordings)."""

    def __init__(self, directory: Path, pattern: str = "*.{mp4,mkv,mov,ts,flv}"):
        self.name = "watch_dir"
        self.dir = Path(directory).expanduser()
        self.pattern = pattern
        self._known: Dict[Path, float] = {}
        self._state: Dict[Path, Tuple[float, float]] = {}

    def poll(self) -> List[Segment]:
        return scan_new_files(self.dir, self.pattern, self._known, self._state)

    def status(self) -> dict:
        return {"mode": "watch_dir", "dir": str(self.dir), "exists": self.dir.exists(),
                "pattern": self.pattern, "files": len(self._known)}


class FFmpegSource(WatchDirSource):
    """Pull an OBS output (SRT/RTMP/HLS) and cut it into segments locally."""

    def __init__(self, url: str, seg_dir: Path, segment_seconds: float = 10.0):
        super().__init__(seg_dir, "*.ts")
        self.name = "stream_url"
        self.url = url
        self.segment_seconds = float(segment_seconds)
        self._proc: Optional[subprocess.Popen] = None
        self._start_attempts = 0

    def _spawn(self) -> None:
        require_ffmpeg()
        ensure_dir(self.dir)
        for stale in self.dir.glob("*.ts"):
            try:
                stale.unlink()
            except Exception:
                pass
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", self.url,
            "-map", "0:v:0", "-map", "0:a:0?",
            "-c", "copy",
            "-f", "segment",
            "-segment_time", str(self.segment_seconds),
            "-segment_format", "mpegts",
            "-reset_timestamps", "1",
            "-strftime", "1",
            str(self.dir / self._segment_pattern()),
        ]
        self._proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self._start_attempts += 1

    def _segment_pattern(self) -> str:
        return "seg_%Y%m%d_%H%M%S.ts"

    def poll(self) -> List[Segment]:
        if self._proc is None or self._proc.poll() is not None:
            if self._proc is not None and self._proc.poll() is not None:
                time.sleep(2.0)
            try:
                self._spawn()
            except Exception:
                return []
            time.sleep(2.0)
        return super().poll()

    def close(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
        self._proc = None

    def status(self) -> dict:
        st = super().status()
        st.update({"url": self.url, "segment_seconds": self.segment_seconds,
                   "running": self._proc is not None and self._proc.poll() is None})
        return st


class RTMPSource(FFmpegSource):
    """Cloud ingestion: subscribe to a live RTMP feed and segment it locally.

    This is the path the phone app takes. The phone pushes RTMP to a public
    ingest (MediaMTX / nginx-rtmp) and this driver subscribes and writes
    timestamped `.ts` chunks into a watch directory the rest of the pipeline
    already knows how to tail.

    With `fallback_key` the source prefers `stream_key` (the VPS: OBS's
    composited live/program, HUD included) and drops to the fallback (the raw
    glasses feed) while the preferred path isn't publishing, e.g. OBS down.
    `mediamtx_api` answers "is it publishing?"; while on the fallback the
    feeds are re-checked every `recheck_seconds`. Segments are named
    and tagged per feed (`program` / `raw`) so a window never mixes the two.
    """

    def __init__(self, url: str, seg_dir: Path, stream_key: str = "",
                 segment_seconds: float = 30.0, fallback_key: str = "",
                 mediamtx_api: str = "", recheck_seconds: float = 30.0):
        base = expand_env(url.rstrip("/"))
        key = expand_env(stream_key) if stream_key else ""
        self._base = base
        self._keys = {"program": key.lstrip("/")}
        fb = expand_env(fallback_key) if fallback_key else ""
        if fb and fb.lstrip("/") != self._keys["program"]:
            self._keys["raw"] = fb.lstrip("/")
        self.api = expand_env(mediamtx_api).rstrip("/") if mediamtx_api else ""
        self.recheck_seconds = float(recheck_seconds)
        self.feed = "program"
        self._checked = 0.0
        super().__init__(self._url_for("program"), seg_dir, segment_seconds)
        self.name = "rtmp"
        self.stream_key = key

    def _url_for(self, feed: str) -> str:
        key = self._keys.get(feed, "")
        return f"{self._base}/{key}" if key else self._base

    def path_ready(self, feed: str) -> Optional[bool]:
        """MediaMTX: is anyone publishing this feed? None = can't tell."""
        if not self.api or feed not in self._keys:
            return None
        import json
        import urllib.request
        path = urllib.parse.quote(f"{urllib.parse.urlsplit(self._base).path.strip('/')}/"
                                  f"{self._keys[feed]}".strip("/"))
        try:
            with urllib.request.urlopen(f"{self.api}/v3/paths/get/{path}", timeout=3) as r:
                return bool(json.loads(r.read() or b"{}").get("ready"))
        except Exception:
            return False   # 404 = no publisher

    def _pick_feed(self) -> str:
        if "raw" not in self._keys:
            return "program"
        if self.path_ready("program") is False:
            return "raw"
        # program up but the glasses aren't: OBS is showing a frozen frame
        if self.path_ready("raw") is False and self.api:
            return "raw"
        if self._proc is not None and self._proc.poll() is not None \
                and self.feed == "program" and not self.api:
            return "raw"   # no API: the program pull just died, try the raw feed
        return "program"

    def _spawn(self) -> None:
        self.feed = self._pick_feed()
        self._checked = time.time()
        self.url = self._url_for(self.feed)
        super()._spawn()

    def _segment_pattern(self) -> str:
        return f"{self.feed}_%Y%m%d_%H%M%S.ts"

    def poll(self) -> List[Segment]:
        if ("raw" in self._keys and self._proc is not None and self._proc.poll() is None
                and time.time() - self._checked >= self.recheck_seconds):
            self._checked = time.time()
            if self._pick_feed() != self.feed:
                self.close()          # super().poll() respawns on the other feed
        segs = super().poll()
        for seg in segs:
            seg.source = "program" if seg.path.name.startswith("program_") else (
                "raw" if seg.path.name.startswith("raw_") else seg.source)
        return segs

    def status(self) -> dict:
        st = super().status()
        st["stream_key_set"] = bool(self.stream_key)
        st.pop("url", None)  # don't leak the full RTMP URL with key
        st["ingest"] = "rtmp"
        if "raw" in self._keys:
            st["feed"] = self.feed   # program (HUD) | raw (fallback)
        return st


class FileSource(Source):
    """A single local file — offline dev, or 'analyze this recording'."""

    def __init__(self, path: Path):
        self.name = "file"
        self.path = Path(path).expanduser()
        self._emitted = False

    def poll(self) -> List[Segment]:
        if self._emitted or not self.path.exists():
            return []
        dur = duration_of(self.path)
        if dur <= 0:
            return []
        self._emitted = True
        start = self.path.stat().st_mtime - dur
        return [Segment(path=self.path, start_wall=start, duration=dur, source="file")]

    def status(self) -> dict:
        return {"mode": "file", "path": str(self.path), "exists": self.path.exists()}


class ReplayBufferSource(Source):
    """OBS replay buffer: ask for a save, then locate the file it produced.

    This is the highest-quality path — no re-encode, OBS holds the last N seconds
    in RAM and dumps one clean file.
    """

    def __init__(self, obs_cfg: dict, fallback_dir: str = ""):
        self.name = "replay_buffer"
        self.client = OBSClient(obs_cfg)
        self.fallback_dir = Path(fallback_dir).expanduser() if fallback_dir else None
        self._seen: set[Path] = set()

    def poll(self) -> List[Segment]:
        return []

    def save(self) -> Optional[Segment]:
        """Trigger a save and return the resulting segment (or None)."""
        if not self.client.connect():
            return None
        self.client.ensure_replay_buffer()
        before = self._newest()
        if not self.client.save_replay_buffer():
            return None

        # 1) preferred: obs-websocket tells us the path
        for _ in range(20):
            time.sleep(0.25)
            data = self.client.request(OBS_REPLAY_REQUEST) or {}
            path = data.get("savedReplayPath")
            if path:
                p = Path(path)
                if p.exists():
                    return self._to_segment(p)
            newest = self._newest()
            if newest is not None and (before is None or newest.stat().st_mtime > before.stat().st_mtime):
                return self._to_segment(newest)
        return None

    def _dirs(self) -> List[Path]:
        dirs = []
        if self.fallback_dir and self.fallback_dir.exists():
            dirs.append(self.fallback_dir)
        for guess in (Path.home() / "Movies" / "OBS", Path.home() / "Videos" / "OBS",
                      Path.home() / "Movies", Path.home() / "Videos"):
            if guess.exists():
                dirs.append(guess)
        return dirs

    def _newest(self) -> Optional[Path]:
        best: Optional[Path] = None
        best_t = 0.0
        for d in self._dirs():
            try:
                for p in d.iterdir():
                    if not p.is_file() or p.suffix.lower() not in {".mp4", ".mkv", ".mov", ".ts"}:
                        continue
                    if "replay" not in p.name.lower():
                        continue
                    t = p.stat().st_mtime
                    if t > best_t:
                        best, best_t = p, t
            except Exception:
                continue
        return best

    def _to_segment(self, path: Path) -> Segment:
        dur = duration_of(path)
        stamp = path.stat().st_mtime
        return Segment(path=path, start_wall=stamp - dur, duration=dur,
                       source="replay_buffer")

    def close(self) -> None:
        self.client.close()

    def status(self) -> dict:
        st = self.client.connect()
        out = {"mode": "replay_buffer", "connected": st, "error": self.client.last_error}
        if st:
            out["active"] = bool((self.client.get_replay_buffer_status() or {}).get("outputActive"))
        return out


def build_source(cfg: dict) -> Source:
    """Factory. `auto` picks replay_buffer -> watch_dir -> file, whichever works."""
    mode = str(cfg.get("mode", "auto")).lower()
    if mode in ("auto", "replay_buffer"):
        client = OBSClient(cfg.get("obs", {}))
        if client.connect():
            client.close()
            return ReplayBufferSource(cfg.get("obs", {}), cfg.get("obs", {}).get("replay_dir", ""))
        if mode == "replay_buffer":
            return ReplayBufferSource(cfg.get("obs", {}), cfg.get("obs", {}).get("replay_dir", ""))
    if mode == "watch_dir":
        return WatchDirSource(Path(cfg.get("watch_dir", "~/Movies/OBS")), cfg.get("watch_glob", "*.{mp4,mkv,mov,ts,flv}"))
    if mode == "stream_url":
        return FFmpegSource(cfg.get("stream_url", ""),
                            Path(cfg.get("workdir")) / "segments",
                            cfg.get("segment_seconds", 10))
    if mode == "rtmp":
        rtmp_cfg = cfg.get("rtmp", {}) or {}
        seg_dir = Path(rtmp_cfg.get("dir", cfg.get("workdir", ".") + "/incoming"))
        return RTMPSource(
            url=rtmp_cfg.get("url", ""),
            seg_dir=seg_dir,
            stream_key=rtmp_cfg.get("stream_key", "") or cfg.get("stream_key", ""),
            segment_seconds=float(rtmp_cfg.get("chunk_seconds", 30)),
            fallback_key=rtmp_cfg.get("fallback_key", "") or "",
            mediamtx_api=rtmp_cfg.get("mediamtx_api", "") or "",
            recheck_seconds=float(rtmp_cfg.get("recheck_seconds", 30)),
        )
    if mode == "file":
        return FileSource(Path(cfg.get("file", "")))
    # auto fallthrough
    wd = Path(cfg.get("watch_dir", "~/Movies/OBS")).expanduser()
    if wd.exists():
        return WatchDirSource(wd, cfg.get("watch_glob", "*.{mp4,mkv,mov,ts,flv}"))
    if cfg.get("file"):
        return FileSource(Path(cfg["file"]))
    return WatchDirSource(wd, cfg.get("watch_glob", "*.{mp4,mkv,mov,ts,flv}"))


def refresh_window(source: Source, window: RollingWindow) -> None:
    """Pull new segments from the source into the rolling window and prune."""
    for seg in source.poll():
        window.add(seg)
    window.prune()


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None
