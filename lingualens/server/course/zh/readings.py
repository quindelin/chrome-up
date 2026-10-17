# -*- coding: utf-8 -*-
"""Graded reading: the only place in the course where Mandarin arrives in
paragraphs.

Everything else a learner meets is one line long. That is right for teaching
a line and useless for learning to read: real text has pronouns that point
three sentences back, connectors that carry the argument, and paragraphs where
the topic is never quite stated. A course that only ever shows sentences
produces someone who can decode a sentence and cannot follow a page.

For Mandarin this gap was worse than a missing feature, because the course
also fades pinyin out from HSK 3 onwards on the reasoning that "if it is
always on you never learn to read the characters". There was nothing to read.
HSK 5-6 is largely a reading exam - 阅读 is 50 of the questions, roughly
4,500 characters to get through in 50 minutes - and a learner who has never
read a connected passage has no chance at it.

So each lesson gets a passage, and the passage is:

  * **graded** - it uses the vocabulary and grammar of that lesson and
    earlier. Nothing in it is new except the odd word, and those are there
    on purpose, because reading is where you are supposed to meet a word
    you half-know and work it out.
  * **chunked** - a passage is a list of sentences, each short enough to be
    read aloud and graded as one utterance. Keep a chunk under ~45
    characters: the gate allows 15 seconds of audio and Mandarin runs
    roughly five characters a second out loud.
  * **checked** - one question for reading, one for listening, so reading is
    not decoding-and-forgetting.

The contract
------------
    PASSAGES[lesson_id] = {
        "title":     "你好",
        "title_en":  "Hello",
        "chunks": [
            ("汉字 sentence.", "pinyin sentence.", "English."),
            ...
        ],
        "questions": [
            {"q": "...", "q_reading": "...", "q_en": "...",
             "a": "...", "a_reading": "...", "a_en": "...",
             "keywords": ["..."], "min_chars": 6},
            ...
        ],
    }

Rules that keep the data honest - `check()` enforces the mechanical ones:

1. Every chunk has all three strings, and the pinyin is the same line
   written entirely in romanisation. Every syllable in it is validated
   against the table of legal Mandarin syllables by `pinyin_check.py`, the
   same way every other reading in the course is: a wrong tone printed above
   a line is a wrong word taught.
2. A passage uses the characters the course has already taught and no
   others. In practice that means the HSK 1 passages hang almost entirely
   on course_zh.py's first units, and by HSK 5 they read like real text.
3. `questions[0]` is the READING question: answered after the learner has
   read the passage and can look at it. `questions[1]` is the LISTENING
   question, and it has to be answerable from the LAST CHUNK ALONE - that
   chunk is the one played with a blank screen (see engine._hearing_steps).
   Authoring the second question about some other part of the passage
   silently turns the listening check into a memory test.
4. `keywords` are strings that genuinely appear in the model answer, so
   the grader can tell "I read it" from "I said something".
5. `min_chars` is about a third of the model answer; it stops 好 counting
   as an answer.
6. Chunks are one or two sentences each, and the passage as a whole hangs
   together - four unrelated sentences is a word list, not a text.

Passages are keyed by lesson id. A lesson with no entry simply gets no
reading step, so a partial table is fine.

The table is split across readings_a … readings_e so several people can
write passages at once without colliding; lessons defined here win.
"""

from __future__ import annotations

import importlib

PASSAGES: dict = {
    1: {
        "title": "你好",
        "title_en": "Hello",
        "chunks": [
            (
                "你好！我叫李明。",
                "nǐ hǎo! wǒ jiào Lǐ Míng.",
                "Hello! I'm Li Ming.",
            ),
            (
                "我很好，谢谢你。你呢？",
                "wǒ hěn hǎo, xièxie nǐ. nǐ ne?",
                "I'm very well, thank you. And you?",
            ),
            (
                "我也很好。再见，明天见！",
                "wǒ yě hěn hǎo. zàijiàn, míngtiān jiàn!",
                "I'm very well too. Goodbye, see you tomorrow!",
            ),
        ],
        "questions": [
            {
                "q": "他叫什么名字？",
                "q_reading": "tā jiào shénme míngzi?",
                "q_en": "What is his name?",
                "a": "他叫李明。",
                "a_reading": "tā jiào Lǐ Míng.",
                "a_en": "He is called Li Ming.",
                "keywords": ["李明"],
                "min_chars": 4,
            },
            {
                "q": "他们什么时候见？",
                "q_reading": "tāmen shénme shíhou jiàn?",
                "q_en": "When are they meeting?",
                "a": "他们明天见。",
                "a_reading": "tāmen míngtiān jiàn.",
                "a_en": "They are meeting tomorrow.",
                "keywords": ["明天"],
                "min_chars": 4,
            },
        ],
    },
    2: {
        "title": "对不起",
        "title_en": "Sorry",
        "chunks": [
            (
                "请进，请坐。",
                "qǐng jìn, qǐng zuò.",
                "Please come in, please sit down.",
            ),
            (
                "对不起，我迟到了。",
                "duìbuqǐ, wǒ chídào le.",
                "Sorry, I'm late.",
            ),
            (
                "没关系，我们等你。谢谢你。",
                "méi guānxi, wǒmen děng nǐ. xièxie nǐ.",
                "It's nothing, we'll wait for you. Thank you.",
            ),
        ],
        "questions": [
            {
                "q": "他为什么道歉？",
                "q_reading": "tā wèishénme dàoqiàn?",
                "q_en": "Why is he apologising?",
                "a": "因为他迟到了。",
                "a_reading": "yīnwèi tā chídào le.",
                "a_en": "Because he is late.",
                "keywords": ["迟到"],
                "min_chars": 5,
            },
            {
                "q": "别人说谢谢，你怎么回答？",
                "q_reading": "biérén shuō xièxie, nǐ zěnme huídá?",
                "q_en": "Someone says thank you - how do you answer?",
                "a": "我说不客气。",
                "a_reading": "wǒ shuō bú kèqi.",
                "a_en": "I say you're welcome.",
                "keywords": ["不客气"],
                "min_chars": 4,
            },
        ],
    },
    3: {
        "title": "我不懂",
        "title_en": "I don't understand",
        "chunks": [
            (
                "你好！你会说中文吗？",
                "nǐ hǎo! nǐ huì shuō Zhōngwén ma?",
                "Hello! Do you speak Chinese?",
            ),
            (
                "我会说一点点。请慢一点。",
                "wǒ huì shuō yìdiǎndiǎn. qǐng màn yìdiǎn.",
                "I speak a little. Please speak more slowly.",
            ),
            (
                "对不起，我不懂。请再说一遍。",
                "duìbuqǐ, wǒ bù dǒng. qǐng zài shuō yí biàn.",
                "Sorry, I don't understand. Please say it again.",
            ),
        ],
        "questions": [
            {
                "q": "他会说中文吗？",
                "q_reading": "tā huì shuō Zhōngwén ma?",
                "q_en": "Can he speak Chinese?",
                "a": "他会说一点点。",
                "a_reading": "tā huì shuō yìdiǎndiǎn.",
                "a_en": "He can speak a little.",
                "keywords": ["一点点"],
                "min_chars": 4,
            },
            {
                "q": "他不懂的时候说什么？",
                "q_reading": "tā bù dǒng de shíhou shuō shénme?",
                "q_en": "What does he say when he doesn't understand?",
                "a": "他说请再说一遍。",
                "a_reading": "tā shuō qǐng zài shuō yí biàn.",
                "a_en": "He says please say it again.",
                "keywords": ["再说一遍"],
                "min_chars": 5,
            },
        ],
    },
}


# The rest of the ladder lives in parts so that several authors can work at
# once. Each part is imported on its own: a part that is still being written
# must shrink the table, not silently take the finished parts down with it -
# one `try` around the whole set used to do exactly that.
def _load_part(name: str) -> dict:
    # Only ImportError is swallowed. The old `except Exception` here also
    # caught SyntaxError, so a part with one bad comma made the whole part
    # vanish while the checker still reported clean - the same bug that
    # cost the Japanese table several hundred rows. A part that is absent
    # is fine; a part that is broken must be loud.
    try:
        module = importlib.import_module(f".{name}", __package__)
    except ImportError:
        if __package__:
            return {}
        # run as a script: no package context, so bootstrap the repo root
        import os as _os
        import sys as _sys

        root = _os.path.abspath(_os.path.join(
            _os.path.dirname(__file__), "..", "..", ".."))
        if root not in _sys.path:
            _sys.path.insert(0, root)
        try:
            module = importlib.import_module(f"server.course.zh.{name}")
        except ImportError:
            return {}
    return dict(getattr(module, "PASSAGES", {}) or {})


# name -> rows contributed, so a part that quietly loaded nothing is visible
LOADED: dict = {}
_PART_NAMES = ("readings_a", "readings_b", "readings_c", "readings_d",
               "readings_e", "readings_f")
for _name in _PART_NAMES:
    _part = _load_part(_name)
    LOADED[_name] = len(_part)
    for _lesson_id, _passage in _part.items():
        PASSAGES.setdefault(int(_lesson_id), _passage)


def dead_parts(names=_PART_NAMES) -> list:
    """Parts whose file exists on disk but contributed nothing."""
    import os as _os

    here = _os.path.dirname(_os.path.abspath(__file__))
    return [n for n in names
            if not LOADED.get(n) and _os.path.exists(_os.path.join(here, n + ".py"))]


def get(lesson_id: int) -> dict:
    """The passage for one lesson, or {} if there isn't one yet."""
    return PASSAGES.get(int(lesson_id)) or {}


def check() -> list:
    """Every mechanical rule above, so the data cannot quietly rot.

    Returns a list of human-readable problems; an empty list means the table
    is sound. Run it the same way you run pinyin_check.py.
    """
    problems = []
    for lesson_id, passage in sorted(PASSAGES.items()):
        where = f"lesson {lesson_id}"
        for key in ("title", "title_en", "chunks", "questions"):
            if key not in passage:
                problems.append(f"{where}: missing {key}")
        chunks = passage.get("chunks") or []
        if not chunks:
            problems.append(f"{where}: no chunks")
            continue
        questions = passage.get("questions") or []
        if len(questions) < 2:
            problems.append(
                f"{where}: needs 2 questions (reading + listening), has {len(questions)}"
            )
        for n, chunk in enumerate(chunks, 1):
            if len(chunk) != 3:
                problems.append(f"{where} chunk {n}: need (text, reading, en)")
                continue
            text, reading, en = chunk
            if not (text and reading and en):
                problems.append(f"{where} chunk {n}: empty string in {chunk}")
            if len(text) > 45:
                problems.append(
                    f"{where} chunk {n}: {len(text)} chars, too long to say in one breath"
                )
            # the pinyin has to cover the same number of characters as the
            # line. `check_pairs` below does this and knows about 儿化 (一会儿
            # is three characters for two syllables), so it is not repeated
            # here - a naive count would flag every erhua in the course.
        for n, q in enumerate(questions, 1):
            for key in ("q", "q_reading", "q_en", "a", "a_reading", "a_en",
                        "keywords", "min_chars"):
                if key not in q:
                    problems.append(f"{where} question {n}: missing {key}")
            for kw in q.get("keywords", []):
                if kw not in q.get("a", ""):
                    problems.append(
                        f"{where} question {n}: keyword {kw!r} is not in the answer"
                    )
            if q.get("min_chars", 0) and q["min_chars"] > len(q.get("a", "")):
                problems.append(f"{where} question {n}: min_chars exceeds the answer")

    # every reading in the course is validated against the syllable table
    try:
        from .pinyin_check import check_pairs
    except Exception:  # pragma: no cover
        return problems
    problems += check_pairs(((c[0], c[1], c[2]) for p in PASSAGES.values()
                             for c in p.get("chunks", [])), "passage chunk")
    problems += check_pairs(((q["q"], q["q_reading"], q["q_en"])
                             for p in PASSAGES.values()
                             for q in p.get("questions", [])), "passage question")
    problems += check_pairs(((q["a"], q["a_reading"], q["a_en"])
                             for p in PASSAGES.values()
                             for q in p.get("questions", [])), "passage answer")
    return problems


def stats() -> dict:
    chunks = sum(len(p["chunks"]) for p in PASSAGES.values())
    chars = sum(len(c[0]) for p in PASSAGES.values() for c in p["chunks"])
    return {
        "passages": len(PASSAGES),
        "chunks": chunks,
        "characters": chars,
        "questions": sum(len(p.get("questions", [])) for p in PASSAGES.values()),
        # with HSK 7-9 the ladder is 85 lessons; a gap here is a lesson with
        # no reading step, which is worth knowing about rather than hiding
        "lessons_without": 85 - len(PASSAGES),
    }


if __name__ == "__main__":
    print(stats())
    found = check()
    print(f"{len(found)} problem(s)")
    for p in found:
        print("  " + p)
