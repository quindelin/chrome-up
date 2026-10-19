"""Session engine: builds the lesson walk-through and enforces the gate."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import course as course_pkg
from . import drills, free, progress as ledger
from .config import reading_mode_for, scene_mode_for
from .curriculum import Course
from .models import Lesson, Phrase, Score
from .pronunciation import evaluate, fluency_reasons
from .think import Target

# Literacy, reading and grammar are per-course modules, resolved by language
# rather than hard-wired to one of them.
#
# This used to import them straight from `course.ja` and then refuse to run
# them for any other language, which left Mandarin with no reading passages,
# no character teaching and no grammar notes - while its own config spent
# thirty lines deciding how to fade the pinyin crutch out. A course that has
# no `hanzi.py` simply gets no hanzi steps; that is the whole mechanism.
_HEAR_NOTE = {"zh": "只听，不看", "ja": "聞くだけ、見ない", "es": "Solo escucha, no mires"}
_WRITE_NOTE = {"zh": "用你自己的话说，不用跟原文一样",
               "ja": "自分の言葉で、原文と同じでなくていい",
               "es": "Con tus propias palabras, no hace falta copiar el texto"}


def inject_count(vocab_cfg: Dict, band: int) -> int:
    """New bank words per lesson in this band.

    `inject_by_band` lets a course hand later bands more words a lesson
    without changing the beginner pace; anything it does not list falls
    back to `inject_per_lesson`.
    """
    by_band = vocab_cfg.get("inject_by_band") or {}
    value = by_band.get(band, by_band.get(str(band)))
    if value is None:
        value = vocab_cfg.get("inject_per_lesson", 4)
    return int(value or 0)


def _course_module(lang: str, name: str):
    """`course.<lang>.<name>`, or None when that course has not written one."""
    try:
        return course_pkg.module_for(lang, name)
    except Exception:  # pragma: no cover - only if a package is incomplete
        return None


@dataclass
class Step:
    kind: str  # listen | speak | recall | info | answer | done
    text: str = ""
    reading: str = ""
    en: str = ""
    speaker: str = ""  # them | you
    prompt_en: str = ""  # English cue for recall items
    note: str = ""
    wait_seconds: float = 0.0
    round: int = 0
    key: str = ""
    # free response only
    sample_text: str = ""
    sample_reading: str = ""
    sample_en: str = ""
    keywords: List[str] = field(default_factory=list)
    min_chars: int = 0
    # literacy only: the second script, and what to call it on screen.
    # あ needs ア beside it and the romaji underneath; 日 needs its on-yomi
    # and its kun-yomi kept apart, because collapsing them into one "reading"
    # line is exactly the confusion a learner arrives with.
    alt: str = ""
    alt_label: str = ""
    kun: str = ""
    # hanzi only: 部首 and 部件. A character is not a picture to be memorised:
    # 你 is 亻 plus 尔 and 妈 is 女 plus 马, and knowing that is what turns 400
    # characters into 40 families instead of 400 separate drawings. Kept out of
    # `alt` because a Japanese radical and a Chinese 部首 are not the same
    # claim about the character.
    radical: str = ""
    components: str = ""
    # audio-only comprehension (`hear`): the line is played but never printed,
    # so it has to travel in a field the UI knows not to render. `text` stays
    # empty; `audio_text` is what gets spoken.
    audio_text: str = ""
    hide_text: bool = False
    # reading passages only: a chunk knows where it sits in the text
    passage_title: str = ""
    chunk_index: int = 0
    chunk_total: int = 0

    def to_dict(
        self,
        show_target: bool = True,
        index: int = 0,
        total: int = 0,
        show_reading: bool = True,
        show_sample: bool = False,
    ) -> dict:
        shown = show_target and not self.hide_text
        return {
            "kind": self.kind,
            "text": self.text if shown else "",
            "reading": self.reading if (shown and show_reading) else "",
            "en": self.en if shown else "",
            "speaker": self.speaker,
            "prompt_en": self.prompt_en,
            "note": self.note,
            "wait_seconds": round(self.wait_seconds, 1),
            "round": self.round,
            "show_target": show_target,
            "show_reading": bool(show_target and show_reading),
            "show_sample": show_sample,
            "sample": {
                "text": self.sample_text if show_sample else "",
                "reading": self.sample_reading if (show_sample and show_reading) else "",
                "en": self.sample_en if show_sample else "",
            },
            "keywords": list(self.keywords),
            "alt": self.alt,
            "alt_label": self.alt_label,
            "kun": self.kun,
            "radical": self.radical,
            "components": self.components,
            "audio_text": self.audio_text,
            "hide_text": bool(self.hide_text),
            "passage_title": self.passage_title,
            "chunk_index": self.chunk_index,
            "chunk_total": self.chunk_total,
            "index": index,
            "total": total,
        }


class Session:
    """One learner, one conversation. Never advances on a failed attempt."""

    def __init__(self, course: Course, cfg: Dict, progress: Dict):
        self.course = course
        self.cfg = cfg
        self.lang = course.lang
        self.progress = progress
        self.mode: str = "lesson"  # lesson | think | review | vocab
        self.lesson_id: int = int(progress.get("lesson_id") or course.first_lesson_id())
        self.band: int = course.lesson_band(self.lesson_id)
        self.level_id: int = course.level_id_of(self.lesson_id)
        self.topic_id: str = ""
        self.steps: List[Step] = []
        self.pos: int = 0
        self.attempts: int = 0
        self.history: List[dict] = []
        self.last_score: Optional[dict] = None
        # the line you just got right, so the glasses can show it in full on
        # the next screen: a recall is answered from the English alone, and
        # without this you never see the characters of a line you passed
        self.last_line: Optional[dict] = None
        self.message: str = ""
        self.thought: Optional[Target] = None
        self.think_done: int = 0
        self._saved: Optional[tuple] = None  # (steps, pos) parked while in think mode
        # optional content modules, resolved per course. Any of them can be
        # missing: a course with no readings simply has no reading steps.
        self._kana = _course_module(self.lang, "kana")
        self._kanji = _course_module(self.lang, "kanji")
        self._hanzi = _course_module(self.lang, "hanzi")
        self._readings = _course_module(self.lang, "readings")
        self._summaries = _course_module(self.lang, "summaries")
        self._grammar = _course_module(self.lang, "grammar")
        self.start_lesson(self.lesson_id)

    # -- lesson construction ------------------------------------------------
    def start_lesson(self, lesson_id: int) -> None:
        lesson = self.course.lesson(lesson_id)
        if not lesson:
            lesson_id = self.course.first_lesson_id()
            lesson = self.course.lesson(lesson_id)
        self.lesson_id = lesson_id
        self.mode = "lesson"
        self.band = lesson.band
        self.level_id = self.course.level_id_of(lesson_id)
        self.pos = 0
        self.attempts = 0
        self.thought = None
        self._saved = None
        self.steps = self._build_steps(lesson_id)
        self.progress["lesson_id"] = lesson_id
        self.message = f"Unit {lesson.unit} · Lesson {lesson.id}: {lesson.title}"

    def _new_words(self, lesson: Lesson) -> List[Phrase]:
        """A slice of the word bank, folded into this lesson."""
        vocab_cfg = self.cfg.get("vocab") or {}
        if not vocab_cfg.get("enabled", True):
            return []
        return self.course.vocab_for_lesson(lesson, inject_count(vocab_cfg, lesson.band))

    # -- English orientation ------------------------------------------------
    def scene_text(self, lesson: Optional[Lesson] = None) -> str:
        """The one sentence that says who you are talking to and where."""
        lesson = lesson or self.course.lesson(self.lesson_id)
        if not lesson:
            return ""
        return lesson.scene or lesson.goal

    def scene_shown(self, lesson: Lesson) -> bool:
        """Whether this band prints the scene, or keeps it one keypress away.

        always -> every lesson opens with it
        first  -> only the first lesson of each unit
        tip    -> never printed; the tip key reveals it
        never  -> gone
        """
        mode = scene_mode_for(self.cfg, self.level_id)
        if mode in ("tip", "never"):
            return False
        if mode == "first":
            unit = self.course.unit_of(lesson.id)
            if not unit or not unit.lessons:
                return True
            return min(l.id for l in unit.lessons) == lesson.id
        return True

    # -- literacy and reading ----------------------------------------------
    def _kana_steps(self, lesson_id: int) -> List[Step]:
        """The slice of the syllabary this lesson is responsible for.

        Non-speech: you look at あ and ア and the romaji together, once, and
        move on. Drilling five kana a day as speech is busywork; what makes
        them stick is meeting them in the dialogue that follows, which is
        exactly where the next steps put them.
        """
        cfg = self.cfg.get("kana") or {}
        if not cfg.get("enabled", True) or not self._kana:
            return []
        rows = self._kana.kana_for_lesson(
            lesson_id,
            int(cfg.get("per_lesson", 5) or 5),
            int(cfg.get("through_lesson", 8) or 8),
        )
        out: List[Step] = []
        for hira, kata, romaji in rows:
            out.append(
                Step(
                    kind="kana",
                    text=hira,
                    reading=romaji,
                    alt=kata,
                    alt_label="カタカナ",
                    en="",
                    note=self._kana.group_of(hira),
                    key=f"kana:{hira}",
                )
            )
        return out

    def _kanji_steps(self, lesson: Lesson) -> List[Step]:
        """The characters the lesson's own vocabulary is built from.

        Derived rather than scheduled, for two reasons. A kanji never turns
        up before a word that uses it, so the learner always has somewhere
        to hang it; and a gap in the table shows up as a missing step rather
        than as a crash, which is what makes a partial table safe to ship.
        """
        cfg = self.cfg.get("kanji") or {}
        if not cfg.get("enabled", True) or not self._kanji:
            return []
        # anything a previous lesson already introduced is not new here
        known: set = set()
        for lid in self.course.lesson_ids:
            if lid >= lesson.id:
                break
            for word in self.course.lessons[lid].vocab:
                known |= set(self._kanji.kanji_in(word.text))
        words = [(v.text, v.reading, v.en) for v in lesson.vocab]
        picked = self._kanji.for_lesson(words, int(cfg.get("per_lesson", 3) or 3), known)
        out: List[Step] = []
        for row in picked:
            example = next((w for w in lesson.vocab if row["char"] in w.text), None)
            note = f"{example.text}（{example.reading}）" if example else ""
            out.append(
                Step(
                    kind="kanji",
                    text=row["char"],
                    reading="・".join(row["on"]) or "—",
                    kun="・".join(row["kun"]) or "—",
                    en=row["en"],
                    alt_label="音",
                    note=note,
                    key=f"kanji:{row['char']}",
                )
            )
        return out

    def _reading_steps(self, lesson: Lesson) -> List[Step]:
        """The passage, read aloud a sentence at a time, then a question.

        Chunked because a whole paragraph cannot be graded as one spoken
        attempt - the gate allows fifteen seconds - and because reading a
        passage aloud in sentences is closer to how you actually read it.
        """
        cfg = self.cfg.get("reading") or {}
        if not cfg.get("enabled", True) or not self._readings:
            return []
        passage = self._readings.get(lesson.id)
        chunks = passage.get("chunks") or []
        if not chunks:
            return []
        out: List[Step] = [
            Step(
                kind="info",
                en=f"Reading: {passage.get('title_en', '')} · {len(chunks)} lines",
                wait_seconds=3.0,
                key=f"read:{lesson.id}:head",
            )
        ]
        for n, chunk in enumerate(chunks, 1):
            text, reading, en = (list(chunk) + ["", "", ""])[:3]
            out.append(
                Step(
                    kind="read",
                    text=text,
                    reading=reading,
                    en=en,
                    passage_title=passage.get("title", ""),
                    chunk_index=n,
                    chunk_total=len(chunks),
                    key=f"read:{lesson.id}:{n}",
                )
            )
        if cfg.get("comprehension", True):
            questions = passage.get("questions") or []
            if questions:
                out.append(
                    self._comprehension_step(lesson, questions[0], f"read-q:{lesson.id}",
                                             "from the passage you just read")
                )
        return out

    def _comprehension_step(self, lesson: Lesson, q: Dict, key: str, note: str) -> Step:
        """One question about a text, answered in the language and gated."""
        return Step(
            kind="answer",
            text=q.get("q", ""),
            reading=q.get("q_reading", ""),
            en=q.get("q_en", ""),
            speaker="them",
            prompt_en=q.get("q_en", ""),
            sample_text=q.get("a", ""),
            sample_reading=q.get("a_reading", ""),
            sample_en=q.get("a_en", ""),
            keywords=list(q.get("keywords") or []),
            min_chars=int(q.get("min_chars") or 0),
            key=key,
            note=note,
        )

    def _hearing_steps(self, lesson: Lesson) -> List[Step]:
        """Listen to one line of the passage with nothing on the screen.

        This is the step the course did not have. Every other input the
        learner gets arrives printed as well as spoken: the hanzi, the pinyin
        and the English are all on the glasses while the audio plays, so what
        is being trained is reading-along. Real listening is decoding a signal
        you cannot see, which is a different skill and the one HSK 听力 tests.

        So: the line is played, nothing is printed, and the question that
        follows can only be answered if the audio was understood. The text
        travels in `audio_text`, which the UI speaks and never renders - and
        `hide_text` is what stops a future author from leaking it by accident.
        """
        cfg = self.cfg.get("listening") or {}
        if not cfg.get("comprehension", True) or not self._readings:
            return []
        passage = self._readings.get(lesson.id)
        chunks = passage.get("chunks") or []
        questions = passage.get("questions") or []
        if not chunks or not questions:
            return []
        # a different chunk from the one the reading question leans on, and a
        # different question, so "I recognised the words I just read" is not
        # the same as "I understood what I heard"
        chunk = chunks[-1]
        q = questions[1] if len(questions) > 1 else questions[0]
        text, reading, _en = (list(chunk) + ["", "", ""])[:3]
        return [
            Step(
                kind="hear",
                audio_text=text,
                hide_text=True,
                reading=reading,
                en="Listen. Nothing on the screen.",
                # in the course's own language: this note used to be Chinese
                # on the Japanese course too
                note=_HEAR_NOTE.get(self.lang, _HEAR_NOTE["zh"]),
                key=f"hear:{lesson.id}",
            ),
            self._comprehension_step(lesson, q, f"hear-q:{lesson.id}",
                                     "from the line you just heard"),
        ]

    def _writing_steps(self, lesson: Lesson) -> List[Step]:
        """Say the passage back, shorter.

        Only from the band where a summary is worth asking for. Graded on
        coverage of the passage's key points rather than on wording, which is
        why the sample is presented as one possible summary and never as a
        reference to match - see `free.grade_writing`.
        """
        cfg = self.cfg.get("writing") or {}
        if not cfg.get("enabled", True) or not self._summaries:
            return []
        if int(self.band or 0) < int(cfg.get("min_band", 6) or 6):
            return []
        item = self._summaries.get(lesson.id)
        if not item:
            return []
        return [
            Step(
                kind="write",
                text=item.get("prompt", ""),
                reading=item.get("prompt_reading", ""),
                en=item.get("prompt_en", ""),
                speaker="them",
                prompt_en=item.get("prompt_en", ""),
                sample_text=item.get("sample", ""),
                sample_reading=item.get("sample_reading", ""),
                sample_en=item.get("sample_en", ""),
                keywords=list(item.get("keywords") or []),
                min_chars=int(item.get("min_chars")
                              or cfg.get("min_chars", 30) or 30),
                key=f"write:{lesson.id}",
                note=_WRITE_NOTE.get(self.lang, _WRITE_NOTE["zh"]),
            )
        ]

    def _hanzi_steps(self, lesson: Lesson) -> List[Step]:
        """The characters the lesson's own vocabulary is built from.

        Mandarin has no syllabary to teach, which is exactly why this used to
        be skipped: it looked like the problem was Japanese-only. It is not.
        Pinyin gets you from sound to meaning and never builds the other
        direction, so a learner who stops seeing pinyin has nothing to stand
        on - and HSK 5-6 is mostly a reading exam. A character is taught with
        its 部首 and its 部件, because 妈 is 女 plus 马 and noticing that is
        the difference between memorising drawings and learning a system.
        """
        cfg = self.cfg.get("hanzi") or {}
        if not cfg.get("enabled", True) or not self._hanzi:
            return []
        known: set = set()
        for lid in self.course.lesson_ids:
            if lid >= lesson.id:
                break
            for word in self.course.lessons[lid].vocab:
                known |= set(self._hanzi.hanzi_in(word.text))
        words = [(v.text, v.reading, v.en) for v in lesson.vocab]
        picked = self._hanzi.for_lesson(words, int(cfg.get("per_lesson", 3) or 3), known)
        out: List[Step] = []
        for row in picked:
            example = next((w for w in lesson.vocab if row["char"] in w.text), None)
            note = f"{example.text} · {example.reading}" if example else ""
            out.append(
                Step(
                    kind="hanzi",
                    text=row["char"],
                    reading=row.get("pinyin", ""),
                    en=row.get("en", ""),
                    radical=row.get("radical", ""),
                    components=row.get("components", ""),
                    alt_label="部首",
                    note=note,
                    key=f"hanzi:{row['char']}",
                )
            )
        return out

    def _build_steps(self, lesson_id: int) -> List[Step]:
        lesson = self.course.lesson(lesson_id)
        assert lesson is not None
        steps: List[Step] = []

        # 0. where you are standing. Pimsleur has to speak this in English
        #    because audio is all it has; we print it, so the whole audio track
        #    stays in the target language. The scene is a signpost: it tells
        #    you who and where, never what the words mean.
        if self.scene_shown(lesson):
            steps.append(
                Step(
                    kind="info",
                    en=self.scene_text(lesson),
                    wait_seconds=float((self.cfg.get("ui") or {}).get("scene_seconds", 6.0) or 0.0),
                    key=f"scene:{lesson_id}",
                )
            )

        # 0b. the syllabary, for the lessons that need it. This comes before
        # the conversation on purpose: you cannot read a line you are being
        # asked to speak, and for the first few lessons the only reason you
        # cannot read it is that nobody has shown you あ yet.
        for row in self._kana_steps(lesson_id):
            steps.append(row)

        # 1. the conversation: their lines are input, your lines are gated
        for turn in lesson.dialogue:
            steps.append(
                Step(
                    kind="listen" if turn.speaker == "them" else "speak",
                    text=turn.text,
                    reading=turn.reading,
                    en=turn.en,
                    speaker=turn.speaker,
                    note=turn.note,
                    key=f"{lesson_id}:{turn.text}",
                )
            )

        # 2. new words: hear it modelled once, then say it from the English
        #    alone. The modelled pass is not decoration - a word has to exist
        #    in your ear before you can be asked to produce it. Asking for a
        #    word you have never heard is not recall, it is guessing, and it
        #    only fails the gate. So the order is target language first
        #    (heard), English second (as the cue), target language last (said
        #    by you) - which is Pimsleur's anticipation.
        new_words = self._new_words(lesson)
        for word in new_words:
            steps.append(
                Step(
                    kind="listen",
                    text=word.text,
                    reading=word.reading,
                    en=word.en,
                    speaker="them",
                    note=f"new word · {word.en}",
                    key=f"vocab:{word.text}",
                )
            )
            steps.append(
                Step(
                    # no anticipation gap here: this is the word's first-ever
                    # encounter, so the gloss is the point, not a rescue
                    kind="recall",
                    text=word.text,
                    reading=word.reading,
                    en=word.en,
                    prompt_en=word.en,
                    note=f"new word · {word.en}",
                    round=0,
                    key=f"vocab:{word.text}",
                )
            )

        # 3. substitution drills - one frame, many slot values
        drill_pool = drills.generate(lesson, self.cfg, self.lang)
        for item in drill_pool:
            steps.append(
                Step(
                    kind="recall",
                    text=item.text,
                    reading=item.reading,
                    en=item.en,
                    prompt_en=item.en,
                    round=0,
                    key=f"{lesson_id}:{item.text}",
                )
            )

        # 3b. old words in new frames - the interleaving pass.  Repeating a
        # fixed line mostly trains recitation; making the learner produce a
        # word from lesson 5 inside a frame from lesson 30 is what actually
        # strengthens retrieval.
        recycled = drills.recombine(
            self.course,
            lesson,
            int((self.cfg.get("drills") or {}).get("recombine", 4) or 4),
        )
        for item in recycled:
            steps.append(
                Step(
                    kind="recall",
                    text=item.text,
                    reading=item.reading,
                    en=item.en,
                    prompt_en=item.en,
                    round=0,
                    key=f"{lesson_id}:{item.text}",
                )
            )

        # 3c. the characters those words are made of. Placed after the words,
        # not before: a character is easier to keep when you already have a
        # word that uses it. Non-speech - you look at it, you do not recite
        # it. Which script this is depends on the course: 漢字 for Japanese,
        # 汉字 with its 部首 and 部件 for Mandarin.
        for row in self._kanji_steps(lesson):
            steps.append(row)
        for row in self._hanzi_steps(lesson):
            steps.append(row)

        # 3d. the reading passage: several sentences that hang together, read
        # aloud, then a question that can only be answered from the text.
        for row in self._reading_steps(lesson):
            steps.append(row)

        # 3e. and the same text heard without being seen. Reading it first is
        # what makes the audio comprehensible; hearing it with the page blank
        # is what makes it listening.
        for row in self._hearing_steps(lesson):
            steps.append(row)

        # 3f. then say it back shorter. HSK 6 写作 is a timed 缩写 and there
        # is no way to get there from memorised lines; the hard part of 缩写
        # is deciding what to drop while keeping the point, and that is just
        # as hard spoken as written - which is the only way it fits a course
        # you use with your voice while wearing glasses.
        for row in self._writing_steps(lesson):
            steps.append(row)

        # 4. free response - the model asks, you answer in your own words
        free_cfg = self.cfg.get("free") or {}
        answers: List[Phrase] = []
        if free_cfg.get("enabled", True):
            for prompt in lesson.prompts[: int(free_cfg.get("per_lesson", 2) or 2)]:
                steps.append(
                    Step(
                        kind="answer",
                        text=prompt.q_text,
                        reading=prompt.q_reading,
                        en=prompt.q_en,
                        prompt_en=prompt.q_en,
                        speaker="them",
                        sample_text=prompt.a_text,
                        sample_reading=prompt.a_reading,
                        sample_en=prompt.a_en,
                        keywords=list(prompt.keywords),
                        min_chars=int(prompt.min_chars or 0),
                        key=f"free:{prompt.q_text}",
                    )
                )
                answers.append(Phrase(prompt.a_text, prompt.a_reading, prompt.a_en))
                # then drill the model answer, so the good form is in your mouth
                steps.append(
                    Step(
                        kind="speak",
                        text=prompt.a_text,
                        reading=prompt.a_reading,
                        en=prompt.a_en,
                        speaker="you",
                        note="a good answer",
                        key=f"free:{prompt.a_text}",
                    )
                )

        # 5. graduated interval recall of everything you just met
        items = self.course.drill_items(lesson) + drill_pool + recycled + new_words + answers
        intervals = list(self.cfg["recall"].get("intervals") or [10, 30, 75])
        rounds = int(self.cfg["recall"].get("rounds") or 3)
        anticipation = float((self.cfg.get("recall") or {}).get("anticipation_seconds", 0.0) or 0.0)
        for r in range(rounds):
            wait = 0.0 if r == 0 else float(intervals[min(r - 1, len(intervals) - 1)])
            steps.append(
                Step(
                    kind="info",
                    text="",
                    reading="",
                    en=f"Recall round {r + 1} of {rounds}",
                    wait_seconds=wait,
                    round=r + 1,
                )
            )
            # rotate the order each round so it isn't pure rote
            rotated = items[r % len(items):] + items[: r % len(items)] if items else []
            for item in rotated:
                steps.append(
                    Step(
                        kind="recall",
                        text=item.text,
                        reading=item.reading,
                        en=item.en,
                        prompt_en=item.en,
                        note=item.note,
                        # the pause before the English lands: retrieve with a
                        # blank screen, and the cue only rescues a blank
                        wait_seconds=anticipation,
                        round=r + 1,
                        key=f"{lesson_id}:{item.text}",
                    )
                )
        return steps

    # -- vocabulary sessions -----------------------------------------------
    def start_vocab(self, topic_id: str) -> int:
        """Drill one themed slice of the word bank: hear, say, recall."""
        topic = self.course.topic(topic_id)
        if not topic:
            self.message = "No such vocabulary topic."
            return 0
        if self.mode not in ("vocab", "review"):
            self._saved = (self.steps, self.pos)
        self.mode = "vocab"
        self.topic_id = topic.id
        self.band = topic.band
        level = self.course.level_by_band(topic.band)
        self.level_id = level.id if level else 1
        self.pos = 0
        self.attempts = 0
        self.thought = None

        steps: List[Step] = []
        for word in topic.words:
            steps.append(
                Step(
                    kind="listen",
                    text=word.text,
                    reading=word.reading,
                    en=word.en,
                    speaker="them",
                    key=f"vocab:{word.text}",
                )
            )
            steps.append(
                Step(
                    kind="speak",
                    text=word.text,
                    reading=word.reading,
                    en=word.en,
                    speaker="you",
                    note=word.en,
                    key=f"vocab:{word.text}",
                )
            )
        rounds = int((self.cfg.get("vocab") or {}).get("recall_rounds", 2) or 2)
        anticipation = float((self.cfg.get("recall") or {}).get("anticipation_seconds", 0.0) or 0.0)
        for r in range(rounds):
            wait = 0.0 if r == 0 else 20.0
            steps.append(
                Step(kind="info", en=f"Recall round {r + 1} of {rounds}",
                     wait_seconds=wait, round=r + 1)
            )
            rotated = topic.words[r % len(topic.words):] + topic.words[: r % len(topic.words)]
            for word in rotated:
                steps.append(
                    Step(
                        kind="recall",
                        text=word.text,
                        reading=word.reading,
                        en=word.en,
                        prompt_en=word.en,
                        wait_seconds=anticipation,
                        round=r + 1,
                        key=f"vocab:{word.text}",
                    )
                )
        self.steps = steps
        label = (self.cfg.get("ui") or {}).get("vocab_label", "Vocabulary")
        self.message = f"{label} · {topic.title} ({topic.title_native}): {len(topic.words)} words"
        return len(topic.words)

    # -- current state ------------------------------------------------------
    def current(self) -> Optional[Step]:
        if self.pos < len(self.steps):
            return self.steps[self.pos]
        return None

    def gate(self) -> Dict:
        if self.mode == "vocab":
            return self.course.gate_for_band(self.band, self.cfg["gate"])
        return self.course.gate_for(self.lesson_id, self.cfg["gate"])

    def reference_text(self) -> str:
        """What the scorer compares against. Free response has no reference."""
        step = self.current()
        if not step:
            return ""
        if step.kind in ("answer", "write"):
            return ""
        return step.text

    def needs_speech(self) -> bool:
        step = self.current()
        return bool(step and step.kind in ("speak", "recall", "answer", "read", "write"))

    def show_target(self) -> bool:
        step = self.current()
        if not step:
            return True
        if step.kind == "answer":
            return True  # the question is always on screen
        if step.kind == "read":
            return True  # you cannot read a blank page
        if step.kind != "recall":
            return True
        reveal_after = int(self.cfg["gate"].get("reveal_after_attempts", 2))
        return self.attempts >= reveal_after

    def reading_mode(self) -> str:
        return reading_mode_for(self.cfg, self.level_id)

    def show_reading(self, step: Optional[Step] = None) -> bool:
        """The reading line fades out as you climb: always -> fade -> reveal -> never."""
        step = step or self.current()
        if not step:
            return True
        mode = self.reading_mode()
        if mode == "always":
            return True
        if mode == "never":
            return False
        if mode == "fade":
            # You see it when the line is taught, not when you must retrieve
            # it. A passage counts as retrieval: from N4 on, reading practice
            # means reading the characters, and the kana line is the thing
            # being weaned off.
            return step.kind not in ("recall", "read")
        if mode == "reveal":
            reveal_after = int(self.cfg["gate"].get("reveal_after_attempts", 2))
            return self.attempts >= reveal_after
        return True

    def show_sample(self) -> bool:
        """Show the model answer only once you have tried (and failed) twice."""
        step = self.current()
        if not step or step.kind != "answer":
            return False
        reveal_after = int(self.cfg["gate"].get("reveal_after_attempts", 2))
        return self.attempts >= reveal_after

    def slow_replay(self) -> bool:
        return self.attempts >= int(self.cfg["gate"].get("slow_replay_after_attempts", 2))

    # -- transitions --------------------------------------------------------
    def advance_non_speech(self, at: Optional[int] = None) -> bool:
        """Move past listen/info steps. Never skips a gated step.

        With `at`, only move if we are still on that step (duplicate requests
        from a second client must not skip the next line).
        """
        if at is not None and at != self.pos:
            return False
        step = self.current()
        if not step:
            return False
        if step.kind in ("listen", "info", "kana", "kanji", "hanzi", "hear"):
            self.pos += 1
            self.attempts = 0
            return True
        return False

    def submit(self, score: Score) -> dict:
        """Grade one spoken attempt. Failing keeps you on the same line."""
        step = self.current()
        if not step:
            return {"passed": False, "reasons": ["Lesson finished."], "advanced": False}
        # `write` is yours to say too: a 缩写 is produced by the learner, even
        # though it looks like a question because the prompt is on screen.
        if step.kind not in ("speak", "recall", "answer", "read", "write"):
            return {
                "passed": False,
                "reasons": ["That line is the other person's - just listen."],
                "advanced": False,
            }

        gate = self.gate()
        reference = self.reference_text()
        if step.kind == "answer":
            passed, reasons = free.grade(
                score, step, gate, self.cfg, self.lang, self.band
            )
        elif step.kind == "write":
            passed, reasons = free.grade_writing(
                score, step, gate, self.cfg, self.lang, self.band
            )
        else:
            passed, reasons = evaluate(score, gate)
            # fluency is graded on top of the segmental gate, never instead of
            # it: a fluent wrong answer is still a wrong answer
            slower = fluency_reasons(
                score, reference, self.cfg, self.lang, self.band
            )
            if slower:
                passed = False
                reasons = list(reasons) + slower
        self.attempts += 1
        max_attempts = int(gate.get("max_attempts", 0) or 0)
        forced_advance = max_attempts > 0 and self.attempts >= max_attempts and not passed

        self.last_score = score.to_dict()
        self.last_score["passed"] = passed
        self.last_score["reasons"] = reasons
        # Only a pass (or a give-up advance) reveals the line: showing it after
        # a miss would hand over the answer before the second try.
        if (passed or forced_advance) and step.kind in ("speak", "recall", "read"):
            self.last_line = {"text": step.text, "reading": step.reading,
                              "en": step.en or step.prompt_en, "passed": bool(passed)}

        # feed the per-course ledger: every attempt counts, and a real pass
        # (not a give-up advance) adds the line to the word list the phone shows
        duration = float(getattr(score, "duration", 0.0) or 0.0)
        ledger.record_attempt(self.progress, bool(passed or forced_advance), duration)
        # the per-syllable detail is the only part of a score that says *what*
        # to fix, and it used to be dropped as soon as the attempt was graded
        try:
            ledger.record_syllables(self.progress, list(getattr(score, "syllables", []) or []))
        except Exception:  # pragma: no cover - never let telemetry break a lesson
            pass
        if passed and not forced_advance and self.mode != "think" and step.kind != "answer":
            if self.mode == "vocab":
                band, lesson_id = self.band, None
            else:
                band = self.course.lesson_band(self.lesson_id) if self.lesson_id else self.band
                lesson_id = self.lesson_id
            ledger.record_learned(
                self.progress,
                step.text,
                step.reading,
                step.en or step.prompt_en,
                "word" if self.course.is_word(step.text) else "phrase",
                band,
                lesson_id,
                score.pron,
            )

        result = {
            "passed": passed,
            "reasons": reasons,
            "attempt": self.attempts,
            "advanced": False,
            "slow_replay": not passed and self.slow_replay(),
            "attempts_left": (max_attempts - self.attempts) if max_attempts else None,
            "lesson_complete": False,
            "next_lesson": None,
            "mode": self.mode,
        }

        self.history.append(
            {
                "t": round(time.time()),
                "text": (score.recognized or step.text)
                if step.kind == "answer"
                else step.text,
                "kind": step.kind,
                "passed": passed,
                "score": score.pron,
                "attempt": self.attempts,
            }
        )
        self.history = self.history[-50:]

        if step.key:
            mastery = self.progress.setdefault("mastery", {})
            prev = mastery.get(step.key)
            if passed or prev is not None:
                # A pass promotes the line; a lapse - or a forced advance on a
                # line you never actually passed - sends it back.  Without the
                # lapse branch a line you have failed five times returns on the
                # same schedule as one you nailed, which is precisely the thing
                # that makes spaced repetition work.
                stage = prev.get("stage", 0) if isinstance(prev, dict) else int(prev or 0)
                entry = dict(prev) if isinstance(prev, dict) else {}
                entry.update(
                    {
                        "text": step.text,
                        "reading": step.reading,
                        "en": step.en or step.prompt_en,
                        "ts": time.time(),
                    }
                )
                entry["stage"] = (
                    min(drills.MAX_STAGE, stage + 1) if passed else max(0, stage - 2)
                )
                mastery[step.key] = entry

        if passed or forced_advance:
            if self.mode == "think":
                self.think_done += 1
                self.mode = "lesson"
                self._restore_lesson()
                self.attempts = 0
                self.message = "Got it. Back to the lesson."
                result["advanced"] = True
                result["mode"] = "lesson"
                return result

            self.pos += 1
            self.attempts = 0
            result["advanced"] = True
            if self.pos >= len(self.steps) and self.mode == "review":
                self.message = "Review done - those lines will come back again."
                self.mode = "lesson"
                self._restore_lesson()
                result["review_complete"] = True
                result["mode"] = "lesson"
                return result
            if self.pos >= len(self.steps) and self.mode == "vocab":
                topic = self.course.topic(self.topic_id)
                self.message = (
                    f"Done: {len(topic.words) if topic else 0} words practised."
                    " They will come back in review."
                )
                self.mode = "lesson"
                self.topic_id = ""
                self._restore_lesson()
                result["vocab_complete"] = True
                result["mode"] = "lesson"
                return result
            if self.pos >= len(self.steps):
                result["lesson_complete"] = True
                completed = set(self.progress.get("completed", []))
                completed.add(self.lesson_id)
                self.progress["completed"] = sorted(completed)
                nxt = self.course.next_lesson_id(self.lesson_id)
                result["lesson_id"] = self.lesson_id
                result["next_lesson"] = nxt
                if nxt is not None:
                    self.start_lesson(nxt)
                    self.message = f"Lesson {result['lesson_id']} complete. Next: lesson {nxt}."
                else:
                    self.message = "Course complete. You finished every lesson."
            else:
                self.message = "Good. Next line."
        else:
            self.message = "Not clear enough - listen, then say it again."
        return result

    def set_think(self, target: Target) -> None:
        """Think-in-the-language mode: one line, drilled until it is right."""
        if self.mode != "think":
            self._saved = (self.steps, self.pos)
        self.mode = "think"
        self.thought = target
        self.attempts = 0
        self.steps = [
            Step(
                kind="speak",
                text=target.text,
                reading=target.reading,
                en=target.en,
                speaker="you",
                note=target.note,
                key=f"think:{target.text}",
            )
        ]
        self.pos = 0
        self.message = f"Your thought: {target.text}"

    def _restore_lesson(self) -> None:
        """Put the parked lesson walk-through back after a think drill."""
        if self._saved:
            self.steps, self.pos = self._saved
            self._saved = None
            self.pos = min(self.pos, max(0, len(self.steps) - 1))
        else:
            self.steps = self._build_steps(self.lesson_id)
            self.pos = 0
        self.thought = None

    def exit_think(self) -> None:
        if self.mode == "think":
            self.mode = "lesson"
            self._restore_lesson()
            self.attempts = 0
            self.message = "Back to the lesson."

    def start_review(self, limit: int = 20) -> int:
        """Endless practice: every mastered line that is due, one pass each."""
        # Respect the intervals: a line you aced a minute ago is not due.  Only
        # pad with not-yet-due lines when the queue is short, because an empty
        # review is worse than a slightly early one.
        items = drills.due_items(self.progress, limit, include_fresh=False)
        if len(items) < limit:
            seen = {i.text for i in items}
            items += [
                i
                for i in drills.due_items(self.progress, limit, include_fresh=True)
                if i.text not in seen
            ][: limit - len(items)]
        if not items:
            self.message = "Nothing due for review yet - finish a lesson first."
            return 0
        if self.mode != "review":
            self._saved = (self.steps, self.pos)
        self.mode = "review"
        self.attempts = 0
        self.steps = [
            Step(
                kind="recall",
                text=item.text,
                reading=item.reading,
                en=item.en,
                prompt_en=item.en,
                key=f"review:{item.text}",
            )
            for item in items
        ]
        self.pos = 0
        self.message = f"Review: {len(items)} lines are due."
        return len(items)

    def review_queue_size(self) -> int:
        return len(drills.due_items(self.progress, 200))

    # -- serialisation ------------------------------------------------------
    def state(self) -> dict:
        lesson = self.course.lesson(self.lesson_id)
        unit = self.course.unit_of(self.lesson_id)
        level = self.course.level_of(self.lesson_id)
        step = self.current()
        index = min(self.pos, len(self.steps))
        return {
            "mode": self.mode,
            "lesson": lesson.to_dict() if lesson else None,
            "unit": {"id": unit.id, "title": unit.title, "focus": unit.focus} if unit else None,
            "level": {
                "id": level.id,
                "band": level.band,
                "code": level.code,
                "title": level.title,
                "focus": level.focus,
            }
            if level
            else None,
            "progress": {
                "lesson_id": self.lesson_id,
                "completed": self.progress.get("completed", []),
                "lesson_count": len(self.course.lesson_ids),
            },
            "step": (
                step.to_dict(
                    self.show_target(),
                    index,
                    len(self.steps),
                    self.show_reading(step),
                    self.show_sample(),
                )
                if step
                else None
            ),
            # the scene is on the payload even when it is not printed, so the
            # tip key can still get you oriented at the highest bands
            "scene": self.scene_text(lesson) if self.mode == "lesson" else "",
            "position": {"index": index, "total": len(self.steps)},
            "reading_mode": self.reading_mode(),
            "topic": (
                {
                    "id": self.topic_id,
                    "title": self.course.topic(self.topic_id).title,
                    "title_native": self.course.topic(self.topic_id).title_native,
                }
                if self.mode == "vocab" and self.course.topic(self.topic_id)
                else None
            ),
            "attempts": self.attempts,
            "gate": self.gate(),
            "slow_replay": self.slow_replay(),
            "last_score": self.last_score,
            "message": self.message,
            "thought": self.thought.to_dict() if self.thought else None,
            "history": self.history[-8:],
            "review_due": self.review_queue_size(),
            # the grammar page for this lesson, if the course has written one
            "grammar": (self._grammar.for_lesson(self.lesson_id)
                        if self._grammar else []),
            # what the glasses waveguide should show for this step
            "glasses": self.glasses_card(),
        }

    def glasses_card(self) -> dict:
        """What the glasses display shows for the current step, ready to draw.

        The phone apps used to build this themselves from `step`, and got it
        wrong in a way that hid most of every lesson: a recall step sends no
        `text` or `en` (only `prompt_en`, so you answer from memory), so
        recall - three steps in four - came out as a bare "…". Info and
        listening steps did the same. Deciding it here gives every client
        (iOS, Android, the web page) one rule set, and a test.

            header   where you are: lesson and position
            cue      what to do, small: "Say it in Mandarin", "Listen"
            target   the big line: characters, or the English cue on a recall
            reading  pinyin / kana, when this step may show it
            english  the meaning, when this step may show it
            footer   the line you just passed, in full; or why you missed
        """
        step = self.current()
        lesson = self.course.lesson(self.lesson_id) if self.mode == "lesson" else None
        total = len(self.steps)
        index = min(self.pos, total)
        if lesson:
            where = f"L{lesson.id} · {lesson.title}"
        elif self.mode == "vocab" and self.course.topic(self.topic_id):
            where = self.course.topic(self.topic_id).title
        else:
            where = {"review": "Review", "think": "Think"}.get(self.mode, "LinguaLens")
        header = f"{where} · {min(index + 1, total)}/{total}" if total else where
        card = {"header": header, "cue": "", "target": "", "reading": "", "english": "",
                "footer": ""}
        if not step:
            card["target"] = "Lesson complete"
            card["cue"] = "Swipe forward for the next lesson"
            return card

        lang = course_pkg.LANG_NAMES.get(self.lang, "the language")
        shown = self.show_target() and not step.hide_text
        reading_ok = self.show_reading(step)
        kind = step.kind

        def full(cue: str) -> None:
            card.update(cue=cue, target=step.text,
                        reading=step.reading if reading_ok else "", english=step.en)

        if kind == "info":
            card.update(cue="", target=step.en or step.text or step.note)
        elif kind == "listen":
            full("Listen")
        elif kind == "speak":
            full("Say it")
        elif kind == "recall":
            if shown:
                full("Say it")
                card["english"] = step.en or step.prompt_en
            else:
                card.update(cue=f"Say it in {lang}", target=step.prompt_en or step.en)
        elif kind == "read":
            n = f" · {step.chunk_index}/{step.chunk_total}" if step.chunk_total else ""
            full("Read aloud" + n)
        elif kind == "answer":
            full(f"Answer in {lang}")
            if self.show_sample() and step.sample_text:
                card["footer"] = "e.g. " + step.sample_text
        elif kind == "write":
            full("Say it shorter")
        elif kind == "hear":
            card.update(cue="Listen", target=step.note or "Nothing on screen - just listen")
        elif kind in ("kana", "kanji", "hanzi"):
            full({"kana": "Kana", "kanji": "Kanji", "hanzi": "Character"}[kind])
            if not card["reading"] and step.reading:
                card["reading"] = step.reading      # a character is taught with its sound
        else:
            full("")

        if not card["footer"]:
            score = self.last_score or {}
            if self.attempts and score and not score.get("passed"):
                reasons = score.get("reasons") or []
                card["footer"] = "Try again" + (f" - {reasons[0]}" if reasons else "")
            elif self.last_line and self.last_line.get("text") != step.text:
                ll = self.last_line
                card["footer"] = "✓ " + " · ".join(
                    x for x in (ll["text"], ll["reading"], ll["en"]) if x)
        return card
