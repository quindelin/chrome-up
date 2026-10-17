# -*- coding: utf-8 -*-
"""JLPT N4 — real errands: shopping, prices, time, plans, opinions.

Reuses units 4-5 of `server/course/ja/course_ja.py`.
"""
from .course_ja import UNITS

LEVEL = {
    "band": 4,
    "id": 2,
    "code": "N4",
    "title": "JLPT N4 · Everyday errands",
    "focus": "Shopping and prices, paying, telling the time, making plans, saying what you think.",
    "gate": {"min_pron_score": 68.0, "min_accuracy": 68.0, "min_completeness": 82.0,
             "min_tone_score": 64.0},
    "units": [dict(u, band=4) for u in UNITS[3:5]],
}
