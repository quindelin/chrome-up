# -*- coding: utf-8 -*-
"""C1-C2 spoken summaries ("Resumen"): read the passage, then say it shorter.

Same contract and the same reasoning as `course.zh.summaries` (HSK 6 缩写):
the skill is deciding what to drop while keeping the point, and that is as
hard spoken as written. DELE C1 and C2 both have a summary-and-synthesis
task, so this is exam-shaped too.

    SUMMARIES[lesson_id] = {"prompt", "prompt_reading", "prompt_en",
                            "sample", "sample_reading", "sample_en",
                            "keywords", "min_chars"}

`keywords` are the points a summary must keep; at least half must be said.
The entries live in c1.py and c2.py next to the passages they summarise.
"""
from . import merged as _merged

SUMMARIES = _merged("SUMMARIES")


def get(lesson_id: int) -> dict:
    return SUMMARIES.get(int(lesson_id)) or {}
