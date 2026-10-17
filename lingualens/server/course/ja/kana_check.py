# -*- coding: utf-8 -*-
"""Japanese data check — the kana counterpart of `zh/pinyin_check.py`.

`text` is what Japanese write (kanji + kana). `reading` is the same line
written entirely in kana: the furigana slot printed above the line in the
glasses display. A single kanji that leaks into a `reading` field is garbage
exactly where the learner is looking for help, so the corpus is machine-checked
rather than trusted.

What it catches:
  * kanji (or stray latin) in a `reading` field
  * katakana loanwords in `text` that did not survive into the `reading`
  * hiragana-only `text` whose `reading` disagrees with it
  * duplicate lesson ids, duplicate vocab words inside a topic
  * a lesson with no "them" turn or no "you" turn (you cannot have a
    conversation with only one side of it)

What it deliberately does NOT do: guess whether a kanji reading is *correct*.
That needs a dictionary; this checks structure, which is what typos break.

    python -m server.course.ja.kana_check
"""
from __future__ import annotations

import re
import sys
from typing import Dict, Iterable, List, Tuple

sys.path.insert(0, ".")

from server.curriculum import Course  # noqa: E402

# --- character classes ------------------------------------------------------
HIRAGANA = r"\u3040-\u309f"
KATAKANA = r"\u30a0-\u30ff"
KANJI = (
    r"\u4e00-\u9fff"      # CJK unified
    r"\u3400-\u4dbf"      # extension A
    r"\u3005\u3006\u3007"  # 々 〆 〇
    r"\u2e80-\u2eff"      # radicals supplement
    r"\uf900-\ufaff"      # compatibility ideographs
)
# punctuation and digits are legitimate in a reading; latin letters are not
# (a romaji leak means somebody pasted the wrong column)
ALLOWED_IN_READING = r"\s\u3000-\u303f\uff01-\uff60\u2010-\u203b0-9０-９\u30fc\u30fb"
RE_KANJI = re.compile(f"[{KANJI}]")
RE_KATAKANA = re.compile(f"[{KATAKANA}]")
RE_BAD_IN_READING = re.compile(f"[^{HIRAGANA}{KATAKANA}{ALLOWED_IN_READING}]")
RE_STRIP = re.compile(f"[^{HIRAGANA}{KATAKANA}0-9]")


def strip_punct(s: str) -> str:
    """Everything kana-ish, so こんにちは。 and こんにちは compare equal."""
    return RE_STRIP.sub("", s or "")


def _body(s: str) -> str:
    return (s or "").replace("{x}", "")


def _counts(s: str) -> Tuple[int, int]:
    """(kanji, kana) in one field, ignoring punctuation and the drill slot."""
    body = _body(s)
    return len(RE_KANJI.findall(body)), len(re.findall(f"[{HIRAGANA}{KATAKANA}]", body))


def problems_in_reading(text: str, reading: str) -> List[str]:
    """Structural problems with one (text, reading) pair."""
    issues: List[str] = []
    reading = reading or ""
    text = text or ""

    # strip the drill slot before scanning: "{x}" is a placeholder, not a typo
    probe = reading.replace("{x}", "")

    kanji = sorted(set(RE_KANJI.findall(probe)))
    if kanji:
        issues.append(f"reading has kanji: {''.join(kanji)}")
    junk = sorted(set(RE_BAD_IN_READING.findall(probe)))
    if junk:
        issues.append(f"reading has non-kana: {''.join(junk)}")
    if not probe.strip():
        issues.append("reading is empty")

    # every character of the line must be accounted for by at least one kana:
    # this is what catches dropped okurigana and truncated readings
    t_kanji, t_kana = _counts(text)
    _r_kanji, r_kana = _counts(reading)
    if t_kanji + t_kana and r_kana < t_kanji + t_kana:
        issues.append(
            f"reading too short: {t_kanji + t_kana} characters in text, {r_kana} kana"
        )

    # a katakana loanword must appear verbatim in the kana line
    katakana_runs = [r for r in RE_KATAKANA.findall(text.replace("{x}", ""))]
    if katakana_runs:
        loan = "".join(katakana_runs)
        if loan not in probe:
            issues.append(f"katakana {loan} missing from reading")

    # a purely-kana line is its own reading
    if text and not RE_KANJI.search(text) and not katakana_runs:
        if strip_punct(text) and strip_punct(text) != strip_punct(reading):
            issues.append(f"kana text {text} != reading {reading}")
    return issues


def check_pairs(pairs: Iterable[Tuple[str, str, str]], where: str) -> List[str]:
    issues: List[str] = []
    for text, reading, _gloss in pairs:
        for problem in problems_in_reading(text, reading):
            issues.append(f"{where}: {text} -> {reading}  ({problem})")
    return issues


def check_course(c: Course) -> List[str]:
    issues: List[str] = []
    seen_ids: Dict[int, str] = {}

    for lesson in c.lessons.values():
        if lesson.id in seen_ids:
            issues.append(f"lesson {lesson.id}: duplicate id")
        seen_ids[lesson.id] = lesson.title
        if not lesson.dialogue:
            issues.append(f"lesson {lesson.id}: no dialogue")
            continue
        speakers = {t.speaker for t in lesson.dialogue}
        if "them" not in speakers:
            issues.append(f"lesson {lesson.id}: no listening turn")
        if "you" not in speakers:
            issues.append(f"lesson {lesson.id}: nothing for the learner to say")
        issues += check_pairs(
            ((v.text, v.reading, v.en) for v in lesson.vocab), f"lesson {lesson.id} vocab"
        )
        issues += check_pairs(
            ((t.text, t.reading, t.en) for t in lesson.dialogue), f"lesson {lesson.id} dialogue"
        )
        for pattern in getattr(lesson, "patterns", []) or []:
            # DrillPattern / Phrase are objects, not the raw dicts the data
            # files are written with.  {x} is dropped from both sides: it is a
            # slot marker, not part of the line.
            issues += check_pairs(
                [
                    (
                        pattern.text.replace("{x}", ""),
                        pattern.reading.replace("{x}", ""),
                        pattern.en,
                    ),
                ],
                f"lesson {lesson.id} pattern",
            )
            issues += check_pairs(
                ((v.text, v.reading, v.en) for v in pattern.values or []),
                f"lesson {lesson.id} pattern values",
            )

    seen_words: Dict[str, str] = {}
    for topic in c.topics.values():
        for w in topic.words:
            if w.text in seen_words:
                issues.append(f"vocab {topic.id}: duplicate word {w.text} (also {seen_words[w.text]})")
            seen_words[w.text] = topic.id
        issues += check_pairs(
            ((w.text, w.reading, w.en) for w in topic.words), f"vocab {topic.id}"
        )

    for lesson_id, prompts in (getattr(c, "_prompts", None) or {}).items():
        for q_text, q_reading, q_en, a_text, a_reading, a_en in prompts:
            issues += check_pairs(
                [(q_text, q_reading, q_en), (a_text, a_reading, a_en)],
                f"prompt {lesson_id}",
            )
    return issues


if __name__ == "__main__":
    c = Course("ja")
    problems = check_course(c)
    print(
        f"language={c.lang} lessons={len(c.lesson_ids)} "
        f"vocab={c.vocab_count()} prompts={c.prompt_count()}"
    )
    if not problems:
        print("kana OK")
    for p in problems:
        print(" ", p)
    print(f"{len(problems)} issue(s)")
