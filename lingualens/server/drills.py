"""Substitution drills + spaced review, for any of the course languages.

Pimsleur's real engine of repetition: one frame, many slot values
(我要__ / __在哪里 / 太__了, {x}に行きます / {x}はどこですか / {x}がすきです).
A single lesson therefore yields far more gated speaking turns than its
dialogue alone, and the review queue keeps already-learned lines coming back
forever.
"""
from __future__ import annotations

import re
import time
from typing import Dict, List

from .models import DrillPattern, Lesson, Phrase

# Frames used for lessons that do not ship their own patterns (the N5 / HSK 1-2
# foundation units).
BASE_PATTERNS: Dict[str, List[DrillPattern]] = {
    "zh": [
        DrillPattern(
            "我要{x}",
            "wǒ yào {x}",
            "I want {x}",
            [
                Phrase("咖啡", "kāfēi", "coffee"),
                Phrase("茶", "chá", "tea"),
                Phrase("水", "shuǐ", "water"),
                Phrase("啤酒", "píjiǔ", "beer"),
            ],
        ),
        DrillPattern(
            "{x}在哪里？",
            "{x} zài nǎlǐ?",
            "Where is the {x}?",
            [
                Phrase("厕所", "cèsuǒ", "restroom"),
                Phrase("地铁站", "dìtiě zhàn", "subway station"),
                Phrase("机场", "jīchǎng", "airport"),
                Phrase("酒店", "jiǔdiàn", "hotel"),
            ],
        ),
        DrillPattern(
            "{x}多少钱？",
            "{x} duōshao qián?",
            "How much is the {x}?",
            [
                Phrase("这个", "zhège", "this one"),
                Phrase("票", "piào", "ticket"),
                Phrase("咖啡", "kāfēi", "coffee"),
            ],
        ),
        DrillPattern(
            "太{x}了",
            "tài {x} le",
            "Too {x}",
            [
                Phrase("贵", "guì", "expensive"),
                Phrase("远", "yuǎn", "far"),
                Phrase("辣", "là", "spicy"),
            ],
        ),
    ],
    "ja": [
        DrillPattern(
            "{x}をください",
            "{x}をください",
            "{x}, please",
            [
                Phrase("コーヒー", "コーヒー", "coffee"),
                Phrase("お茶", "おちゃ", "tea"),
                Phrase("水", "みず", "water"),
                Phrase("ビール", "ビール", "beer"),
            ],
        ),
        DrillPattern(
            "{x}はどこですか",
            "{x}はどこですか",
            "Where is the {x}?",
            [
                Phrase("トイレ", "トイレ", "the restroom"),
                Phrase("駅", "えき", "the station"),
                Phrase("空港", "くうこう", "the airport"),
                Phrase("ホテル", "ホテル", "the hotel"),
            ],
        ),
        DrillPattern(
            "{x}はいくらですか",
            "{x}はいくらですか",
            "How much is the {x}?",
            [
                Phrase("これ", "これ", "this one"),
                Phrase("切符", "きっぷ", "the ticket"),
                Phrase("お弁当", "おべんとう", "the bento"),
            ],
        ),
        DrillPattern(
            "{x}が好きです",
            "{x}がすきです",
            "I like {x}",
            [
                Phrase("ラーメン", "ラーメン", "ramen"),
                Phrase("寿司", "すし", "sushi"),
                Phrase("音楽", "おんがく", "music"),
            ],
        ),
        DrillPattern(
            "{x}に行きます",
            "{x}にいきます",
            "I'm going to {x}",
            [
                Phrase("東京", "とうきょう", "Tokyo"),
                Phrase("駅", "えき", "the station"),
                Phrase("レストラン", "レストラン", "the restaurant"),
            ],
        ),
    ],
    # Spanish authors patterns on every lesson, so these only cover a lesson
    # that is still being written. The slot carries its own article: gender
    # agreement is the learner's job in the authored frames, not here.
    "es": [
        DrillPattern(
            "Quiero {x}, por favor.",
            "",
            "I'd like {x}, please.",
            [
                Phrase("un café", "", "a coffee"),
                Phrase("un té", "", "a tea"),
                Phrase("agua", "", "water"),
            ],
        ),
        DrillPattern(
            "¿Dónde está {x}?",
            "",
            "Where is {x}?",
            [
                Phrase("el baño", "", "the bathroom"),
                Phrase("la estación", "", "the station"),
                Phrase("el hotel", "", "the hotel"),
            ],
        ),
        DrillPattern(
            "¿Cuánto cuesta {x}?",
            "",
            "How much is {x}?",
            [
                Phrase("esto", "", "this"),
                Phrase("el billete", "", "the ticket"),
                Phrase("la camiseta", "", "the T-shirt"),
            ],
        ),
    ],
}


# What each fallback slot accepts.  Keyed by frame text so reordering the
# lists above cannot silently mis-tag a slot.
SLOT_KINDS = {
    "我要{x}": "object",
    "{x}在哪里？": "place",
    "{x}多少钱？": "object",
    "太{x}了": "adjective",
    "{x}をください": "object",
    "{x}はどこですか": "place",
    "{x}はいくらですか": "object",
    "{x}が好きです": "object",
    "{x}に行きます": "place",
    "Quiero {x}, por favor.": "es-order",
    "¿Dónde está {x}?": "es-place",
    "¿Cuánto cuesta {x}?": "es-thing",
}
for _patterns in BASE_PATTERNS.values():
    for _pattern in _patterns:
        _pattern.kind = SLOT_KINDS.get(_pattern.text, "")


def base_patterns(lang: str) -> List[DrillPattern]:
    return BASE_PATTERNS.get(lang) or BASE_PATTERNS["zh"]


def generate(lesson: Lesson, cfg: Dict, lang: str = "zh") -> List[Phrase]:
    """Expand a lesson's patterns into concrete drill lines."""
    drills_cfg = cfg.get("drills", {}) or {}
    if not drills_cfg.get("enabled", True):
        return []
    per = int(drills_cfg.get("per_pattern", 3) or 3)
    # Only the lesson's own frames. The generic BASE_PATTERNS used to fill in
    # for lessons that had none, which put 我要咖啡 / 厕所在哪里 / 太贵了 into
    # HSK 1 lesson 1 - words the learner had never heard - and asked for them
    # from the English four times over. A lesson without frames gets no
    # drills; it does not get somebody else's.
    patterns = lesson.patterns
    out: List[Phrase] = []
    for pattern in patterns:
        for value in pattern.values[:per]:
            text = pattern.text.replace("{x}", value.text)
            reading = pattern.reading.replace("{x}", value.reading) if value.reading else ""
            en = pattern.en.replace("{x}", value.en)
            out.append(Phrase(text, reading, en))
    return out


def count_for(lesson: Lesson, cfg: Dict, lang: str = "zh") -> int:
    return len(generate(lesson, cfg, lang))


# --- old words in new frames ----------------------------------------------
#
# Repeating an identical line mostly trains recitation.  The retrieval benefit
# comes from producing an OLD word in a NEW frame, which is what interleaving
# is for.  A word inherits its kind from the slot it was authored in, so
# authors tag one field per pattern rather than every value.

_ARTICLE = re.compile(r"^(a|an|the)\s+", re.I)
# articles and possessives: any of these in front of {x} means the frame has
# already determined the noun, so a value carrying its own article doubles up
# ("My a passport was stolen").
_TRAILING_DETERMINER = re.compile(
    r"\b(the|a|an|my|your|his|her|its|our|their|this|that|these|those)\s+$", re.I
)
PER_FRAME = 2  # recycled words per frame - two gives contrast without bloat


_LEADING_DETERMINER = re.compile(r"^(my|your|his|her|its|our|their|a|an|the)\b", re.I)


def fill_en(frame: str, value: str) -> str:
    """Substitute {x}, repairing the ways a value gloss fails to compose.

    Slot values are authored to stand alone - capitalised, carrying their own
    article ("My father", "a passport") - but the frame supplies its own
    grammar around the hole.  Dropping a standalone gloss straight in is what
    produced "Please give me the a passport" and "I was cautioned by My
    father".  Both repairs are English-only; the target language is untouched.
    """
    head = frame.split("{x}", 1)[0]
    # 1. doubled determiner: the frame already ends in one
    if _ARTICLE.match(value) and _TRAILING_DETERMINER.search(head):
        value = _ARTICLE.sub("", value, count=1)
    # 2. a gloss capitalised only because it was written standalone.  Lower a
    #    leading determiner when the hole sits mid-sentence.  Proper nouns are
    #    untouched, so "transferred to Kyoto" keeps its capital.
    if not head:
        if value:                                  # sentence-initial
            value = value[0].upper() + value[1:]
    elif _LEADING_DETERMINER.match(value):
        value = value[0].lower() + value[1:]       # mid-sentence
    return frame.replace("{x}", value)


def known_words(course, upto: "int | None" = None) -> List[tuple]:
    """(word, kind) for every slot value authored before lesson `upto`.

    A word that appears in two different kinds of slot is ambiguous and is
    dropped: better to recycle a few words fewer than to teach 学校を食べます.
    """
    words: Dict[str, Phrase] = {}
    kinds: Dict[str, set] = {}
    for lesson in course.lessons.values():
        if upto is not None and lesson.id >= upto:
            continue
        for pattern in lesson.patterns or []:
            if not pattern.kind:
                continue
            for value in pattern.values:
                words[value.text] = value
                kinds.setdefault(value.text, set()).add(pattern.kind)
    return [(words[w], next(iter(k))) for w, k in kinds.items() if len(k) == 1]


def recombine(course, lesson: Lesson, limit: int = 4) -> List[Phrase]:
    """Fill the CURRENT lesson's slots with words learned in EARLIER lessons.

    Returns [] for untagged courses, so nothing changes until the data carries
    kinds, and nothing ungrammatical is ever generated.
    """
    if limit <= 0:
        return []
    pool = known_words(course, upto=lesson.id)
    if not pool:
        return []
    out: List[Phrase] = []
    used: set = set()
    for pattern in lesson.patterns or []:
        if len(out) >= limit:
            break
        if not pattern.kind:
            continue
        own = {v.text for v in pattern.values}
        taken = 0
        for word, kind in pool:
            if taken >= PER_FRAME:
                break
            if kind != pattern.kind or word.text in own or word.text in used:
                continue
            used.add(word.text)
            taken += 1
            out.append(
                Phrase(
                    pattern.text.replace("{x}", word.text),
                    pattern.reading.replace("{x}", word.reading) if word.reading else "",
                    fill_en(pattern.en, word.en),
                    "old word, new frame",
                )
            )
            if len(out) >= limit:
                break
    return out


# --- spaced review ---------------------------------------------------------

# Seconds to wait before an item at a given mastery stage comes back.
#
# The old ladder topped out at 3 days, which meant that an item you had not
# touched in six months was treated as overdue by six months and jumped the
# queue ahead of everything you were actually working on - and, more to the
# point, that nothing was ever scheduled further out than a weekend. Review
# at 3-day intervals for a year is maintenance, not retention; it never tests
# whether you still know the thing. The ladder below runs out to 18 months so
# that a line you truly own can be left alone long enough for forgetting to
# become informative.
#
# Roughly the classic expanding sequence (5m, 30m, 2h, 1d, 3d, 1w, 2w, 5w,
# 3mo, 8mo, 18mo), with the two sub-day steps that make a first session stick.
# Index == mastery stage; see engine.Session.submit for the promotion rule.
STAGE_INTERVALS = [
    0,                  # 0  same session
    5 * 60,             # 1  five minutes
    30 * 60,            # 2  half an hour
    2 * 3600,           # 3  two hours
    24 * 3600,          # 4  one day
    3 * 24 * 3600,      # 5  three days
    7 * 24 * 3600,      # 6  one week
    16 * 24 * 3600,     # 7  a fortnight and a bit
    35 * 24 * 3600,     # 8  five weeks
    90 * 24 * 3600,     # 9  three months
    240 * 24 * 3600,    # 10 eight months
    540 * 24 * 3600,    # 11 eighteen months
]

# Highest mastery stage an item can reach. Kept in step with STAGE_INTERVALS
# rather than derived, so that shortening the ladder can never silently
# promote an item past the end of it.
MAX_STAGE = len(STAGE_INTERVALS) - 1


def due_items(progress: Dict, limit: int = 20, include_fresh: bool = True) -> List[Phrase]:
    """Mastered lines that are due for another pass. Never runs out."""
    mastery = progress.get("mastery") or {}
    now = time.time()
    scored = []
    for key, entry in mastery.items():
        if isinstance(entry, dict):
            stage = int(entry.get("stage", 0))
            ts = float(entry.get("ts", 0) or 0)
            text = entry.get("text") or entry.get("hanzi") or ""
            reading = entry.get("reading") or entry.get("pinyin") or ""
            en = entry.get("en", "")
        else:  # legacy int format
            stage = int(entry)
            ts, text, reading, en = 0.0, "", "", ""
        if not text:
            continue
        interval = STAGE_INTERVALS[min(stage, len(STAGE_INTERVALS) - 1)]
        overdue = now - ts - interval
        if overdue >= 0 or include_fresh:
            scored.append((-overdue, Phrase(text, reading, en)))

    scored.sort(key=lambda pair: pair[0])  # most overdue first
    items: List[Phrase] = []
    seen = set()
    for _, phrase in scored:
        if phrase.text in seen:
            continue
        seen.add(phrase.text)
        items.append(phrase)
        if len(items) >= limit:
            break
    return items
