# -*- coding: utf-8 -*-
"""A grammar reference, one page per lesson.

The course has always had `notes` - good, short, and about one and a half
per lesson. That is enough to explain the joke in a line and not enough to
explain the grammar the line is built on. A learner who meets 〜てしまう
three times in three lessons, each time with a one-line gloss, has three
half-ideas and no way to find any of them again.

This module is the other half: a page per lesson, always in the same
place, that states the point, gives the formula, and shows it twice.

The contract
------------
    GRAMMAR[lesson_id] = [
        {
            "point":    "〜てしまう",
            "en":       "finish completely, or regret",
            "formula":  "V-て + しまう",
            "examples": [
                ("宿題を忘れてしまいました。", "しゅくだいをわすれてしまいました。",
                 "I went and forgot the homework."),
            ],
            "contrast": "〜ておく is doing it in advance on purpose; "
                        "〜てしまう is it happening, often regretted.",
            "watch":    "In speech it collapses to 〜ちゃう / 〜てまう.",
        },
        …
    ]

Rules:

1. `point` is the Japanese name of the thing, exactly as a learner would
   look it up. `en` is one line. `formula` is the shape to fill in.
2. Two or three `examples`, each (text, reading, en). The reading is the
   line written entirely in kana - the same rule the rest of the course
   follows.
3. `contrast` is the part that actually teaches: the thing this gets
   confused with, and how to tell them apart. Omit it if there is genuinely
   nothing to confuse it with.
4. `watch` is for the exception, the spoken contraction, or the place the
   rule stops holding. Optional.
5. Two to four entries per lesson. Not more: a page you have to scroll is
   a page you do not read twice.
6. Nothing here invents grammar the lesson does not use. If the lesson's
   dialogue and patterns never touch 〜ば, do not write 〜ば.

Entries are keyed by lesson id; a lesson with no entry simply has no page.
"""

if not __package__:  # run directly as a script: no package context
    import os as _os
    import sys as _sys

    _sys.path.insert(0, _os.path.abspath(
        _os.path.join(_os.path.dirname(__file__), "..", "..", "..")))
    from server.course.ja import _parts
else:
    from . import _parts

GRAMMAR: dict = {}

# grammar_c is a fallback for lessons 1-36, the beginner half. It loads last
# and `setdefault` means it only fills what is missing, so if grammar_a is
# ever written it wins automatically and this silently contributes nothing.
# That beats blocking the most important half of the reference on one author.
_PART_A, _PART_B, _PART_C = _parts.load_parts(
    ("grammar_a", "grammar_b", "grammar_c"), "GRAMMAR"
)
_PARTS = (_PART_A, _PART_B, _PART_C)

for _part in _PARTS:
    for _lesson_id, _rows in (_part or {}).items():
        GRAMMAR.setdefault(int(_lesson_id), _rows)


def for_lesson(lesson_id: int) -> list:
    """The grammar page for one lesson, or an empty list."""
    return list(GRAMMAR.get(int(lesson_id)) or [])


def check() -> list:
    """Mechanical rules above, so the pages cannot quietly rot."""
    import re

    kanji = re.compile(r"[一-鿿]")
    problems = []

    # `problems_in_reading` catches what a kanji-only test misses: a dropped
    # okurigana, a Latin character, a reading shorter than the text it
    # belongs to. It lives in kana_check, which pulls in the whole
    # curriculum, so it is imported here rather than at module scope -
    # `grammar` sits on the app's import path and must not drag that in.
    try:
        from .kana_check import problems_in_reading  # type: ignore
    except ImportError:
        try:
            from server.course.ja.kana_check import problems_in_reading  # type: ignore
        except ImportError:
            problems_in_reading = None

    def page_problems(where: str, rows: list) -> list:
        out = []
        if not rows:
            return [f"{where}: empty grammar page"]
        if len(rows) > 4:
            out.append(f"{where}: {len(rows)} entries, keep it to four")
        for n, row in enumerate(rows, 1):
            for key in ("point", "en", "formula", "examples"):
                if key not in row:
                    out.append(f"{where} entry {n}: missing {key}")
            if not row.get("examples"):
                out.append(f"{where} entry {n}: no examples")
                continue
            if len(row["examples"]) < 2:
                out.append(f"{where} entry {n}: give at least two examples")
            for ex in row["examples"]:
                if len(ex) != 3:
                    out.append(f"{where} entry {n}: example needs (text, reading, en)")
                    continue
                text, reading, en = ex
                if not (text and reading and en):
                    out.append(f"{where} entry {n}: empty string in {ex}")
                if kanji.search(reading):
                    out.append(f"{where} entry {n}: reading still has kanji: {reading}")
                if problems_in_reading is not None:
                    for msg in problems_in_reading(text, reading):
                        out.append(f"{where} entry {n}: {msg}")
        return out

    problems = []
    for lesson_id, rows in sorted(GRAMMAR.items()):
        problems += page_problems(f"lesson {lesson_id}", rows)

    # The merge keeps one page per lesson, so a page that lost the `setdefault`
    # race is never validated - and it is exactly the page that goes live if
    # the part that won ever fails to import or is deleted. grammar_c carries
    # lessons 1-36 but only 13-36 are effective, so its beginner half would
    # otherwise ship unverified. Check the shadowed pages too.
    for name, part in zip(("grammar_a", "grammar_b", "grammar_c"), _PARTS):
        for lesson_id, rows in sorted((part or {}).items()):
            if GRAMMAR.get(int(lesson_id)) is rows:
                continue  # this is the page that won; already checked above
            problems += page_problems(
                f"{name} lesson {lesson_id} (shadowed, not live)", rows)
    return problems


def stats() -> dict:
    entries = sum(len(v) for v in GRAMMAR.values())
    examples = sum(len(e.get("examples", [])) for v in GRAMMAR.values() for e in v)
    return {"pages": len(GRAMMAR), "entries": entries, "examples": examples,
            "lessons_without": 73 - len(GRAMMAR)}


if __name__ == "__main__":
    print(stats())
    print("parts:", _parts.LOADED)
    found = check()
    found += [f"part {n} exists but loaded nothing" for n in
              _parts.dead_parts(("grammar_a", "grammar_b", "grammar_c"))]
    print(f"{len(found)} problem(s)")
    for p in found:
        print("  " + p)
