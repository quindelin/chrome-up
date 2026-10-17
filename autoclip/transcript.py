"""Speech-to-text with word timestamps (faster-whisper, else openai-whisper, else off).

Word-level timing is what makes burned-in captions look like CapCut: we can pop
2-3 words at a time instead of a static sentence block.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Word:
    t0: float
    t1: float
    text: str

    def to_dict(self) -> dict:
        return {"t0": round(self.t0, 3), "t1": round(self.t1, 3), "text": self.text}


@dataclass
class Transcript:
    words: List[Word] = field(default_factory=list)
    text: str = ""
    language: str = ""
    engine: str = ""
    note: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.words)

    def to_dict(self) -> dict:
        return {"engine": self.engine, "language": self.language, "text": self.text,
                "words": [w.to_dict() for w in self.words], "note": self.note}

    def slice(self, start: float, end: float) -> "Transcript":
        words = [w for w in self.words if w.t1 > start and w.t0 < end]
        shifted = [Word(max(0.0, w.t0 - start), max(0.0, w.t1 - start), w.text) for w in words]
        return Transcript(words=shifted, text=" ".join(w.text for w in shifted),
                          language=self.language, engine=self.engine)


def transcribe(path: Path, model: str = "base", language: str = "") -> Transcript:
    """Best-effort transcription. Returns an empty Transcript (with a note) on failure."""
    note = ""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception:
        WhisperModel = None  # type: ignore

    if WhisperModel is not None:
        try:
            wm = WhisperModel(model, device="cpu", compute_type="int8")
            segments, info = wm.transcribe(
                str(path), word_timestamps=True,
                language=(language or None), vad_filter=True,
            )
            words: List[Word] = []
            text_parts: List[str] = []
            for seg in segments:
                text_parts.append(seg.text.strip())
                for w in (seg.words or []):
                    words.append(Word(float(w.start), float(w.end), w.word.strip()))
                if not seg.words and seg.text.strip():
                    # fall back to segment-level timing
                    words.append(Word(float(seg.start), float(seg.end), seg.text.strip()))
            return Transcript(words=words, text=" ".join(text_parts).strip(),
                              language=getattr(info, "language", "") or language,
                              engine="faster-whisper")
        except Exception as exc:  # noqa: BLE001
            note = f"faster-whisper failed: {exc}"

    try:
        import whisper  # type: ignore
    except Exception:
        return Transcript(note=note if WhisperModel is not None else
                          "no STT engine installed (pip install faster-whisper)")

    try:
        model_obj = whisper.load_model(model)
        result = model_obj.transcribe(str(path), word_timestamps=True, language=(language or None))
        words = []
        text_parts = []
        for seg in result.get("segments", []):
            text_parts.append(seg.get("text", "").strip())
            for w in seg.get("words", []) or []:
                words.append(Word(float(w.get("start", 0.0)), float(w.get("end", 0.0)),
                                  str(w.get("word", "")).strip()))
        return Transcript(words=words, text=result.get("text", "").strip(),
                          language=result.get("language", language), engine="whisper")
    except Exception as exc:  # noqa: BLE001
        return Transcript(note=f"whisper failed: {exc}")


def caption_lines(transcript: Transcript, max_words: int = 3,
                  max_chars: int = 28) -> List[dict]:
    """Group words into short, punchy caption lines for burn-in.

    Each line also carries its `words` with timestamps, which is what makes
    karaoke / word-pop animation possible.
    """
    lines: List[dict] = []

    def emit(bucket: List[Word]) -> None:
        if not bucket:
            return
        lines.append({
            "t0": bucket[0].t0,
            "t1": bucket[-1].t1,
            "text": " ".join(b.text for b in bucket),
            "words": [{"t0": b.t0, "t1": b.t1, "text": b.text} for b in bucket],
        })

    bucket: List[Word] = []
    for w in transcript.words:
        if not w.text:
            continue
        bucket.append(w)
        joined = " ".join(b.text for b in bucket)
        if len(bucket) >= max_words or len(joined) >= max_chars or w.text.endswith((".", "!", "?")):
            emit(bucket)
            bucket = []
    emit(bucket)
    return lines


def transcript_for_window(path: Path, cfg: dict) -> Transcript:
    if not cfg.get("transcribe", True):
        return Transcript(note="transcription disabled")
    return transcribe(path, model=str(cfg.get("transcribe_model", "base")))


def ffmpeg_has_ass() -> bool:
    """True when this ffmpeg build can burn in subtitles (libass)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    import subprocess
    try:
        out = subprocess.run([ffmpeg, "-hide_banner", "-filters"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        return b"subtitles" in (out.stdout or b"")
    except Exception:
        return False
