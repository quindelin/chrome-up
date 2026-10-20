# -*- coding: utf-8 -*-
"""Mandarin: what the engine needs to know about this course's language.

Loaded on its own by server/course/__init__.py (no package import). The full
field list, with what each one does, is in docs/NEW_COURSE.md.
"""

CODE = "zh"
NAME = "Mandarin"
NATIVE = "中文"
ALIASES = ["chinese", "zh-cn", "zh_cn", "mandarin", "cn", "putonghua"]
BAND_LABEL = "HSK"
TOKENS = "char"          # one character is one unit of meaning
SPEECH_LANG = "zh-CN"
# Prompts, fillers, notes and config defaults for zh still live in the
# engine's own tables (free.py, think.py, pronunciation.py, engine.py,
# config.py LANG_DEFAULTS); a new course puts them here instead.
