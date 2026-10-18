"""Spanish course package: the CEFR ladder, A1 first.

Same contract as `course.ja` and `course.zh`:
  LEVELS  - the lesson ladder (units -> lessons: dialogue, drills, recall)
  VOCAB   - the word bank (themed topics per CEFR band)
  PROMPTS - free-response questions per lesson
  SCENES  - one English sentence before each conversation

Bands count UP, the way HSK does and JLPT does not: 1 = A1, 2 = A2,
3 = B1, 4 = B2, 5 = C1. Only A1 is written so far; the loader tolerates the
rest being absent, exactly like the Japanese package, so the ladder grows
one band at a time without the course ever failing to load.

Built against the audit of the Japanese course (docs/COURSE_AUDIT.md), so
from lesson 1:
  * every lesson has substitution patterns with slot kinds, so old words come
    back in new frames (the Japanese N5/N4 lessons have none)
  * the learner, not the other speaker, says the lesson's target structure
  * tú and usted are both taught and both produced - register is not deferred
  * one variety, stated: the lines are Peninsular (Spain) Spanish, and where
    Latin America says it differently the vocab note says so (billete /
    boleto, zumo / jugo, recto / derecho). Mixing them line to line is what
    a teacher would mark down first.
  * the word bank is sized to what the lessons actually inject, so walking the
    band in order reaches every word (Japanese reaches ~7% of its bank)
"""
from importlib import import_module

_LEVEL_MODULES = ["a1", "a2", "b1", "b2", "c1"]
_VOCAB_MODULES = {1: "vocab_a1", 2: "vocab_a2", 3: "vocab_b1", 4: "vocab_b2", 5: "vocab_c1"}


def _try(name):
    """Import a sibling content module, or None if it is not written yet.

    Only a *missing* module is tolerated: one that exists and fails to import
    still raises, so broken content is never silently hidden.
    """
    try:
        return import_module(f".{name}", __name__)
    except ModuleNotFoundError as exc:
        if exc.name != f"{__name__}.{name}":
            raise
        return None


_modules = {name: _try(name) for name in set(_LEVEL_MODULES) | set(_VOCAB_MODULES.values())}
freeform = _try("freeform")
scenes = _try("scenes")

LEVELS = [_modules[n].LEVEL for n in _LEVEL_MODULES if _modules[n]]
VOCAB = {band: _modules[n].TOPICS for band, n in sorted(_VOCAB_MODULES.items()) if _modules[n]}
PROMPTS = getattr(freeform, "PROMPTS", {}) if freeform else {}
SCENES = getattr(scenes, "SCENES", {}) if scenes else {}

LABEL = "CEFR"
BAND_NAME = "cefr"
SPEECH_LANG = "es-ES"   # TTS + dictation. The course is Peninsular; es-MX works too.

__all__ = ["LEVELS", "VOCAB", "PROMPTS", "SCENES", "LABEL", "BAND_NAME", "SPEECH_LANG",
           "freeform", "scenes"]
