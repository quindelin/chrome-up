# -*- coding: utf-8 -*-
"""JLPT N5 — survive the first conversations.

Reuses the hand-authored foundation units in `server/course/ja/course_ja.py`
(units 1-3: greetings & courtesy, getting around, food & ordering).
"""
from .course_ja import UNITS

LEVEL = {
    "band": 5,
    "id": 1,
    "code": "N5",
    "title": "JLPT N5 · First contact",
    "focus": "Greetings, please/thank you/sorry, directions, transport, ordering the basics.",
    "gate": {"min_pron_score": 62.0, "min_accuracy": 62.0, "min_completeness": 78.0,
             "min_tone_score": 60.0},
    "units": [dict(u, band=5) for u in UNITS[0:3]],
}
