"""Japanese course package: six bands, labelled by what they teach
(N5, N4, N4+, N4–N3, N3, N2 preview; see docs/COURSE_AUDIT.md).

Two kinds of content live here:
  LEVELS - the lesson ladder (units -> lessons: dialogue, drills, recall)
  VOCAB  - the word bank (themed topics per JLPT band), which is what lets you
           build sentences instead of only repeating ours

Content modules are loaded defensively.  Authors land files at different
times, so a level that is still being written must shrink the ladder rather
than break the whole course - otherwise N5 through N3 are unusable while N2 is
drafted.  ONLY ModuleNotFoundError is tolerated: a module that exists but
fails to import (syntax error, malformed data) still raises, so real breakage
is never silently hidden.
"""
from importlib import import_module

# (attribute, module name) - band id for vocab, None for a level module
_LEVEL_MODULES = ["jlpt5", "jlpt4", "jlpt3", "jlpt2", "jlpt1", "jlpt0"]
_VOCAB_MODULES = {5: "vocab_n5", 4: "vocab_n4", 3: "vocab_n3",
                  2: "vocab_n2", 1: "vocab_n1", 0: "vocab_n0"}


def _try(name):
    """Import a sibling content module, or return None if it is not written yet."""
    try:
        return import_module(f".{name}", __name__)
    except ModuleNotFoundError:
        return None


_modules = {name: _try(name) for name in set(_LEVEL_MODULES) | set(_VOCAB_MODULES.values())}
freeform = _try("freeform")
scenes = _try("scenes")

LEVELS = [_modules[n].LEVEL for n in _LEVEL_MODULES if _modules[n]]

# jlpt band -> themed word lists. Band n's bank is JLPT Nn-sized (0 = above
# N1), even where the band's lessons are labelled lower.
VOCAB = {band: _modules[n].TOPICS for band, n in sorted(_VOCAB_MODULES.items())
         if _modules[n]}

PROMPTS = getattr(freeform, "PROMPTS", {}) if freeform else {}

# English scene-setting, {lesson_id: one sentence}. Printed, never spoken.
# Optional: a course with no scenes module still loads, it just has no scenes.
SCENES = getattr(scenes, "SCENES", {}) if scenes else {}

# how the UI and the gate talk about this ladder
LABEL = "N"            # fallback only: every band authors its own `code`
BAND_NAME = "jlpt"     # the key used in state / urls
SPEECH_LANG = "ja-JP"  # what the TTS and the dictation engine use

__all__ = ["LEVELS", "VOCAB", "PROMPTS", "SCENES", "LABEL", "BAND_NAME", "SPEECH_LANG",
           "freeform", "scenes"]
