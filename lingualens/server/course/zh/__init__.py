"""Mandarin course package: the HSK 1 -> HSK 9 ladder.

Two kinds of content live here:
  LEVELS - the lesson ladder (units -> lessons: dialogue, drills, recall)
  VOCAB  - the word bank (themed topics per HSK band), which is what lets you
           build sentences instead of only repeating ours

The ladder used to stop at HSK 6, which quietly made "HSK 6" the goal. It
isn't. The 2021 standard adds 7-9 on top and roughly doubles the word count
again; more to the point, the step from 6 to 7-9 is not more vocabulary but
register and domain - following the news, reading a contract, sitting in a
meeting. So band 7 is "native register" and "domains" rather than "harder
HSK 6".
"""
from . import freeform, hsk1, hsk2, hsk3, hsk4, hsk5, hsk6, hsk7
from . import vocab_hsk1, vocab_hsk2, vocab_hsk3, vocab_hsk4, vocab_hsk5, vocab_hsk6, vocab_hsk7
from . import freeform7
from . import scenes

LEVELS = [
    hsk1.LEVEL,
    hsk2.LEVEL,
    hsk3.LEVEL,
    hsk4.LEVEL,
    hsk5.LEVEL,
    hsk6.LEVEL,
    hsk7.LEVEL,
]

# hsk band -> themed word lists
VOCAB = {
    1: vocab_hsk1.TOPICS,
    2: vocab_hsk2.TOPICS,
    3: vocab_hsk3.TOPICS,
    4: vocab_hsk4.TOPICS,
    5: vocab_hsk5.TOPICS,
    6: vocab_hsk6.TOPICS,
    7: vocab_hsk7.TOPICS,
}

# Prompts are split the same way the levels are: 146 for HSK 1-6 in
# freeform.py, and the HSK 7-9 ones in freeform7.py. Neither overwrites the
# other - a lesson id belongs to exactly one of them.
PROMPTS = {**freeform.PROMPTS, **freeform7.PROMPTS}

# English scene-setting, {lesson_id: one sentence}. Printed, never spoken.
SCENES = scenes.SCENES

# how the UI and the gate talk about this ladder
LABEL = "HSK"          # "HSK 3"
BAND_NAME = "hsk"      # the key used in state / urls
SPEECH_LANG = "zh-CN"  # what the TTS and the dictation engine use

__all__ = ["LEVELS", "VOCAB", "PROMPTS", "SCENES", "LABEL", "BAND_NAME", "SPEECH_LANG",
           "freeform", "freeform7", "scenes"]
