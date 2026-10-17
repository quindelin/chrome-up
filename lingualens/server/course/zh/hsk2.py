# -*- coding: utf-8 -*-
"""HSK 2 — real errands: shopping, bargaining, time, plans, opinions.

Reuses units 4-5 of `server/course_zh.py`.
"""
from .course_zh import UNITS

LEVEL = {
    "band": 2,
    "id": 2,
    "title": "HSK 2 · Everyday errands",
    "focus": "Shopping and bargaining, paying, telling the time, making plans, saying what you think.",
    "gate": {"min_pron_score": 68.0, "min_accuracy": 68.0, "min_completeness": 82.0, "min_tone_score": 64.0},
    "units": [dict(u, band=2) for u in UNITS[3:5]],
}
