# -*- coding: utf-8 -*-
"""Graded reading: the only place in the course where Japanese arrives in
paragraphs.

Everything else a learner meets is one line long. That is right for
teaching a line and useless for learning to read: real text has pronouns
that point three sentences back, connectors that carry the argument, and
paragraphs where the topic is never quite stated. A course that only ever
shows sentences produces someone who can decode a sentence and cannot
follow a page.

So each lesson gets a passage, and the passage is:

  * **graded** - it uses the vocabulary and grammar of that lesson and
    earlier. Nothing in it is new except the odd word, and those are there
    on purpose, because reading is where you are supposed to meet a word
    you half-know and work it out.
  * **chunked** - a passage is a list of sentences, each short enough to be
    read aloud and graded as one utterance. Keep a chunk under ~45
    characters: the gate allows 15 seconds of audio and Japanese runs
    roughly six characters a second.
  * **checked** - one or two questions afterwards, so reading is not
    decoding-and-forgetting. The question must be answerable from the text.

The contract
------------
    PASSAGES[lesson_id] = {
        "title":     "はじめまして",
        "title_en":  "How do you do",
        "chunks": [
            ("Japanese sentence.", "かな sentence.", "English."),
            ...
        ],
        "questions": [
            {"q": "...", "q_en": "...", "a": "...", "a_en": "...",
             "keywords": ["...", "..."], "min_chars": 6},
        ],
    }

Rules that keep the data honest - `check()` enforces the mechanical ones:

1. Every chunk has all three strings, and the reading is the same line
   written entirely in kana. No kanji, no Latin, no digits: that is what
   `kana_check.py` demands everywhere else in the course, and there is no
   reason to hold the passages to a lower bar.
2. A passage uses the kanji the course has already taught and no others.
   Lessons 1-3 are almost entirely kana for this reason: the syllabary is
   still being drilled. By N3 the passage reads like real text.
3. `keywords` are strings that genuinely appear in the model answer, so
   the grader can tell "I read it" from "I said something".
4. `min_chars` is about a third of the model answer; it stops 「はい」
   counting as an answer.
5. Chunks are one sentence each, and the passage as a whole hangs
   together - four unrelated sentences is a word list, not a text.

Passages are keyed by lesson id. A lesson with no entry simply gets no
reading step, so a partial table is fine.
"""

if not __package__:  # run directly as a script: no package context
    import os as _os
    import sys as _sys

    _sys.path.insert(0, _os.path.abspath(
        _os.path.join(_os.path.dirname(__file__), "..", "..", "..")))
    from server.course.ja import _parts
else:
    from . import _parts

PASSAGES: dict = {
    1: {
        "title": "あいさつ",
        "title_en": "Greetings",
        "chunks": [
            (
                "たなかさんはまいあさ、「おはようございます」といいます。",
                "たなかさんはまいあさ、「おはようございます」といいます。",
                "Every morning Tanaka says good morning.",
            ),
            (
                "ひるは「こんにちは」、よるは「こんばんは」をつかいます。",
                "ひるは「こんにちは」、よるは「こんばんは」をつかいます。",
                "At midday he uses 'konnichiwa', in the evening 'konbanwa'.",
            ),
            (
                "「ありがとう」といわれたら、「どういたしまして」とこたえます。",
                "「ありがとう」といわれたら、「どういたしまして」とこたえます。",
                "When someone thanks him, he answers 'you're welcome'.",
            ),
            (
                "かえるときは、「さようなら。またね」といいます。",
                "かえるときは、「さようなら。またね」といいます。",
                "When he leaves he says goodbye, and 'see you'.",
            ),
        ],
        "questions": [
            {
                "q": "たなかさんはよる、なんといいますか。",
                "q_en": "What does Tanaka say in the evening?",
                "a": "「こんばんは」といいます。",
                "a_en": "He says 'konbanwa'.",
                "keywords": ["こんばんは"],
                "min_chars": 6,
            },
        ],
    },
    2: {
        "title": "みせで",
        "title_en": "At the shop",
        "chunks": [
            (
                "みせで「おねがいします」といって、パンをかいます。",
                "みせで「おねがいします」といって、パンをかいます。",
                "At the shop he says 'one, please' and buys bread.",
            ),
            (
                "まちがえたときは、「すみません」と「ごめんなさい」をつかいます。",
                "まちがえたときは、「すみません」と「ごめんなさい」をつかいます。",
                "When he gets it wrong he uses 'sumimasen' and 'gomennasai'.",
            ),
            (
                "「おそくなりました」というと、みんな「だいじょうぶですよ」とこたえます。",
                "「おそくなりました」というと、みんな「だいじょうぶですよ」とこたえます。",
                "When he says he is late, everyone answers that it is fine.",
            ),
            (
                "ともだちが「どうぞ」といって、おちゃをだしてくれました。",
                "ともだちが「どうぞ」といって、おちゃをだしてくれました。",
                "A friend said 'here you are' and poured the tea.",
            ),
        ],
        "questions": [
            {
                "q": "おそくなったとき、なんといいますか。",
                "q_en": "What do you say when you are late?",
                "a": "「すみません、おそくなりました」といいます。",
                "a_en": "You say 'sorry I'm late'.",
                "keywords": ["すみません", "おそく"],
                "min_chars": 8,
            },
        ],
    },
    3: {
        "title": "わからないとき",
        "title_en": "When you don't understand",
        "chunks": [
            (
                "日本語がわかりますかと、よくきかれます。",
                "にほんごがわかりますかと、よくきかれます。",
                "I am often asked whether I understand Japanese.",
            ),
            (
                "わからないときは、「すみません、よく分かりません」といいます。",
                "わからないときは、「すみません、よくわかりません」といいます。",
                "When I don't understand I say sorry, I don't really follow.",
            ),
            (
                "「もう一度、ゆっくりいってください」とたのむと、わかりやすくなります。",
                "「もういちど、ゆっくりいってください」とたのむと、わかりやすくなります。",
                "If I ask them to say it once more, slowly, it becomes easier.",
            ),
            (
                "日本語はまだむずかしいですが、英語なら少しわかります。",
                "にほんごはまだむずかしいですが、えいごならすこしわかります。",
                "Japanese is still hard, but if it is English I follow a little.",
            ),
        ],
        "questions": [
            {
                "q": "わからないとき、なんといってたのみますか。",
                "q_en": "When you don't understand, what do you say to ask for help?",
                "a": "「もう一度、ゆっくり言ってください」と頼みます。",
                "a_en": "You ask them to say it once more, slowly.",
                "keywords": ["もう一度", "ゆっくり"],
                "min_chars": 8,
            },
        ],
    },
}


# The table is built in parts so that several people can write passages at
# once without colliding. Each part is a plain PASSAGES-shaped dict; lessons
# already defined here (1-3, the worked examples) win.
_PART_A, _PART_B, _PART_C = _parts.load_parts(
    ("readings_a", "readings_b", "readings_c"), "PASSAGES"
)

for _part in (_PART_A, _PART_B, _PART_C):
    for _lesson_id, _passage in (_part or {}).items():
        PASSAGES.setdefault(int(_lesson_id), _passage)


def get(lesson_id: int) -> dict:
    """The passage for one lesson, or {} if there isn't one yet."""
    return PASSAGES.get(int(lesson_id)) or {}


def check() -> list:
    """Every mechanical rule above, so the data cannot quietly rot.

    Returns a list of human-readable problems; an empty list means the
    table is sound. Run it the same way you run kana_check.py.
    """
    import re

    problems = []
    latin = re.compile(r"[A-Za-z0-9]")
    kanji = re.compile(r"[一-鿿]")

    for lesson_id, passage in sorted(PASSAGES.items()):
        where = f"lesson {lesson_id}"
        for key in ("title", "title_en", "chunks", "questions"):
            if key not in passage:
                problems.append(f"{where}: missing {key}")
        if not passage.get("chunks"):
            problems.append(f"{where}: no chunks")
            continue
        if not passage.get("questions"):
            problems.append(f"{where}: no questions")
        for n, chunk in enumerate(passage["chunks"], 1):
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
            if kanji.search(reading):
                problems.append(f"{where} chunk {n}: reading still has kanji: {reading}")
            if latin.search(reading):
                problems.append(f"{where} chunk {n}: reading has latin or digits: {reading}")
            # the kana reading should cover the same ground as the text
            stripped = kanji.sub("", text)
            if reading and stripped and len(reading) < len(stripped) * 0.9:
                problems.append(
                    f"{where} chunk {n}: reading looks short for the text: {reading}"
                )
        for n, q in enumerate(passage.get("questions", []), 1):
            for key in ("q", "q_en", "a", "a_en", "keywords", "min_chars"):
                if key not in q:
                    problems.append(f"{where} question {n}: missing {key}")
            for kw in q.get("keywords", []):
                if kw not in q.get("a", ""):
                    problems.append(
                        f"{where} question {n}: keyword {kw!r} is not in the answer"
                    )
            if q.get("min_chars", 0) and q["min_chars"] > len(q.get("a", "")):
                problems.append(f"{where} question {n}: min_chars exceeds the answer")
    return problems


def stats() -> dict:
    chunks = sum(len(p["chunks"]) for p in PASSAGES.values())
    chars = sum(len(c[0]) for p in PASSAGES.values() for c in p["chunks"])
    return {
        "passages": len(PASSAGES),
        "chunks": chunks,
        "characters": chars,
        "lessons_without": 73 - len(PASSAGES),
    }


if __name__ == "__main__":
    print(stats())
    print("parts:", _parts.LOADED)
    found = check()
    found += [f"part {n} exists but loaded nothing" for n in
              _parts.dead_parts(("readings_a", "readings_b", "readings_c"))]
    print(f"{len(found)} problem(s)")
    for p in found:
        print("  " + p)
