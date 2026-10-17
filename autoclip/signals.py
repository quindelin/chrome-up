"""Cheap, local pre-analysis of a window: audio energy, motion, scene cuts, brightness.

This produces the numeric substrate the agent reasons over. It is deliberately
model-free so it runs on a laptop in real time; semantic judgement (is this funny?
is this worth posting?) is the agent's job.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np

from .util import ensure_dir, require_ffmpeg, run


@dataclass
class SecondSignal:
    t: float
    rms_db: float
    speech: bool
    motion: float
    brightness: float
    cut: bool

    def to_dict(self) -> dict:
        return {"t": round(self.t, 2), "rms_db": round(self.rms_db, 1), "speech": self.speech,
                "motion": round(self.motion, 4), "brightness": round(self.brightness, 3),
                "cut": self.cut}


@dataclass
class Moment:
    start: float
    end: float
    score: float
    reasons: List[str] = field(default_factory=list)
    peak_t: float = 0.0

    def to_dict(self) -> dict:
        return {"start": round(self.start, 2), "end": round(self.end, 2),
                "score": round(self.score, 3), "reasons": self.reasons,
                "peak_t": round(self.peak_t, 2)}


@dataclass
class Analysis:
    duration: float
    per_second: List[SecondSignal] = field(default_factory=list)
    moments: List[Moment] = field(default_factory=list)
    frames: List[dict] = field(default_factory=list)   # {"t", "path"}
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "duration": round(self.duration, 2),
            "per_second": [s.to_dict() for s in self.per_second],
            "moments": [m.to_dict() for m in self.moments],
            "frames": self.frames,
            "notes": self.notes,
        }


# --------------------------------------------------------------------------- decode
def decode_audio(path: Path, hz: int = 16000, max_seconds: float = 600.0) -> np.ndarray:
    """Mono float32 PCM in [-1, 1]. Empty array when there is no audio track."""
    require_ffmpeg()
    proc = run([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-t", str(max_seconds),
        "-vn", "-ac", "1", "-ar", str(hz), "-f", "s16le", "-",
    ], timeout=max(120, max_seconds * 2), check=False)
    raw = proc.stdout
    if not raw:
        return np.zeros(0, dtype=np.float32)
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def decode_frames(path: Path, fps: float = 1.0, width: int = 320,
                  max_frames: int = 1200, max_seconds: float = 900.0) -> np.ndarray:
    """RGB frames as (n, h, w, 3) uint8 at `fps`. Returns empty array on failure."""
    require_ffmpeg()
    height = max(2, int(round(width * 9 / 16 / 2) * 2))  # keep roughly 16:9
    proc = run([
        "ffmpeg", "-v", "error", "-i", str(path),
        "-t", str(max_seconds),
        "-vf", f"fps={fps},scale={width}:{height}",
        "-frames:v", str(max_frames),
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ], timeout=max(180, max_seconds * 2), check=False)
    raw = proc.stdout
    frame_bytes = width * height * 3
    if not raw or len(raw) < frame_bytes:
        return np.zeros((0, height, width, 3), dtype=np.uint8)
    n = len(raw) // frame_bytes
    return np.frombuffer(raw[:n * frame_bytes], dtype=np.uint8).reshape(n, height, width, 3)


def extract_frame_images(path: Path, out_dir: Path, every_seconds: float = 4.0,
                         max_frames: int = 40, width: int = 640) -> List[dict]:
    """Write JPEG stills (for vision agents) and return [{t, path}]."""
    require_ffmpeg()
    out_dir = ensure_dir(out_dir)
    for stale in out_dir.glob("*.jpg"):
        try:
            stale.unlink()
        except Exception:
            pass
    pattern = out_dir / "f_%05d.jpg"
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(path),
        "-vf", f"fps=1/{every_seconds},scale={width}:-2",
        "-frames:v", str(max_frames), "-q:v", "4", str(pattern),
    ], timeout=300, check=False)
    frames: List[dict] = []
    for i, p in enumerate(sorted(out_dir.glob("f_*.jpg"))):
        frames.append({"t": round(i * every_seconds, 2), "path": str(p), "index": i})
    return frames


# --------------------------------------------------------------------------- features
def audio_envelope(pcm: np.ndarray, hz: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-second RMS in dBFS (floor -80). Returns (db, is_speech)."""
    if pcm.size == 0:
        return np.zeros(0), np.zeros(0, dtype=bool)
    per = hz
    n = len(pcm) // per
    if n == 0:
        return np.zeros(0), np.zeros(0, dtype=bool)
    blocks = pcm[: n * per].reshape(n, per)
    rms = np.sqrt(np.mean(blocks ** 2, axis=1) + 1e-12)
    db = 20.0 * np.log10(rms + 1e-12)
    db = np.clip(db, -80.0, 0.0)
    return db, db > -45.0


def video_features(frames: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-frame motion, brightness, and cut flags. Frames are at 1 fps."""
    if len(frames) == 0:
        return (np.zeros(0), np.zeros(0), np.zeros(0, dtype=bool))
    gray = frames.astype(np.float32).mean(axis=3) / 255.0
    brightness = gray.mean(axis=(1, 2))
    if len(frames) < 2:
        return (np.zeros(len(frames)), brightness, np.zeros(len(frames), dtype=bool))
    diff = np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
    motion = np.concatenate([[diff[0] if len(diff) else 0.0], diff])
    thresh = max(0.02, float(np.percentile(motion, 90)) * 0.85)
    cuts = motion > max(0.12, thresh * 3.0)
    return motion, brightness, cuts


def build_per_second(db: np.ndarray, speech: np.ndarray, motion: np.ndarray,
                     brightness: np.ndarray, cuts: np.ndarray) -> List[SecondSignal]:
    n = max(len(db), len(motion), len(brightness))
    out: List[SecondSignal] = []
    for i in range(n):
        out.append(SecondSignal(
            t=float(i),
            rms_db=float(db[i]) if i < len(db) else -80.0,
            speech=bool(speech[i]) if i < len(speech) else False,
            motion=float(motion[i]) if i < len(motion) else 0.0,
            brightness=float(brightness[i]) if i < len(brightness) else 0.0,
            cut=bool(cuts[i]) if i < len(cuts) else False,
        ))
    return out


# --------------------------------------------------------------------------- candidates
def find_moments(per_second: List[SecondSignal], min_seconds: float = 10.0,
                 target_seconds: float = 25.0, max_seconds: float = 30.0,
                 pad_before: float = 2.0, pad_after: float = 3.0) -> List[Moment]:
    """Group 'hot' seconds into candidate clips, scored 0..1.

    Short-form platforms reward completion and replays, so runs are grown toward
    `target_seconds` (never past `max_seconds`) and long runs are trimmed to the
    densest `max_seconds` around the peak — not chopped from the head.
    """
    if not per_second:
        return []
    n = len(per_second)
    db = np.array([s.rms_db for s in per_second])
    mot = np.array([s.motion for s in per_second])
    cuts = np.array([s.cut for s in per_second], dtype=float)
    bright = np.array([s.brightness for s in per_second])

    db_clipped = np.clip(db, -70.0, -5.0)
    # Absolute scale is the fallback when a signal is flat (no variance to
    # normalise against) — otherwise a uniformly loud clip scores as silence.
    db_abs = np.clip((db_clipped + 70.0) / 65.0, 0.0, 1.0)
    mot_abs = np.clip(mot / 0.35, 0.0, 1.0)

    def norm(a: np.ndarray, fallback: np.ndarray) -> np.ndarray:
        lo, hi = float(a.min()), float(a.max())
        return fallback if hi - lo < 1e-9 else (a - lo) / (hi - lo)

    db_n = norm(db_clipped, db_abs)
    mot_n = norm(mot, mot_abs)

    energy = 0.55 * db_n + 0.45 * mot_n + 0.25 * cuts
    energy -= 0.5 * (bright < 0.06)          # near-black footage is unusable
    energy = np.clip(energy, 0.0, None)

    if energy.max() <= 1e-9:
        return []
    # Never set the bar at the ceiling: a flat-but-strong window (e.g. constant
    # talking) is still a valid clip, so cap the threshold below the max.
    thresh = max(0.35, float(min(np.percentile(energy, 70), 0.9 * float(energy.max()))))
    hot = energy > thresh

    moments: List[Moment] = []
    i = 0
    while i < n:
        if not hot[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and hot[j + 1]:
            j += 1
        # bridge small gaps (<= 2s of quiet inside an otherwise hot run)
        while j + 3 < n and np.any(hot[j + 1: j + 3]):
            j += int(np.argmax(hot[j + 1: j + 3]) or 1)
        run_slice = energy[i: j + 1]
        if run_slice.size == 0:
            i = j + 1
            continue
        peak = i + int(np.argmax(run_slice))
        start = max(0.0, float(i) - pad_before)
        end = min(float(n), float(j) + 1 + pad_after)
        span = end - start
        if span < min_seconds:
            grow = (min_seconds - span) / 2.0
            start = max(0.0, start - grow)
            end = min(float(n), end + grow)
        elif span < target_seconds:
            # pad out toward the ideal short-form length when there is room
            grow = (min(target_seconds, max_seconds) - span) / 2.0
            start = max(0.0, start - grow)
            end = min(float(n), end + grow)
        if end - start > max_seconds:
            # keep the densest max_seconds around the peak
            start = max(0.0, min(start, float(peak) - max_seconds * 0.6))
            end = min(float(n), start + max_seconds)
        score = float(np.clip(run_slice.mean() * 0.6 + run_slice.max() * 0.4, 0.0, 1.0))
        reasons: List[str] = []
        if db_n[i: j + 1].mean() > 0.6:
            reasons.append("loud audio / emphasis")
        if mot_n[i: j + 1].mean() > 0.6:
            reasons.append("high motion")
        if cuts[i: j + 1].sum() >= 2:
            reasons.append("multiple scene changes")
        if np.mean([s.speech for s in per_second[i: j + 1]]) > 0.5:
            reasons.append("speech present")
        if not reasons:
            reasons.append("local energy spike")
        moments.append(Moment(start=start, end=end, score=score, reasons=reasons,
                              peak_t=float(peak)))
        i = j + 1

    moments.sort(key=lambda m: m.score, reverse=True)
    return moments


def analyze_window(path: Path, cfg: dict, frames_dir: Optional[Path] = None,
                   with_frames: bool = True) -> Analysis:
    """Full local analysis of one materialized window file."""
    fps = float(cfg.get("frame_fps", 1.0))
    hz = int(cfg.get("audio_hz", 16000))
    notes: List[str] = []

    pcm = decode_audio(path, hz=hz, max_seconds=float(cfg.get("transcribe_max_seconds", 300)))
    db, speech = audio_envelope(pcm, hz)
    if pcm.size == 0:
        notes.append("no audio track decoded (silent source or ffmpeg audio filters missing)")

    frames = decode_frames(path, fps=fps) if shutil.which("ffmpeg") else np.zeros((0, 2, 2, 3), np.uint8)
    motion, brightness, cuts = video_features(frames)
    if len(frames) == 0:
        notes.append("no video frames decoded")

    per_second = build_per_second(db, speech, motion, brightness, cuts)
    duration = float(max(len(db), len(motion)))

    frame_images: List[dict] = []
    if with_frames and frames_dir is not None:
        try:
            frame_images = extract_frame_images(path, frames_dir, every_seconds=4.0)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"frame extraction failed: {exc}")

    moments = find_moments(
        per_second,
        min_seconds=float(cfg.get("min_moment_seconds", 10)),
        target_seconds=float(cfg.get("target_moment_seconds", 25)),
        max_seconds=float(cfg.get("max_moment_seconds", 30)),
    )
    return Analysis(duration=duration, per_second=per_second, moments=moments,
                    frames=frame_images, notes=notes)


def analysis_json(analysis: Analysis) -> str:
    return json.dumps(analysis.to_dict(), indent=2)
