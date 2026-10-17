"""Per-course progress: lessons, the word ledger, and the habits around them.

One learner can study Mandarin and Japanese at the same time, so everything
hangs off `courses[lang]` inside a single JSON document:

    {
      "active": "zh",
      "courses": {
        "zh": {
          "lesson_id": 12,
          "completed": [1, 2, 3],
          "mastery":   {"12:你好": {"stage": 3, "ts": ...}},
          "words":     {"你好": {"text": "你好", "reading": "nǐ hǎo", ...}},
          "stats":     {"utterances": 812, "attempts": 1204, "seconds": 5400,
                        "days": ["2026-10-15", "2026-10-16"]}
        },
        "ja": {...}
      }
    }

`words` is the ledger the phone shows: every item you have actually passed
the gate on, with how many times and when. `kind` splits single vocabulary
items (`word`) from whole lines (`phrase`) so a learner can watch their
vocabulary grow without the dialogue lines drowning it.
"""
from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

DAY_FMT = "%Y-%m-%d"

# what an old, single-course state.json looks like
_LEGACY_KEYS = ("lesson_id", "completed", "mastery")


def _today() -> str:
    return date.today().strftime(DAY_FMT)


def _blank_course() -> Dict[str, Any]:
    return {
        "lesson_id": None,
        "completed": [],
        "mastery": {},
        "words": {},
        # Per-syllable scores, keyed by the syllable itself: {"好": [n, tone_sum,
        # phone_sum]}. Every attempt already produces them - iFlytek reports a
        # tone score per syllable - and they were being thrown away the moment
        # the attempt was graded. Aggregated, they are the most useful thing in
        # the app: not "your tones are 78" but "your third tones are fine and
        # your 3+3 sequences are not, and 好 is where it shows".
        "syllables": {},
        "stats": {"utterances": 0, "attempts": 0, "seconds": 0.0, "days": [], "last_day": ""},
    }


class Learner:
    """One learner's state across every course."""

    def __init__(self, raw: Optional[Dict[str, Any]], default_lang: str) -> None:
        self.default_lang = default_lang
        self.migrated = False
        # Mutate the caller's dict in place: the store keeps a reference to it,
        # so a migration must never rebind to a fresh object.
        if not isinstance(raw, dict):
            raw = {}
        self.raw = raw
        if "courses" not in raw:
            self.migrated = True
            legacy = {k: v for k, v in raw.items() if k in _LEGACY_KEYS}
            raw.clear()
            raw.update({"active": default_lang, "courses": {default_lang: legacy} if legacy else {}})
        courses = raw.setdefault("courses", {})
        if not isinstance(courses, dict):
            courses = {}
            raw["courses"] = courses
        for lang, body in list(courses.items()):
            # fill in missing keys in place: a live Session holds a reference
            # to this exact dict, so it must never be replaced by a copy
            base = _blank_course()
            if not isinstance(body, dict):
                courses[lang] = base
                continue
            for key, value in base.items():
                if key not in body:
                    body[key] = value
            if not isinstance(body["stats"], dict):
                body["stats"] = {}
            for key, value in base["stats"].items():
                body["stats"].setdefault(key, value)

    # -- active course -------------------------------------------------------
    @property
    def active(self) -> str:
        return self.raw.get("active") or self.default_lang

    def set_active(self, lang: str) -> str:
        self.raw["active"] = lang
        return lang

    # -- per-course state ----------------------------------------------------
    def course(self, lang: str) -> Dict[str, Any]:
        courses = self.raw.setdefault("courses", {})
        body = courses.get(lang)
        if not isinstance(body, dict):
            body = _blank_course()
            courses[lang] = body
        return body

    def has(self, lang: str) -> bool:
        return isinstance(self.raw.get("courses", {}).get(lang), dict)

    def languages(self) -> List[str]:
        return sorted(self.raw.get("courses", {}).keys())


# --------------------------------------------------------------------------
# recording
# --------------------------------------------------------------------------
def record_attempt(p: Dict[str, Any], passed: bool, seconds: float = 0.0) -> None:
    """Count the attempt; only a pass becomes a learned utterance."""
    stats = p.setdefault("stats", _blank_course()["stats"])
    stats["attempts"] = int(stats.get("attempts") or 0) + 1
    if seconds > 0:
        stats["seconds"] = float(stats.get("seconds") or 0.0) + float(seconds)
    if passed:
        stats["utterances"] = int(stats.get("utterances") or 0) + 1
    day = _today()
    days = stats.setdefault("days", [])
    if day not in days:
        days.append(day)
        days.sort()
        if len(days) > 400:
            del days[: len(days) - 400]
    stats["last_day"] = day


def record_learned(
    p: Dict[str, Any],
    text: str,
    reading: str = "",
    en: str = "",
    kind: str = "phrase",
    band: int = 0,
    lesson_id: Optional[int] = None,
    score: float = 0.0,
) -> Dict[str, Any]:
    """Add one passed item to the learner's word ledger."""
    text = (text or "").strip()
    if not text:
        return {}
    words = p.setdefault("words", {})
    now = time.time()
    entry = words.get(text)
    if not isinstance(entry, dict):
        entry = {
            "text": text,
            "reading": reading,
            "en": en,
            "kind": kind,
            "band": band,
            "lesson_id": lesson_id,
            "first": now,
            "last": now,
            "passes": 0,
            "best": 0.0,
        }
        words[text] = entry
    entry["passes"] = int(entry.get("passes") or 0) + 1
    entry["last"] = now
    entry["best"] = max(float(entry.get("best") or 0.0), float(score or 0.0))
    # keep the freshest metadata: authors occasionally fix a reading
    if reading:
        entry["reading"] = reading
    if en:
        entry["en"] = en
    if band:
        entry["band"] = band
    return entry


def record_syllables(p: Dict[str, Any], syllables: List[dict]) -> None:
    """Fold one attempt's per-syllable scores into the running totals.

    Stored as [times, tone_sum, phone_sum] rather than a list of scores: it
    has to stay small enough to sit in state.json for months, and a mean is
    all the heatmap ever shows. A -1 means "the provider did not measure
    this" and is skipped rather than counted as a zero.
    """
    if not syllables:
        return
    ledger = p.setdefault("syllables", {})
    if not isinstance(ledger, dict):
        return
    for unit in syllables:
        word = str(unit.get("word") or "").strip()
        if not word:
            continue
        tone = float(unit.get("tone", -1) or -1)
        phone = float(unit.get("accuracy", -1) or -1)
        if tone < 0 and phone < 0:
            continue
        row = ledger.get(word)
        if not isinstance(row, list) or len(row) != 3:
            row = [0, 0.0, 0.0]
            ledger[word] = row
        row[0] = int(row[0]) + 1
        if tone >= 0:
            row[1] = float(row[1]) + tone
        if phone >= 0:
            row[2] = float(row[2]) + phone


def diagnostics(p: Dict[str, Any], limit: int = 12) -> Dict[str, Any]:
    """The tone/phone heatmap: what to fix first, derived from what you did.

    Sorted worst-first and only reported past a small sample, because one bad
    attempt at a syllable is noise and five is a pattern.
    """
    ledger = p.get("syllables") or {}
    if not isinstance(ledger, dict):
        return {"worst_tone": [], "worst_phone": [], "samples": 0}
    rows = []
    for word, row in ledger.items():
        if not isinstance(row, list) or len(row) != 3:
            continue
        times = int(row[0] or 0)
        if times < 3:
            continue
        tone = float(row[1]) / times if row[1] else -1.0
        phone = float(row[2]) / times if row[2] else -1.0
        rows.append({"word": word, "times": times, "tone": round(tone, 1),
                     "phone": round(phone, 1)})

    def top(key: str) -> List[dict]:
        measured = [r for r in rows if r[key] >= 0]
        measured.sort(key=lambda r: r[key])
        return measured[: max(0, limit)]

    return {
        "worst_tone": top("tone"),
        "worst_phone": top("phone"),
        "samples": sum(int(r[0]) for r in ledger.values() if isinstance(r, list)),
        "distinct": len(rows),
    }


# --------------------------------------------------------------------------
# reading it back
# --------------------------------------------------------------------------
def streak_days(p: Dict[str, Any]) -> int:
    """Consecutive days practised, counting back from today (or yesterday)."""
    days = (p.get("stats") or {}).get("days") or []
    if not days:
        return 0
    seen = {d for d in days if isinstance(d, str)}
    cursor = date.today()
    if cursor.strftime(DAY_FMT) not in seen:
        cursor -= timedelta(days=1)  # a day that has not ended yet still counts
        if cursor.strftime(DAY_FMT) not in seen:
            return 0
    run = 0
    while cursor.strftime(DAY_FMT) in seen:
        run += 1
        cursor -= timedelta(days=1)
    return run


def word_list(
    p: Dict[str, Any],
    kind: str = "",
    band: Optional[int] = None,
    query: str = "",
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """The learned items, newest first. `kind`: word | phrase."""
    items = [w for w in (p.get("words") or {}).values() if isinstance(w, dict)]
    if kind:
        items = [w for w in items if (w.get("kind") or "phrase") == kind]
    if band is not None:
        items = [w for w in items if int(w.get("band") or 0) == int(band)]
    q = (query or "").strip().lower()
    if q:
        items = [
            w
            for w in items
            if q in (w.get("text") or "").lower()
            or q in (w.get("reading") or "").lower()
            or q in (w.get("en") or "").lower()
        ]
    items.sort(key=lambda w: (w.get("last") or 0), reverse=True)
    total = len(items)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [dict(w, first_day=_day(w.get("first")), last_day=_day(w.get("last")))
                  for w in items[offset : offset + limit]],
    }


def _day(ts: Optional[float]) -> str:
    if not ts:
        return ""
    try:
        return date.fromtimestamp(float(ts)).strftime(DAY_FMT)
    except (ValueError, OSError, OverflowError):
        return ""


def summary(
    course_lang: str,
    p: Dict[str, Any],
    course=None,
    review_due: int = 0,
    name: str = "",
    native: str = "",
) -> Dict[str, Any]:
    """Everything the progress screen for one course needs."""
    words = {k: v for k, v in (p.get("words") or {}).items() if isinstance(v, dict)}
    learned_words = [w for w in words.values() if (w.get("kind") or "") == "word"]
    phrases = [w for w in words.values() if (w.get("kind") or "") != "word"]

    completed = set(p.get("completed") or [])
    lesson_total = len(course.lesson_ids) if course else 0
    vocab_total = course.vocab_count() if course else 0
    stats = p.get("stats") or {}

    bands: List[Dict[str, Any]] = []
    if course:
        for lv in course.levels:
            lv_lessons = {l.id for l in course.lessons_of_band(lv.band)}
            bands.append(
                {
                    "id": lv.id,
                    "band": lv.band,
                    "code": lv.code,
                    "title": lv.title,
                    "lessons_done": len(lv_lessons & completed),
                    "lessons_total": len(lv_lessons),
                    "words_learned": sum(1 for w in learned_words if int(w.get("band") or 0) == lv.band),
                    "words_total": lv.vocab_count(),
                }
            )

    recent = sorted(words.values(), key=lambda w: (w.get("last") or 0), reverse=True)[:6]
    minutes = round(float(stats.get("seconds") or 0.0) / 60.0, 1)

    return {
        "course": course_lang,
        "name": name or course_lang,
        "native": native or name or course_lang,
        "lessons_done": len(completed),
        "lessons_total": lesson_total,
        "lesson_pct": _pct(len(completed), lesson_total),
        "words_learned": len(learned_words),
        "words_total": vocab_total,
        "word_pct": _pct(len(learned_words), vocab_total),
        "phrases_learned": len(phrases),
        "utterances": int(stats.get("utterances") or 0),
        "attempts": int(stats.get("attempts") or 0),
        "minutes": minutes,
        "streak_days": streak_days(p),
        "last_day": stats.get("last_day") or "",
        "review_due": review_due,
        "bands": bands,
        "recent": [
            {"text": w.get("text"), "reading": w.get("reading"), "en": w.get("en"),
             "kind": w.get("kind"), "passes": w.get("passes"), "last_day": _day(w.get("last"))}
            for w in recent
        ],
    }


def _pct(done: int, total: int) -> float:
    if not total:
        return 0.0
    return round(100.0 * done / total, 1)
