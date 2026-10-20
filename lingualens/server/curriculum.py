"""Course assembly: exam bands -> units -> lessons, plus gate rules.

Language-agnostic. `Course("zh")` walks HSK 1-6, `Course("ja")` walks JLPT
N5-N1 plus an above-N1 mastery band; both come out of here with the same shape.

Two extra content streams hang off each band:
  - vocabulary topics (the word bank, ~1,200 items per language)
  - free-response prompts attached to every lesson
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from . import course as course_pkg
from .models import (
    DrillPattern,
    FreePrompt,
    Lesson,
    Level,
    Phrase,
    Story,
    Turn,
    Unit,
    VocabTopic,
)

_PUNCT = re.compile(r"[\s，。！？、；：,.!?;:\"'“”‘’（）()…—\-–・·「」『』]+")

# characters that carry no information about whether you answered the question
_ZH_FUNCTION = set(
    "我的你了不也很都吗呢吧啊是有在去要会能就还太好了请谢谢请问多少什么谁哪里怎么因为但是虽然而且吧呢"
)

# Japanese grammatical glue: particles, the copula, and the polite verb endings.
# Stripped before we compare "did you actually answer this question?".
_JA_FUNCTION_WORDS = [
    "くださいまして", "ございました", "ございます", "いただきます", "いたします",
    "でしょう", "じゃありません", "ではありません", "かもしれません",
    "からです", "ですね", "ですよ", "ますか", "でしょうか",
    "あります", "います", "おります", "しましょう",
    "ください", "ました", "ません", "でした", "です", "ます",
    "して", "した", "します", "される", "させる", "られる",
    "これ", "それ", "あれ", "この", "その", "あの", "ここ", "そこ", "あそこ",
    "どうぞ", "そう", "はい", "いいえ", "じゃあ", "そして", "でも", "しかし",
    "から", "まで", "より", "には", "では", "とは", "のか", "くらい", "だけ",
    "は", "が", "を", "に", "へ", "も", "や", "の", "と", "で", "か", "ね", "よ", "な", "わ",
    "？", "?",
]
# "？" and "?" are metacharacters, so every entry is escaped before joining
_JA_FUNCTION_RE = re.compile("|".join(re.escape(w) for w in sorted(_JA_FUNCTION_WORDS, key=len, reverse=True)))


def _strip(text: str) -> str:
    return _PUNCT.sub("", text or "")


# Words that carry no meaning for "did you answer the question?", and the
# verb forms a question and its answer share in different persons ("¿de
# dónde eres?" - "soy de Canadá"). Both come from the course's meta.py
# (FUNCTION_WORDS, LEMMAS), so a spaced language needs no engine edit.
_FUNCTION_CACHE: Dict[str, set] = {}
_LEMMA_CACHE: Dict[str, Dict[str, str]] = {}


def _function_words(lang: str) -> set:
    if lang not in _FUNCTION_CACHE:
        raw = course_pkg.meta_get(lang, "FUNCTION_WORDS", "") or ""
        _FUNCTION_CACHE[lang] = set((raw.split() if isinstance(raw, str) else raw))
    return _FUNCTION_CACHE[lang]


def _lemmas(lang: str) -> Dict[str, str]:
    if lang not in _LEMMA_CACHE:
        table: Dict[str, str] = {}
        for lemma, forms in (course_pkg.meta_get(lang, "LEMMAS", {}) or {}).items():
            for form in (forms.split() if isinstance(forms, str) else forms):
                table[form] = lemma
        _LEMMA_CACHE[lang] = table
    return _LEMMA_CACHE[lang]


def _words(text: str) -> List[str]:
    """Lower-cased words of a space-delimited line, any script."""
    return course_pkg.words(text)


def _stem(word: str, lang: str) -> str:
    from .pronunciation import _fold  # accents are the transcriber's, not yours
    lemma = _lemmas(lang).get(word)
    if lemma:
        return lemma
    return _fold(word)[:3]


def content_runs(text: str, lang: str = "zh", min_len: int = 2) -> List[str]:
    """Maximal runs of characters that carry meaning.

    zh: 你叫|什么|名字 -> [叫, 名字]   ja: 最近の仕事 -> [最近, 仕事]
    """
    if course_pkg.is_spaced(lang):
        # a word is already a "run"; min_len is in words' letters here
        runs = [w for w in _words(text) if w not in _function_words(lang)]
        long_runs = [r for r in runs if len(r) >= 3]
        return long_runs or runs
    s = _strip(text)
    if lang == "ja":
        runs = [p for p in _JA_FUNCTION_RE.split(s) if p]
    else:
        runs: List[str] = []
        cur = ""
        for ch in s:
            if ch in _ZH_FUNCTION:
                if cur:
                    runs.append(cur)
                    cur = ""
            else:
                cur += ch
        if cur:
            runs.append(cur)
    long_runs = [r for r in runs if len(r) >= min_len]
    return long_runs or runs


def content_chars(text: str, lang: str = "zh") -> set:
    """The characters in a line that actually carry meaning.

    For a space-delimited language this is the set of content *words*: letter
    overlap between any two Spanish sentences is near total, so a character
    set would call every answer on-topic.
    """
    if course_pkg.is_spaced(lang):
        return {_stem(w, lang) for w in _words(text) if w not in _function_words(lang)}
    s = _strip(text)
    if lang == "ja":
        return {ch for ch in _JA_FUNCTION_RE.sub("", s)}
    return {ch for ch in s if ch not in _ZH_FUNCTION}


def derive_keywords(question: str, answer: str, vocab: List[Phrase], lang: str = "zh") -> List[str]:
    """Hints shown with the question, e.g. 最近 / 仕事. Not a hard gate."""
    if course_pkg.is_spaced(lang):
        q_words = set(_words(question))
        hits = [" ".join(_words(v.text)) for v in vocab
                if _words(v.text) and set(_words(v.text)) <= q_words
                and not set(_words(v.text)) <= _function_words(lang)]
        runs = content_runs(question, lang) or content_runs(answer, lang)
        out = []
        for word in hits + sorted(runs, key=len, reverse=True):
            if word and word not in out:
                out.append(word)
        return out[:3]
    q = _strip(question)
    hits = [v.text for v in vocab if len(v.text) >= 2 and v.text in q]
    runs = content_runs(q, lang) or content_runs(_strip(answer), lang)
    runs.sort(key=len, reverse=True)
    chunks: List[str] = []
    for run in runs:
        if len(run) <= 2:
            chunks.append(run)
        else:
            chunks += [run[i : i + 2] for i in range(0, len(run) - 1, 2)]
    out: List[str] = []
    for word in hits + chunks:
        if word and word not in out:
            out.append(word)
    return out[:3]


class Course:
    """The whole ladder for one language: 6 bands, units, lessons, word bank."""

    def __init__(self, lang: str = "zh") -> None:
        self.lang = course_pkg.normalize(lang)
        self.speech_lang = course_pkg.speech_lang(self.lang)
        self.levels: List[Level] = []
        self.units: List[Unit] = []
        self.lessons: Dict[int, Lesson] = {}
        self.topics: Dict[str, VocabTopic] = {}
        self.vocab_by_band: Dict[int, List[VocabTopic]] = {}

        raw_levels, raw_vocab, prompts = course_pkg.course_data(self.lang)
        self._prompts = prompts
        self._scenes = course_pkg.scenes(self.lang)

        # Build EVERY vocabulary bank, not just the bands that happen to have a
        # level module.  Keying this to the levels loop silently hid whole banks
        # from every audit: while jlpt1.py/jlpt0.py were missing, the 288-word
        # N1 and N1+ banks were never loaded, so kana_check scanned 844 of 1420
        # words and reported "0 issues" for content it had never looked at.  A
        # bank is content in its own right and must not depend on a level file
        # existing to be seen.
        # A word belongs to the easiest band that claims it, and it must be
        # drilled there and nowhere else. Several people write these files at
        # once, so the same word gets filed under two topics: without this it
        # is drilled twice, and a bank quietly pads itself with words the
        # learner already met two bands earlier.
        #
        # Bands run 0 (hardest, N1+) to 5 (easiest, N5), so "easiest first"
        # is *descending* band order. Getting this backwards is quiet and
        # destructive: it hands 山 to an N3 topic and deletes it from N5, so
        # the beginner never meets it at all.
        #
        # Which way is "easiest" is the course's call, not ours: JLPT counts
        # down (N5 -> N1) while HSK and CEFR count up. LEVELS is authored
        # easiest-first, so that order decides; bands with no level module
        # yet fall in after it, in JLPT order for backward compatibility.
        seen_words: Dict[str, str] = {}
        self.duplicate_words: List[Tuple[str, str, str]] = []
        level_order = [int(lv["band"]) for lv in raw_levels]
        band_order = [b for b in level_order if b in raw_vocab] + [
            b for b in sorted(raw_vocab, reverse=True) if b not in level_order]
        for band in band_order:
            for raw in raw_vocab.get(band, []):
                for w in raw["words"]:
                    seen_words.setdefault(w[0], raw["id"])

        # Built in ascending order so the topic ordering downstream is
        # unchanged; ownership was already decided above.
        for band in sorted(raw_vocab):
            topics = self._build_topics(band, raw_vocab, seen_words,
                                        self.duplicate_words)
            self.vocab_by_band[band] = topics
            for topic in topics:
                self.topics[topic.id] = topic

        # The deck (deck.py): the rest of each band's vocabulary, studied as
        # its own topics and met in the library, never injected into a
        # lesson. Kept apart from the bank because the bank must be exactly
        # lessons x inject_by_band, and a band needs thousands of words.
        # A deck word the bank already owns is a duplicate, like any other.
        self.decks_by_band: Dict[int, List[VocabTopic]] = {}
        deck_mod = course_pkg.module_for(self.lang, "deck")
        raw_decks = dict(getattr(deck_mod, "DECKS", None) or {})
        # easiest band first, as above, so a word lands in the band it belongs to
        deck_order = [b for b in level_order if b in raw_decks] + [
            b for b in sorted(raw_decks, reverse=True) if b not in level_order]
        for band in deck_order:
            topics = self._build_topics(band, raw_decks, seen_words,
                                        self.duplicate_words)
            for topic in topics:
                topic.deck = True
                self.topics[topic.id] = topic
            self.decks_by_band[band] = topics

        # The library (library.py): graded stories, the hours of input.
        self.stories: Dict[str, Story] = {}
        lib_mod = course_pkg.module_for(self.lang, "library")
        for raw in list(getattr(lib_mod, "STORIES", None) or []):
            story = Story(
                id=str(raw["id"]),
                band=int(raw["band"]),
                title=raw.get("title", ""),
                title_en=raw.get("title_en", ""),
                chunks=[Phrase(*(list(c) + ["", ""])[:3]) for c in raw.get("chunks", [])],
                questions=list(raw.get("questions") or []),
                voices=int(raw.get("voices") or 1),
            )
            if story.id in self.stories:
                raise ValueError(f"library: story id {story.id!r} defined twice")
            self.stories[story.id] = story

        for raw_level in raw_levels:
            band = int(raw_level["band"])
            level_units: List[Unit] = []
            for raw_unit in raw_level["units"]:
                unit_lessons: List[Lesson] = []
                for raw in raw_unit["lessons"]:
                    patterns = [
                        DrillPattern(
                            text=p["text"],
                            reading=p["reading"],
                            en=p["en"],
                            values=[Phrase(*v) for v in p.get("values", [])],
                            kind=str(p.get("kind") or ""),
                        )
                        for p in raw.get("patterns", [])
                    ]
                    lesson = Lesson(
                        id=raw["id"],
                        unit=raw_unit["id"],
                        title=raw["title"],
                        goal=raw["goal"],
                        vocab=[Phrase(*v) for v in raw["vocab"]],
                        dialogue=[Turn(*t) for t in raw["dialogue"]],
                        # an author may override the shared map right here
                        scene=raw.get("scene") or self._scenes.get(raw["id"], ""),
                        notes=list(raw.get("notes", [])),
                        patterns=patterns,
                        band=band,
                    )
                    self._attach_prompts(lesson)
                    unit_lessons.append(lesson)
                    self.lessons[lesson.id] = lesson
                unit = Unit(
                    id=raw_unit["id"],
                    title=raw_unit["title"],
                    focus=raw_unit["focus"],
                    gate=dict(raw_unit.get("gate", {})),
                    lessons=unit_lessons,
                    band=band,
                )
                level_units.append(unit)
                self.units.append(unit)

            level_id = int(raw_level["id"])
            self.levels.append(
                Level(
                    id=level_id,
                    band=band,
                    code=raw_level.get("code") or f"{course_pkg.band_label(self.lang)} {band}",
                    title=raw_level["title"],
                    focus=raw_level["focus"],
                    gate=dict(raw_level.get("gate", {})),
                    units=level_units,
                    vocab_topics=self.vocab_by_band.get(band, []),
                    deck_topics=self.decks_by_band.get(band, []),
                    story_count=sum(1 for st in self.stories.values() if st.band == band),
                )
            )

        self.lesson_ids: List[int] = sorted(self.lessons)
        self._word_set: Optional[set] = None

    # -- content assembly ---------------------------------------------------
    def _attach_prompts(self, lesson: Lesson) -> None:
        """Turn the author's six strings into a graded free-response prompt."""
        for raw in self._prompts.get(lesson.id, []):
            q_text, q_reading, q_en, a_text, a_reading, a_en = raw
            text = _strip(a_text)
            lesson.prompts.append(
                FreePrompt(
                    q_text=q_text,
                    q_reading=q_reading,
                    q_en=q_en,
                    a_text=a_text,
                    a_reading=a_reading,
                    a_en=a_en,
                    keywords=derive_keywords(q_text, a_text, lesson.vocab, self.lang),
                    min_chars=max(2, len(text) // 3),
                )
            )

    def _build_topics(
        self,
        band: int,
        raw_vocab: dict,
        seen: Optional[Dict[str, str]] = None,
        duplicates: Optional[List[Tuple[str, str, str]]] = None,
    ) -> List[VocabTopic]:
        # `seen` maps word -> owning topic id, decided up front over the whole
        # bank. A word is kept only by its owner; everywhere else it is a
        # duplicate and is dropped, recorded so padding stays visible.
        if seen is None:
            seen = {}
        out: List[VocabTopic] = []
        for raw in raw_vocab.get(band, []):
            words = [Phrase(*w) for w in raw["words"]]
            unique = []
            local = set()
            for w in words:
                if w.text in local:
                    continue
                owner = seen.get(w.text)
                if owner is None:
                    seen[w.text] = raw["id"]
                elif owner != raw["id"]:
                    if duplicates is not None:
                        duplicates.append((w.text, owner, raw["id"]))
                    continue
                local.add(w.text)
                unique.append(w)
            out.append(
                VocabTopic(
                    id=raw["id"],
                    band=band,
                    title=raw["title"],
                    title_native=raw.get("title_native") or raw.get("title_zh") or raw["title"],
                    words=unique,
                )
            )
        return out

    # -- lookups ------------------------------------------------------------
    def unit_of(self, lesson_id: int) -> Optional[Unit]:
        lesson = self.lessons.get(lesson_id)
        if not lesson:
            return None
        return next((u for u in self.units if u.id == lesson.unit), None)

    def level_of(self, lesson_id: int) -> Optional[Level]:
        unit = self.unit_of(lesson_id)
        if not unit:
            return None
        return next((lv for lv in self.levels if lv.band == unit.band), None)

    def level_by_band(self, band: int) -> Optional[Level]:
        return next((lv for lv in self.levels if lv.band == band), None)

    def level_by_id(self, level_id: int) -> Optional[Level]:
        return next((lv for lv in self.levels if lv.id == level_id), None)

    def level_id_of(self, lesson_id: int) -> int:
        level = self.level_of(lesson_id)
        return level.id if level else 1

    def lesson(self, lesson_id: int) -> Optional[Lesson]:
        return self.lessons.get(lesson_id)

    def next_lesson_id(self, lesson_id: int) -> Optional[int]:
        try:
            i = self.lesson_ids.index(lesson_id)
        except ValueError:
            return self.lesson_ids[0]
        return self.lesson_ids[i + 1] if i + 1 < len(self.lesson_ids) else None

    def first_lesson_id(self) -> int:
        return self.lesson_ids[0]

    def lessons_of_band(self, band: int) -> List[Lesson]:
        return sorted((l for l in self.lessons.values() if l.band == band), key=lambda l: l.id)

    def topic(self, topic_id: str) -> Optional[VocabTopic]:
        return self.topics.get(topic_id)

    def vocab_words(self, band: int) -> List[Phrase]:
        """Every word in this band's bank, in topic order."""
        out: List[Phrase] = []
        for topic in self.vocab_by_band.get(band, []):
            out.extend(topic.words)
        return out

    def vocab_for_lesson(self, lesson: Lesson, count: int) -> List[Phrase]:
        """A deterministic slice of the band's bank for one lesson.

        Lesson 1 gets words 0-3, lesson 2 gets 4-7, wrapping around, so a whole
        band walked in order covers its entire bank.
        """
        if count <= 0:
            return []
        words = self.vocab_words(lesson.band)
        if not words:
            return []
        siblings = self.lessons_of_band(lesson.band)
        try:
            index = siblings.index(lesson)
        except ValueError:
            index = 0
        start = (index * count) % len(words)
        return [words[(start + i) % len(words)] for i in range(min(count, len(words)))]

    def deck_words(self, band: int) -> List[Phrase]:
        """Every word in this band's deck (deck.py), in topic order."""
        return [w for t in self.decks_by_band.get(band, []) for w in t.words]

    def stories_of_band(self, band: int) -> List[Story]:
        return sorted((s for s in self.stories.values() if s.band == band), key=lambda s: s.id)

    def story(self, story_id: str) -> Optional[Story]:
        return self.stories.get(str(story_id))

    def vocab_count(self) -> int:
        return sum(len(t.words) for t in self.topics.values())

    # -- word set for the per-course ledger ---------------------------------
    def word_set(self) -> set:
        """Every word this course can teach: bank + every lesson's vocab."""
        if self._word_set is None:
            words: set = set()
            for topic in self.topics.values():
                for w in topic.words:
                    words.add(w.text)
            for lesson in self.lessons.values():
                for v in lesson.vocab:
                    words.add(v.text)
            self._word_set = words
        return self._word_set

    def is_word(self, text: str) -> bool:
        return bool(text) and text in self.word_set()

    def prompt_count(self) -> int:
        return sum(len(l.prompts) for l in self.lessons.values())

    # -- gates --------------------------------------------------------------
    def gate_for(self, lesson_id: int, base_gate: Dict[str, float]) -> Dict[str, float]:
        """Each band (and each unit) can only tighten the gate."""
        gate = dict(base_gate)
        level = self.level_of(lesson_id)
        if level:
            for key, value in level.gate.items():
                gate[key] = max(float(gate.get(key, 0.0)), float(value))
        unit = self.unit_of(lesson_id)
        if unit:
            for key, value in unit.gate.items():
                gate[key] = max(float(gate.get(key, 0.0)), float(value))
        return gate

    def gate_for_band(self, band: int, base_gate: Dict[str, float]) -> Dict[str, float]:
        """Gate for anything that is not a lesson (vocab sessions, review)."""
        gate = dict(base_gate)
        level = self.level_by_band(band)
        if level:
            for key, value in level.gate.items():
                gate[key] = max(float(gate.get(key, 0.0)), float(value))
        return gate

    def lesson_band(self, lesson_id: int) -> int:
        lesson = self.lessons.get(lesson_id)
        return lesson.band if lesson else self.levels[0].band

    # -- drill material -----------------------------------------------------
    def drill_items(self, lesson: Lesson) -> List[Phrase]:
        """Vocab + every line you have to say, used for graduated recall."""
        items: List[Phrase] = []
        seen = set()
        for phrase in lesson.vocab:
            if phrase.text not in seen:
                seen.add(phrase.text)
                items.append(phrase)
        for turn in lesson.dialogue:
            if turn.speaker == "you" and turn.text not in seen:
                seen.add(turn.text)
                items.append(Phrase(turn.text, turn.reading, turn.en, turn.note))
        return items

    def to_dict(self) -> dict:
        return {
            "language": self.lang,
            "speech_lang": self.speech_lang,
            "levels": [lv.to_dict() for lv in self.levels],
            "lesson_count": len(self.lesson_ids),
            "level_count": len(self.levels),
            "vocab_count": self.vocab_count(),
            "prompt_count": self.prompt_count(),
            "story_count": len(self.stories),
        }
