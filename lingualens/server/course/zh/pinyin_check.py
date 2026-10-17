# -*- coding: utf-8 -*-
"""Pinyin validator.

We hand-write pinyin for ~1,200 vocabulary items, 73 lessons and 146 free
prompts. Tone marks are easy to get wrong and a wrong tone is a wrong word, so
every syllable is checked against the table of legal Mandarin syllables.

    python -m server.course.zh.pinyin_check
"""
from __future__ import annotations

import re
import unicodedata
from typing import Dict, Iterable, List, Tuple

TONED = "āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü"
_TONE_MAP = {
    "ā": "a", "á": "a", "ǎ": "a", "à": "a",
    "ē": "e", "é": "e", "ě": "e", "è": "e",
    "ī": "i", "í": "i", "ǐ": "i", "ì": "i",
    "ō": "o", "ó": "o", "ǒ": "o", "ò": "o",
    "ū": "u", "ú": "u", "ǔ": "u", "ù": "u",
    "ǖ": "ü", "ǘ": "ü", "ǚ": "ü", "ǜ": "ü", "ü": "ü",
}

INITIALS: Dict[str, List[str]] = {
    "": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "er", "o", "ou"],
    "b": ["a", "ai", "an", "ang", "ao", "ei", "en", "eng", "i", "ian", "iao",
          "ie", "in", "ing", "o", "u"],
    "p": ["a", "ai", "an", "ang", "ao", "ei", "en", "eng", "i", "ian", "iao",
          "ie", "in", "ing", "o", "ou", "u"],
    "m": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ian",
          "iao", "ie", "in", "ing", "o", "ou", "u"],
    "f": ["a", "an", "ang", "ei", "en", "eng", "o", "ou", "u"],
    "d": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ian",
          "iao", "ie", "ing", "iu", "ong", "ou", "u", "uan", "ui", "un", "uo"],
    "t": ["a", "ai", "an", "ang", "ao", "e", "eng", "i", "ian", "iao", "ie",
          "ing", "ong", "ou", "u", "uan", "ui", "un", "uo"],
    "n": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ian",
          "iang", "iao", "ie", "in", "ing", "iu", "ong", "ou", "u", "uan",
          "un", "uo", "ü", "üe"],
    "l": ["a", "ai", "an", "ang", "ao", "e", "ei", "eng", "i", "ia", "ian",
          "iang", "iao", "ie", "in", "ing", "iu", "o", "ong", "ou", "u",
          "uan", "un", "uo", "ü", "üe"],
    "g": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "ong", "ou",
          "u", "ua", "uai", "uan", "uang", "ui", "un", "uo"],
    "k": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "ong", "ou",
          "u", "ua", "uai", "uan", "uang", "ui", "un", "uo"],
    "h": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "ong", "ou",
          "u", "ua", "uai", "uan", "uang", "ui", "un", "uo"],
    # ju/qu/xu are written with u but are really ü
    "j": ["i", "ia", "ian", "iang", "iao", "ie", "in", "ing", "iong", "iu",
          "u", "uan", "ue", "un", "ü", "üe", "ün"],
    "q": ["i", "ia", "ian", "iang", "iao", "ie", "in", "ing", "iong", "iu",
          "u", "uan", "ue", "un", "ü", "üe", "ün"],
    "x": ["i", "ia", "ian", "iang", "iao", "ie", "in", "ing", "iong", "iu",
          "u", "uan", "ue", "un", "ü", "üe", "ün"],
    "zh": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ong",
           "ou", "u", "ua", "uai", "uan", "uang", "ui", "un", "uo"],
    "ch": ["a", "ai", "an", "ang", "ao", "e", "en", "eng", "i", "ong", "ou",
           "u", "ua", "uai", "uan", "uang", "ui", "un", "uo"],
    "sh": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ou",
           "u", "ua", "uai", "uan", "uang", "ui", "un", "uo"],
    "r": ["an", "ang", "ao", "e", "en", "eng", "i", "ong", "ou", "u", "ua",
          "uai", "uan", "uang", "ui", "un", "uo"],
    "z": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ong",
          "ou", "u", "uan", "ui", "un", "uo"],
    "c": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ong",
          "ou", "u", "uan", "ui", "un", "uo"],
    "s": ["a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "i", "ong",
          "ou", "u", "uan", "ui", "un", "uo"],
    "y": ["a", "an", "ang", "ao", "e", "i", "in", "ing", "o", "ong", "ou",
          "u", "uan", "ue", "un"],
    "w": ["a", "ai", "an", "ang", "ei", "en", "eng", "o", "u"],
}

_SYLLABLES = {
    initial + final for initial, finals in INITIALS.items() for final in finals
}
_FINALS = {final for finals in INITIALS.values() for final in finals}
_FINALS_BY_INITIAL = {initial: set(finals) for initial, finals in INITIALS.items()}
# bare interjections - legal on their own, never inside a longer word
_EXTRA = {"n", "ng", "m", "hm", "hng", "ê", "yo", "lo", "êi"}

_INITIAL_ORDER = sorted(
    ("zh", "ch", "sh", "b", "p", "m", "f", "d", "t", "n", "l", "g", "k", "h",
     "j", "q", "x", "r", "z", "c", "s", "y", "w"),
    key=len,
    reverse=True,
)


def untone(text: str) -> str:
    out = []
    for ch in unicodedata.normalize("NFC", text or ""):
        out.append(_TONE_MAP.get(ch, ch))
    return "".join(out)


def syllables(pinyin: str) -> List[str]:
    raw = untone(pinyin or "").lower()
    raw = raw.replace("'", " ")
    raw = re.sub(r"[^a-zü\s]", " ", raw)
    return [t for t in raw.split() if t]


def _is_erhua(token: str) -> bool:
    """nǎr (哪儿) is one syllable for two characters - but ér is not erhua."""
    return (
        len(token) > 2
        and token.endswith("r")
        and token not in _SYLLABLES
        and valid_syllable(token[:-1], bare=False)
    )


def valid_syllable(token: str, bare: bool = True) -> bool:
    if bare and token in _EXTRA:
        return True
    if token in _SYLLABLES:
        return True
    for initial in _INITIAL_ORDER:
        final = token[len(initial):]
        if token.startswith(initial) and final in _FINALS_BY_INITIAL[initial]:
            return True
    return False


def _dp(text: str, allow_erhua: bool) -> Optional[List[str]]:
    n = len(text)
    best: List[Optional[List[str]]] = [None] * (n + 1)
    best[0] = []
    for i in range(n):
        if best[i] is None:
            continue
        for j in range(min(i + 7, n), i, -1):  # longest match first
            token = text[i:j]
            if allow_erhua and _is_erhua(token):
                if best[j] is None:
                    best[j] = best[i] + [token]
                continue
            if not valid_syllable(token, bare=False):
                continue
            if best[j] is None:
                best[j] = best[i] + [token]
    return best[n]


def _segment_one(text: str) -> Optional[List[str]]:
    """Split one space-free run of pinyin into legal syllables.

    Erhua (nàr = 哪儿) is only accepted when nothing else parses, otherwise
    fǎnér would happily split as fa + ner.
    """
    if text in _EXTRA:
        return [text]
    return _dp(text, allow_erhua=False) or _dp(text, allow_erhua=True)


def segment(pinyin: str) -> Optional[List[str]]:
    """Split a pinyin string into legal syllables, or None if impossible.

    wǒmen -> ["wo", "men"];  yígài'érlùn -> ["yi", "gai", "er", "lun"]
    """
    out: List[str] = []
    for token in syllables(pinyin):
        parts = _segment_one(token)
        if parts is None:
            return None
        out.extend(parts)
    return out


def check_pairs(pairs: Iterable[Tuple[str, str, str]], where: str) -> List[str]:
    """pairs: (hanzi, pinyin, gloss). Returns human-readable problems."""
    issues: List[str] = []
    for hanzi, pinyin, _gloss in pairs:
        parts = segment(pinyin)
        n_hz = len(re.sub(r"[^\u4e00-\u9fff]", "", hanzi or ""))
        if parts is None:
            issues.append(f"{where}: {hanzi} -> {pinyin}  (cannot parse)")
            continue
        # erhua: 哪儿 nǎr is one syllable standing for two characters
        n_py = len(parts) + sum(1 for p in parts if _is_erhua(p))
        if n_hz and parts and n_py != n_hz:
            issues.append(
                f"{where}: {hanzi} -> {pinyin}  ({n_hz} chars vs {n_py} syllables)"
            )
    return issues


def check_course(course) -> List[str]:
    issues: List[str] = []
    seen: Dict[str, str] = {}
    for level in course.levels:
        for topic in level.vocab_topics:
            issues += check_pairs(
                ((w.text, w.reading, w.en) for w in topic.words), f"vocab {topic.id}"
            )
            for w in topic.words:
                if w.text in seen:
                    issues.append(f"vocab {topic.id}: duplicate word {w.text} (also {seen[w.text]})")
                seen[w.text] = topic.id
    for lesson in course.lessons.values():
        issues += check_pairs(
            ((v.text, v.reading, v.en) for v in lesson.vocab), f"lesson {lesson.id} vocab"
        )
        issues += check_pairs(
            ((t.text, t.reading, t.en) for t in lesson.dialogue), f"lesson {lesson.id} dialogue"
        )
        # Drill frames were never checked at all.  {x} is dropped from both
        # sides: it is a slot marker, and a bare "x" cannot be segmented as a
        # syllable, so leaving it in would make every frame unparseable.
        for pattern in getattr(lesson, "patterns", []) or []:
            issues += check_pairs(
                [
                    (
                        pattern.text.replace("{x}", ""),
                        pattern.reading.replace("{x}", ""),
                        pattern.en,
                    )
                ],
                f"lesson {lesson.id} pattern",
            )
            issues += check_pairs(
                ((v.text, v.reading, v.en) for v in pattern.values or []),
                f"lesson {lesson.id} pattern values",
            )
        for p in lesson.prompts:
            issues += check_pairs(
                [(p.q_text, p.q_reading, p.q_en), (p.a_text, p.a_reading, p.a_en)],
                f"lesson {lesson.id} free",
            )
    return issues


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from server.curriculum import Course

    c = Course("zh")
    problems = check_course(c)
    print(f"language={c.lang} lessons={len(c.lesson_ids)} vocab={c.vocab_count()} prompts={c.prompt_count()}")
    if not problems:
        print("pinyin OK")
    for p in problems:
        print(" ", p)
    print(f"{len(problems)} issue(s)")
