# -*- coding: utf-8 -*-
"""Where to start.

Everybody used to begin at lesson 1 with 你好. That is right for most people
and quietly terrible for the rest: an intermediate learner spends weeks on
content they already have, and a complete beginner dropped into HSK 4 learns
nothing but failure. The course has no idea which it is dealing with.

So: a short test, ~4 lines from each band, spoken and gated the same way a
lesson is. The result is the first band that actually challenges you, which
is where you start.

Two design decisions worth stating:

1. **It samples dialogue, it doesn't invent test items.** Placement items
   that are specially written measure the test, not the course. A line from
   lesson 40 is exactly the thing you would be asked to say in lesson 40.

2. **It places you at the first band you can't do, not the last one you
   can.** Being placed slightly low costs a few lessons of easy review;
   being placed slightly high costs the confidence to continue at all.

The test is deliberately short. Twenty-odd lines is enough to separate six
bands, because the bands are far apart; a longer test would be more precise
and nobody would finish it.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .curriculum import Course
from .models import Score
from .pronunciation import evaluate

# lines per band, and the pass rate below which that band counts as "not yet"
PER_BAND = 4
PASS_RATE = 0.6


def build(course: Course, per_band: int = PER_BAND) -> List[Dict]:
    """One probe per band, spread across that band's lessons.

    Lines are taken from the middle of each band rather than its start, so a
    probe is representative of the band and not of its easiest lesson. The
    learner's own line ("you") is used: something they would be asked to say,
    not something said at them.
    """
    items: List[Dict] = []
    for level in course.levels:
        ids = [l.id for l in course.lessons_of_band(level.band)]
        if not ids:
            continue
        # spread the probes across the band
        picks = _spread(ids, max(1, per_band))
        for lid in picks:
            lesson = course.lesson(lid)
            if not lesson:
                continue
            turn = next((t for t in lesson.dialogue if t.speaker == "you"), None)
            if not turn:
                continue
            items.append({
                "lesson_id": lid,
                "band": level.band,      # int, for grouping the results
                "code": level.code,      # "HSK 4", for showing the learner
                "text": turn.text,
                "reading": turn.reading,
                "en": turn.en,
            })
    return items


def _spread(ids: List[int], n: int) -> List[int]:
    """n ids spread across the list, without repeats."""
    if not ids or n <= 0:
        return []
    if n >= len(ids):
        return list(ids)
    step = len(ids) / float(n)
    out, seen = [], set()
    for i in range(n):
        idx = min(len(ids) - 1, int(i * step + step / 2))
        lid = ids[idx]
        if lid not in seen:
            seen.add(lid)
            out.append(lid)
    return out


class Placement:
    """One learner's placement test, in memory while it runs."""

    def __init__(self, course: Course, cfg: Dict, items: Optional[List[Dict]] = None):
        self.course = course
        self.cfg = cfg
        self.items = items if items is not None else build(course)
        self.pos = 0
        self.results: List[Tuple[int, bool]] = []  # (band, passed)

    # -- running ------------------------------------------------------------
    def current(self) -> Optional[Dict]:
        if self.pos < len(self.items):
            return self.items[self.pos]
        return None

    def submit(self, score: Score) -> Dict:
        """Grade one probe. Never blocks: a failed probe still moves on."""
        item = self.current()
        if not item:
            return {"done": True, "recommended": self.recommended()}
        gate = self.course.gate_for(item["lesson_id"], self.cfg["gate"])
        passed, reasons = evaluate(score, gate)
        self.results.append((int(item["band"]), bool(passed)))
        self.pos += 1
        return {
            "done": self.pos >= len(self.items),
            "passed": bool(passed),
            "reasons": list(reasons),
            "item": item,
            "progress": f"{self.pos}/{len(self.items)}",
            "recommended": self.recommended() if self.pos >= len(self.items) else None,
        }

    # -- the verdict --------------------------------------------------------
    def rates(self) -> Dict[int, float]:
        """Pass rate per band, from what has been answered so far."""
        bands: Dict[int, List[bool]] = {}
        for band, ok in self.results:
            bands.setdefault(band, []).append(ok)
        return {b: (sum(v) / len(v)) for b, v in bands.items()}

    def recommended(self) -> Optional[int]:
        """First lesson of the first band the learner can't yet do.

        All bands cleared means the top band - which is a real result, not a
        fallback: someone who can place out of a 85-lesson course should be
        allowed to.
        """
        if not self.results:
            return None
        rates = self.rates()

        def first_of(band: int) -> Optional[int]:
            lessons = self.course.lessons_of_band(band)
            return lessons[0].id if lessons else None

        for band in sorted(rates):
            if rates[band] < PASS_RATE:
                return first_of(band)
        return first_of(max(rates))
