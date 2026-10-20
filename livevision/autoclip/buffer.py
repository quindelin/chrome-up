"""Rolling window of video segments + materialization into a single analyzable file.

The invariant: at any moment we hold >= `window.seconds` of the most recent
footage (as a list of segments), and can hand the agent one contiguous file.
"""
from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from .util import duration_of, ensure_dir, require_ffmpeg, run


@dataclass
class Segment:
    path: Path
    start_wall: float      # epoch seconds when this segment begins
    duration: float        # seconds
    source: str = "unknown"
    growing: bool = False  # still being written by ffmpeg/OBS

    @property
    def end_wall(self) -> float:
        return self.start_wall + self.duration

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "start_wall": round(self.start_wall, 3),
            "end_wall": round(self.end_wall, 3),
            "duration": round(self.duration, 3),
            "source": self.source,
            "growing": self.growing,
        }


@dataclass
class Window:
    """A materialized, analyzable slice of the stream."""
    path: Path
    start_wall: float
    duration: float
    source: str
    segments: List[Segment] = field(default_factory=list)

    @property
    def end_wall(self) -> float:
        return self.start_wall + self.duration

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "start_wall": round(self.start_wall, 3),
            "end_wall": round(self.end_wall, 3),
            "duration": round(self.duration, 3),
            "source": self.source,
            "segments": [s.to_dict() for s in self.segments],
        }


class RollingWindow:
    """Keeps the last `seconds` of footage as a list of segments."""

    def __init__(self, seconds: float, workdir: Path, keep_margin: float = 60.0):
        self.seconds = float(seconds)
        self.margin = float(keep_margin)
        self.workdir = ensure_dir(workdir)
        self.segments: List[Segment] = []

    # ------------------------------------------------------------------ ingest
    def add(self, seg: Segment) -> None:
        for existing in self.segments:
            if existing.path == seg.path:
                existing.duration = seg.duration
                existing.start_wall = seg.start_wall
                existing.growing = seg.growing
                return
        self.segments.append(seg)
        self.segments.sort(key=lambda s: s.start_wall)

    def prune(self, now: float | None = None) -> None:
        """Drop (and delete) segments fully older than the retention horizon."""
        now = now or time.time()
        cutoff = now - self.seconds - self.margin
        kept: List[Segment] = []
        for seg in self.segments:
            if seg.end_wall < cutoff and not seg.growing:
                try:
                    seg.path.unlink(missing_ok=True)
                except Exception:
                    pass
            else:
                kept.append(seg)
        self.segments = kept

    # ------------------------------------------------------------------ queries
    def span(self, now: float | None = None) -> tuple[float, float]:
        if not self.segments:
            now = now or time.time()
            return (now, now)
        return (self.segments[0].start_wall, self.segments[-1].end_wall)

    def covered_seconds(self, now: float | None = None) -> float:
        t0, t1 = self.span(now)
        return max(0.0, t1 - t0)

    def segments_in(self, start: float, end: float) -> List[Segment]:
        return [s for s in self.segments if s.end_wall > start and s.start_wall < end]

    def to_dict(self) -> dict:
        return {
            "seconds": self.seconds,
            "covered_seconds": round(self.covered_seconds(), 2),
            "span": [round(v, 3) for v in self.span()],
            "segments": [s.to_dict() for s in self.segments],
        }

    # ------------------------------------------------------------------ materialize
    def materialize(self, start: float | None = None, end: float | None = None,
                    out_dir: Path | None = None, name: str | None = None) -> Window:
        """Concat the overlapping segments into one file the agent can analyze.

        Offsets are absolute wall-clock; None means "edge of the buffer".
        """
        require_ffmpeg()
        # a source restart (or an RTMP feed switch) clears its chunk dir
        self.segments = [s for s in self.segments if s.path.exists()]
        t0, t1 = self.span()
        start = t0 if start is None else max(t0, start)
        end = t1 if end is None else min(t1, end)
        segs = self.segments_in(start, end)
        # one feed per window: after a program <-> raw switch only the newest
        # run counts, so concat never mixes a 1920x1080 HUD and a portrait feed
        run_from = len(segs)
        while run_from > 0 and segs[run_from - 1].source == segs[-1].source:
            run_from -= 1
        segs = segs[run_from:]
        if not segs:
            raise RuntimeError(
                f"no footage in window [{start:.1f}, {end:.1f}]; buffer holds "
                f"{self.covered_seconds():.1f}s "
                f"(need source.mode / OBS replay buffer / recording to be producing files)"
            )

        out_dir = ensure_dir(out_dir or (self.workdir / "windows"))
        name = name or f"window_{int(start)}"
        out_path = out_dir / f"{name}.mkv"

        if len(segs) == 1:
            seg = segs[0]
            offset = max(0.0, start - seg.start_wall)
            dur = max(0.1, min(seg.duration - offset, end - max(start, seg.start_wall)))
            # One long recording covers the window: trim so "the last 5 minutes"
            # really is 5 minutes and clip offsets stay relative to the window.
            if offset > 1.0 or dur < seg.duration - 1.0:
                run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                     "-ss", f"{offset:.3f}", "-i", str(seg.path), "-t", f"{dur:.3f}",
                     "-c", "copy", "-avoid_negative_ts", "make_zero",
                     "-movflags", "+faststart", str(out_path)], timeout=900)
                return Window(path=out_path, start_wall=max(start, seg.start_wall),
                              duration=duration_of(out_path) or dur, source=seg.source,
                              segments=list(segs))
            return Window(path=seg.path, start_wall=seg.start_wall,
                          duration=seg.duration, source=seg.source,
                          segments=list(segs))

        list_file = out_dir / f"{name}.concat.txt"
        with list_file.open("w", encoding="utf-8") as fh:
            for seg in segs:
                # absolute: ffmpeg resolves relative entries against the list
                # file's own dir, and source dirs (rtmp.dir) are often relative
                safe = str(seg.path.resolve()).replace("'", "'\\''")
                fh.write(f"file '{safe}'\n")

        try:
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "concat", "-safe", "0", "-i", str(list_file),
                 "-c", "copy", "-bsf:a", "aac_adtstoasc", "-movflags", "+faststart",
                 str(out_path)], timeout=600)
        except RuntimeError:
            # mixed codecs / containers: fall back to a re-encode
            run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "concat", "-safe", "0", "-i", str(list_file),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                 "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                 str(out_path)], timeout=1800)

        return Window(path=out_path, start_wall=segs[0].start_wall,
                      duration=max(0.1, duration_of(out_path) or (end - start)),
                      source="concat", segments=list(segs))


def expand_glob(pattern: str) -> List[str]:
    """'*.{mp4,mkv,ts}' -> ['*.mp4', '*.mkv', '*.ts']"""
    if "{" in pattern and "}" in pattern:
        head, rest = pattern.split("{", 1)
        body, tail = rest.split("}", 1)
        return [f"{head}{opt}{tail}" for opt in body.split(",") if opt]
    return [pattern]


def scan_new_files(directory: Path, pattern: str, known: dict[Path, float],
                   poll_state: dict[Path, tuple[float, float]]) -> List[Segment]:
    """Find video files in `directory`, returning segments with wall-clock starts.

    `known` maps path -> last seen size (mutated). A file counts as `growing`
    while its size changes between polls; growing files are still reported so
    the window is never stale.
    """
    directory = Path(directory)
    if not directory.exists():
        return []
    patterns = expand_glob(pattern)
    out: List[Segment] = []
    now = time.time()
    try:
        entries = sorted(directory.iterdir(), key=lambda p: p.stat().st_mtime)
    except Exception:
        return []

    for path in entries:
        if not path.is_file():
            continue
        if not any(fnmatch.fnmatch(path.name.lower(), pat.lower()) for pat in patterns):
            continue
        try:
            st = path.stat()
        except Exception:
            continue
        size = st.st_size
        prev = known.get(path)
        known[path] = size
        growing = prev is not None and size != prev

        dur = poll_state.get(path, (0.0, 0.0))[1]
        if dur <= 0.0 or growing:
            dur = duration_of(path)
            poll_state[path] = (now, dur)
        if dur <= 0.0:
            continue

        # mtime is when the file last grew; for a finished file that is approx its end.
        end_wall = st.st_mtime
        start_wall = end_wall - dur
        out.append(Segment(path=path, start_wall=start_wall, duration=dur,
                           source="watch_dir", growing=growing))
    return out


def iter_video_files(directory: Path) -> Iterable[Path]:
    directory = Path(directory)
    if not directory.exists():
        return []
    return (p for p in sorted(directory.iterdir(), key=lambda q: q.stat().st_mtime)
            if p.is_file() and p.suffix.lower() in {".mp4", ".mkv", ".mov", ".ts", ".flv", ".webm"})
