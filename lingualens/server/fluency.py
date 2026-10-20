"""How far a course's content can actually take a learner.

A course is labelled A1-C2 by the grammar its lessons cover. That label says
nothing about exposure: 76 lessons and 1,200 words is A2 vocabulary however
far the syllabus reaches. This module measures what a course contains,
compares it to what each CEFR band needs, and names the highest band the
content backs up - the *earned* level, which is what the app shows.

The targets, cumulative and per band (docs/FLUENCY_TARGETS.md has the sources):

  words   - distinct vocabulary taught: lesson vocab + bank + deck.
            CEFR word-count studies (Milton & Alexiou 2009, Milton 2010)
            put B2 at roughly 3,000-4,000 and C2 at 5,000-8,000+.
  listen  - running words of graded story text in the library. Nation
            (2006) puts unassisted listening at 6-7k word families and
            98% coverage, which only volume of input builds. Scaled by
            the language's FSI category: Arabic needs more hours than
            Italian to reach the same band.
  context - share of deck words that occur in a story at or below their
            band. A word learned only as a flashcard is half learned.

A band counts as earned only when every band below it is earned too.
Approximate by design: matching a deck word inside a story uses a folded
prefix, not a lemmatizer. It is a floor for the gate, not a linguistic
analysis; the reviewer pass in docs/EXPAND_COURSE.md does the real check.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from . import course as course_pkg

CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"]

# cumulative, by CEFR index 1..6
WORDS = {1: 600, 2: 1200, 3: 2500, 4: 4000, 5: 6000, 6: 8000}
LISTEN = {1: 5_000, 2: 20_000, 3: 60_000, 4: 130_000, 5: 230_000, 6: 350_000}
CONTEXT = 0.80

# running words per story, by CEFR index: a short story at A1, a long one at C2
STORY_WORDS = {1: (50, 160), 2: (100, 260), 3: (180, 420), 4: (300, 650),
               5: (400, 950), 6: (500, 1200)}

# FSI category (1 = closest to English, 4 = hardest) and the input it costs
FSI = {"es": 1, "fr": 1, "it": 1, "pt": 1, "de": 2, "ru": 3, "hi": 3,
       "ar": 4, "ko": 4, "zh": 4, "ja": 4}
FSI_FACTOR = {1: 1.0, 2: 1.15, 3: 1.3, 4: 1.6}

WPM = 130            # speech rate the hour estimates assume
SECONDS_PER_STEP = 9.0
SECONDS_PER_DECK_WORD = 25.0


def label(cefr: int) -> str:
    return CEFR[cefr - 1] if cefr else "pre-A1"


def fsi_category(lang: str) -> int:
    return int(course_pkg.meta_get(lang, "FSI_CATEGORY", 0) or FSI.get(lang, 2))


def listen_target(lang: str, cefr: int) -> int:
    return int(LISTEN[cefr] * FSI_FACTOR[fsi_category(lang)])


def running_words(text: str, lang: str) -> int:
    """Words in a line; an unspaced script counts characters / CHARS_PER_WORD."""
    if course_pkg.is_spaced(lang):
        return len(course_pkg.words(text))
    per = float(course_pkg.meta_get(lang, "CHARS_PER_WORD", 1.7) or 1.7)
    return int(round(sum(1 for ch in text if ch.isalpha()) / per))


def cefr_of_bands(course) -> Dict[int, int]:
    """{course band: CEFR index}. Levels are authored easiest-first, so the
    k-th level is the k-th CEFR band; HSK and JLPT map by position (an
    approximation, documented in FLUENCY_TARGETS.md), anything past C2 caps."""
    return {lv.band: min(i + 1, 6) for i, lv in enumerate(course.levels)}


def _key(word: str, lang: str) -> str:
    from .pronunciation import _fold
    m = course_pkg.meta(lang)
    fn = getattr(m, "word_key", None) if m else None
    if fn:
        try:
            word = fn(word) or word
        except Exception:  # noqa: BLE001 - a course's helper must not break the report
            pass
    word = _fold(word)
    hangul = any("가" <= ch <= "힣" for ch in word)
    return word[:2] if hangul else word[:5]


def _content_keys(text: str, lang: str) -> set:
    from .curriculum import _function_words
    fw = _function_words(lang)
    return {_key(w, lang) for w in course_pkg.words(text) if w not in fw}


def in_text(word: str, keys: set, blob: str, lang: str) -> bool:
    """Whether a deck word occurs in a story (keys / blob of that story set)."""
    if not course_pkg.is_spaced(lang):
        core = "".join(ch for ch in word if ch.isalpha())
        return bool(core) and core in blob
    need = _content_keys(word, lang)
    return bool(need) and need <= keys


def report(course, cfg: Optional[Dict] = None) -> Dict:
    """What the course holds, band by band, against the targets."""
    lang = course.lang
    mapping = cefr_of_bands(course)
    rows: List[Dict] = []
    seen_words: set = set()
    listen_total = 0
    deck_total: List[str] = []
    story_keys: set = set()
    story_blob = ""
    steps_total = 0
    earned = 0
    broken = False
    readings = course_pkg.module_for(lang, "readings")
    if readings is not None and not hasattr(readings, "get"):
        readings = None

    for lv in course.levels:
        band = lv.band
        cefr = mapping[band]
        lessons = course.lessons_of_band(band)
        for l in lessons:
            seen_words |= {v.text for v in l.vocab}
        seen_words |= {w.text for w in course.vocab_words(band)}
        deck = [w.text for w in course.deck_words(band)]
        seen_words |= set(deck)
        deck_total += deck
        stories = course.stories_of_band(band)
        # a lesson's passage is heard blind too, so it is input like a story
        for l in lessons:
            chunks = (readings.get(l.id) or {}).get("chunks") if readings else None
            listen_total += sum(running_words(c[0], lang) for c in (chunks or []))
        for st in stories:
            text = " ".join(c.text for c in st.chunks)
            listen_total += running_words(text, lang)
            if course_pkg.is_spaced(lang):
                story_keys |= _content_keys(text, lang)
            else:
                story_blob += text
        in_ctx = sum(1 for w in deck_total if in_text(w, story_keys, story_blob, lang))
        # nothing in a deck means nothing is flashcard-only
        context = (in_ctx / len(deck_total)) if deck_total else 1.0
        # lesson steps are estimated from the bank inject, not built: building
        # every session is what the gate does, and it is slow
        steps_total += sum(1 for _ in lessons) * 175

        need_words, need_listen = WORDS[cefr], listen_target(lang, cefr)
        ok = (len(seen_words) >= need_words and listen_total >= need_listen
              and context >= CONTEXT)
        if ok and not broken:
            earned = cefr
        else:
            broken = True

        rows.append({
            "band": band, "code": lv.code, "cefr": CEFR[cefr - 1],
            "lessons": len(lessons), "stories": len(stories),
            "words": len(seen_words), "words_target": need_words,
            "listen_words": listen_total, "listen_target": need_listen,
            "context": round(context, 3), "context_target": CONTEXT,
            "met": ok,
        })

    # each dimension by its course-wide total: "1,196 words" is A1-sized
    # vocabulary however the words are spread over the bands
    words_level = max([c for c in WORDS if len(seen_words) >= WORDS[c]] or [0])
    listen_level = max([c for c in LISTEN if listen_total >= listen_target(lang, c)] or [0])
    deck_n = len(deck_total)
    hours = (steps_total * SECONDS_PER_STEP / 3600.0
             + listen_total / WPM / 60.0 * 2.0          # heard blind, then followed
             + deck_n * SECONDS_PER_DECK_WORD / 3600.0)
    top = max(mapping.values()) if mapping else 0
    return {
        "language": lang,
        "fsi_category": fsi_category(lang),
        "claimed": CEFR[top - 1] if top else "",
        "earned": label(earned),
        "earned_index": earned,
        # each dimension on its own, for the honest label: grammar is what the
        # lessons cover, the other two are what the content backs up
        "grammar": CEFR[top - 1] if top else "",
        "vocabulary": label(words_level),
        "listening": label(listen_level),
        "hours": round(hours, 1),
        "bands": rows,
    }


def gaps(rep: Dict, upto: int = 6) -> List[str]:
    """What is still missing, in words an author can act on."""
    out = []
    for r in rep["bands"]:
        if CEFR.index(r["cefr"]) + 1 > upto:
            break
        if r["met"]:
            continue
        need = []
        if r["words"] < r["words_target"]:
            need.append(f"{r['words_target'] - r['words']} more words")
        if r["listen_words"] < r["listen_target"]:
            need.append(f"{r['listen_target'] - r['listen_words']} more running words of stories")
        if r["context"] < r["context_target"]:
            need.append(f"deck-in-story {r['context']:.0%} < {r['context_target']:.0%}")
        out.append(f"{r['code']} ({r['cefr']}): " + ", ".join(need))
    return out
