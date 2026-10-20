"""Curriculum + session datatypes.

The datatypes are language-neutral. Every course, Chinese or Japanese, fills
the same two slots:

    text      what a native speaker actually writes
                zh: 漢字 (你好)          ja: 漢字かな交じり (こんにちは)
    reading   the pronunciation crutch printed above it
                zh: 拼音 (nǐ hǎo)       ja: かな (こんにちは)

`reading` is deliberately a crutch: the UI fades it out as the learner climbs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Phrase:
    """A vocabulary / drill item."""

    text: str
    reading: str
    en: str
    note: str = ""

    def to_dict(self) -> dict:
        return {"text": self.text, "reading": self.reading, "en": self.en, "note": self.note}


@dataclass
class Turn:
    """One line of a Pimsleur-style dialogue."""

    speaker: str  # "them" (listen) | "you" (must be spoken and gated)
    text: str
    reading: str
    en: str
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "speaker": self.speaker,
            "text": self.text,
            "reading": self.reading,
            "en": self.en,
            "note": self.note,
        }


@dataclass
class DrillPattern:
    """A substitution drill: one frame, many slot values."""

    text: str     # 我要去{x}   /  {x}に行きます
    reading: str  # wǒ yào qù {x}  /  {x}にいきます
    en: str       # I want to go to {x} / I'm going to {x}
    values: List[Phrase] = field(default_factory=list)
    # What the {x} slot accepts, as a NARROW semantic class.  "" = untagged.
    # Classes in use: object | place | person | clock | day | food
    #                 weather-noun | weather-adj
    #
    # Narrow is deliberate, and it has to encode GRAMMATICAL class as well as
    # meaning.  A coarse "adjective" tag would let 好吃 (tasty) be recycled
    # into 他比我{x} and produce "he is tastier than me"; a coarse "time" tag
    # would produce 我每天明天起床.  And two weather slots had to split into
    # weather-noun / weather-adj because 雨 is "rain" under 〜なら but "rainy"
    # under 明日は〜です - tag both "weather" and you get "If there's sunny".
    # Tag a slot only with a class whose members really are interchangeable
    # with another slot's members, in that slot's own grammar.
    # Authors tag ONE field per pattern and each value inherits the kind.
    #
    # Untagged slots are simply never filled with recycled words - we would
    # rather emit nothing than emit 学校を食べます.  Verbal slots are left
    # untagged on purpose: transitivity differs, so 想{x}这个 cannot take the
    # intransitive verbs that 一…就{x} happily accepts.
    kind: str = ""

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "reading": self.reading,
            "en": self.en,
            "kind": self.kind,
            "values": [v.to_dict() for v in self.values],
        }


@dataclass
class FreePrompt:
    """A free-response question: the model asks, you answer in your own words.

    The sample answer is not the only right answer - it is what we show you
    afterwards and what we drill the pronunciation of.
    """

    q_text: str
    q_reading: str
    q_en: str
    a_text: str
    a_reading: str
    a_en: str
    keywords: List[str] = field(default_factory=list)
    min_chars: int = 0

    def to_dict(self) -> dict:
        return {
            "q_text": self.q_text,
            "q_reading": self.q_reading,
            "q_en": self.q_en,
            "a_text": self.a_text,
            "a_reading": self.a_reading,
            "a_en": self.a_en,
            "keywords": list(self.keywords),
            "min_chars": self.min_chars,
        }


@dataclass
class VocabTopic:
    """A themed slice of the word bank: 食物 / 交通, 食べ物 / 交通 …"""

    id: str
    band: int          # HSK 1-6, or JLPT 5/4/3/2/1/0
    title: str
    title_native: str  # 人与家庭 / 人と家族
    words: List[Phrase] = field(default_factory=list)
    # a deck topic (deck.py) is studied on its own and met in the library;
    # it is never injected into lessons, so it can be as big as the band needs
    deck: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "band": self.band,
            "title": self.title,
            "title_native": self.title_native,
            "deck": self.deck,
            "count": len(self.words),
            "words": [w.to_dict() for w in self.words],
        }


@dataclass
class Story:
    """One graded story from the course library (library.py).

    The lessons teach a band's grammar; the library is where the hours of
    input come from. A story is heard blind first, then followed line by
    line with the text up, then asked about.
    """

    id: str
    band: int
    title: str
    title_en: str
    chunks: List[Phrase] = field(default_factory=list)   # one sentence each
    questions: List[dict] = field(default_factory=list)  # same shape as readings
    voices: int = 1      # 2 = a dialogue, alternating speakers by chunk

    def running_words(self, words) -> int:
        """Running words (or characters, for an unspaced script) in the text."""
        return sum(words(c.text) for c in self.chunks)

    def to_dict(self, brief: bool = False) -> dict:
        out = {"id": self.id, "band": self.band, "title": self.title,
               "title_en": self.title_en, "lines": len(self.chunks)}
        if not brief:
            out["chunks"] = [c.to_dict() for c in self.chunks]
            out["questions"] = list(self.questions)
        return out


@dataclass
class Lesson:
    id: int
    unit: int
    title: str
    goal: str
    vocab: List[Phrase]
    dialogue: List[Turn]
    # One English sentence that says WHO you are talking to and WHERE, shown
    # before the conversation starts. Pimsleur's "organic learning": a line
    # spoken by a stranger with no setting is noise, and there is nothing to
    # retrieve from it later. Never spoken aloud - it is printed only.
    scene: str = ""
    notes: List[str] = field(default_factory=list)
    patterns: List[DrillPattern] = field(default_factory=list)
    band: int = 1        # HSK band or JLPT band
    prompts: List[FreePrompt] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "unit": self.unit,
            "band": self.band,
            "title": self.title,
            "goal": self.goal,
            "scene": self.scene,
            "vocab": [v.to_dict() for v in self.vocab],
            "dialogue": [t.to_dict() for t in self.dialogue],
            "patterns": [p.to_dict() for p in self.patterns],
            "prompts": [p.to_dict() for p in self.prompts],
            "notes": list(self.notes),
        }


@dataclass
class Unit:
    id: int
    title: str
    focus: str
    # difficulty tightens as you move through the course
    gate: Dict[str, float] = field(default_factory=dict)
    lessons: List[Lesson] = field(default_factory=list)
    band: int = 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "band": self.band,
            "title": self.title,
            "focus": self.focus,
            "gate": dict(self.gate),
            "lessons": [l.to_dict() for l in self.lessons],
        }


@dataclass
class Level:
    """One exam band: HSK 1 … HSK 6, or JLPT N5 … N1 (+ an above-N1 band)."""

    id: int        # ladder position, 1 = easiest
    band: int      # HSK 1-6 | JLPT 5,4,3,2,1 or 0 (0 = beyond N1)
    code: str      # "HSK 3" | "N3" | "N1+"  - what the menu prints
    title: str
    focus: str
    gate: Dict[str, float] = field(default_factory=dict)
    units: List[Unit] = field(default_factory=list)
    vocab_topics: List[VocabTopic] = field(default_factory=list)
    deck_topics: List[VocabTopic] = field(default_factory=list)
    story_count: int = 0

    def lesson_count(self) -> int:
        return sum(len(u.lessons) for u in self.units)

    def vocab_count(self) -> int:
        return sum(len(t.words) for t in self.vocab_topics)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "band": self.band,
            "code": self.code,
            "title": self.title,
            "focus": self.focus,
            "gate": dict(self.gate),
            "lesson_count": self.lesson_count(),
            "vocab_count": self.vocab_count(),
            "vocab_topics": [
                {
                    "id": t.id,
                    "band": t.band,
                    "title": t.title,
                    "title_native": t.title_native,
                    "count": len(t.words),
                }
                for t in self.vocab_topics
            ],
            "deck_topics": [
                {"id": t.id, "band": t.band, "title": t.title,
                 "title_native": t.title_native, "count": len(t.words)}
                for t in self.deck_topics
            ],
            "deck_count": sum(len(t.words) for t in self.deck_topics),
            "story_count": self.story_count,
            "units": [u.to_dict() for u in self.units],
        }


@dataclass
class Score:
    """Result of one pronunciation attempt."""

    provider: str
    pron: float = 0.0
    accuracy: float = 0.0
    fluency: float = 0.0
    completeness: float = 0.0
    recognized: str = ""
    words: List[dict] = field(default_factory=list)
    passed: bool = False
    reasons: List[str] = field(default_factory=list)
    coverage: float = 1.0
    duration: float = 0.0
    error: Optional[str] = None
    # `tone` is the suprasegmental score: 声调 for Mandarin, 高低アクセント for
    # Japanese. -1 when the provider cannot measure it, and the gate then skips
    # it instead of failing you on something nobody measured.
    tone: float = -1.0
    phone: float = -1.0
    # per-unit detail: syllables (zh) or morae (ja)
    syllables: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "pron": round(self.pron, 1),
            "accuracy": round(self.accuracy, 1),
            "fluency": round(self.fluency, 1),
            "completeness": round(self.completeness, 1),
            "recognized": self.recognized,
            "words": self.words,
            "passed": self.passed,
            "reasons": self.reasons,
            "coverage": round(self.coverage, 3),
            "duration": round(self.duration, 2),
            "error": self.error,
            "tone": round(self.tone, 1),
            "phone": round(self.phone, 1),
            "syllables": self.syllables[:16],
        }

    def worst_syllable(self) -> Optional[dict]:
        """Lowest-scoring unit - the thing to fix first."""
        if not self.syllables:
            return None
        return min(self.syllables, key=lambda s: s.get("tone", 100.0))
