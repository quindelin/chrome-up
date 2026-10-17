"""Small shared helpers: shelling out to ffmpeg/ffprobe, time, paths."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".ts", ".m2ts", ".flv", ".webm", ".avi", ".m4v"}


class FFmpegMissing(RuntimeError):
    pass


def require_ffmpeg() -> str:
    if FFMPEG is None:
        raise FFmpegMissing(
            "ffmpeg not found on PATH. Install it:  brew install ffmpeg  (or apt-get install ffmpeg)"
        )
    return FFMPEG


def run(cmd: list[str], timeout: float | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, capturing output. Raises RuntimeError with stderr on failure."""
    proc = subprocess.run(
        [str(c) for c in cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(str(c) for c in cmd)}\n"
            f"{proc.stderr.decode('utf-8', 'replace')[-2000:]}"
        )
    return proc


def _duration_from_ffmpeg(path: str) -> float:
    """Fallback when ffprobe is missing: parse 'Duration: hh:mm:ss.xx'."""
    if FFMPEG is None:
        return 0.0
    try:
        proc = subprocess.run([FFMPEG, "-hide_banner", "-i", path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except Exception:
        return 0.0
    text = proc.stderr.decode("utf-8", "replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", text)
    if not m:
        return 0.0
    h, mi, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mi * 60 + s


def probe(path: Path | str) -> dict[str, Any]:
    """ffprobe JSON: duration + video/audio stream basics. Missing ffprobe -> best effort."""
    path = str(path)
    out: dict[str, Any] = {"duration": 0.0, "width": 0, "height": 0, "fps": 0.0,
                           "has_audio": False, "has_video": False}
    if FFPROBE is None:
        out["duration"] = _duration_from_ffmpeg(path)
        return out
    try:
        proc = run([
            FFPROBE, "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", path,
        ], timeout=30, check=False)
        data = json.loads(proc.stdout.decode("utf-8", "replace") or "{}")
    except Exception:
        return out
    fmt = data.get("format", {}) or {}
    try:
        out["duration"] = float(fmt.get("duration") or 0.0)
    except (TypeError, ValueError):
        out["duration"] = 0.0
    for stream in data.get("streams", []) or []:
        ct = stream.get("codec_type")
        if ct == "video" and not out["has_video"]:
            out["has_video"] = True
            out["width"] = int(stream.get("width") or 0)
            out["height"] = int(stream.get("height") or 0)
            rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1"
            try:
                num, den = str(rate).split("/")
                out["fps"] = float(num) / float(den) if float(den) else 0.0
            except Exception:
                out["fps"] = 0.0
        elif ct == "audio":
            out["has_audio"] = True
    if not out["duration"]:
        try:
            out["duration"] = float((fmt.get("tags") or {}).get("DURATION") or 0.0)
        except (TypeError, ValueError):
            pass
    return out


def duration_of(path: Path | str) -> float:
    return float(probe(path).get("duration") or 0.0)


def srt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms == 1000:  # rounding edge
        s += 1
        ms = 0
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def ass_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


_ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)(?::-(.*?))?\}")


def expand_env(value: str, *, env: dict | None = None) -> str:
    """Expand ${VAR} and ${VAR:-default} using `os.environ` (or `env`)."""
    if not isinstance(value, str) or "$" not in value:
        return value
    import os
    src = env if env is not None else os.environ

    def repl(match: re.Match) -> str:
        var, default = match.group(1), match.group(2)
        if var in src and src[var] != "":
            return src[var]
        return default if default is not None else ""

    return _ENV_RE.sub(repl, value)
