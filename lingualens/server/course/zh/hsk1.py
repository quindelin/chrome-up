# -*- coding: utf-8 -*-
"""HSK 1 — survive the first conversations.

Reuses the hand-authored foundation units in `server/course_zh.py`
(units 1-3: greetings & courtesy, getting around, food & ordering).
"""
from .course_zh import UNITS

LEVEL = {
    "band": 1,
    "id": 1,
    "title": "HSK 1 · First contact",
    "focus": "Greetings, please/thank you/sorry, directions, numbers, ordering the basics.",
    "gate": {"min_pron_score": 62.0, "min_accuracy": 62.0, "min_completeness": 78.0, "min_tone_score": 60.0},
    "units": [dict(u, band=1) for u in UNITS[0:3]],
}
