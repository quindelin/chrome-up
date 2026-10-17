# -*- coding: utf-8 -*-
"""Loading the big tables, which are authored in parts.

Kana, kanji, readings and grammar are big enough that more than one person
writes them at a time, so each is split into part files merged at import
time. Two things have to hold for that to be safe:

1. A missing part must not break the course. It is a gap in the content,
   not a bug.
2. Running a checker directly - `python server/course/ja/readings.py` -
   must load the parts too. Relative imports do not work without package
   context, and a bare `except ImportError` around them leaves the checker
   reporting only the worked examples: apparently clean, actually blind.
   That is worse than a crash, so `load_parts` falls back to an absolute
   import with the repo root on sys.path.
"""

import importlib
import os
import sys

_PACKAGE = "server.course.ja"


def _repo_root() -> str:
    # this file lives at <root>/server/course/ja/_parts.py
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir, os.pardir))


# name -> number of rows that part contributed, for the checkers to print.
# A part that fails to import yields None and counts 0, and the difference
# between "this part is 22 passages" and "this part is 0 passages" is the
# only way to notice a part that has gone quietly missing.
LOADED: dict = {}


def load_parts(names, attr):
    """Return [value or None] for `attr` in each of the part modules."""
    out = []
    for name in names:
        mod = None
        # the normal case: imported as a submodule of the package
        try:
            mod = importlib.import_module("." + name, _PACKAGE)
        except ImportError:
            pass
        # run directly as a script: no package context, so bootstrap sys.path
        if mod is None:
            root = _repo_root()
            if root not in sys.path:
                sys.path.insert(0, root)
            try:
                mod = importlib.import_module(_PACKAGE + "." + name)
            except ImportError:
                pass
        value = getattr(mod, attr, None) if mod else None
        LOADED[name] = len(value) if value is not None else 0
        out.append(value)
    return out


def dead_parts(names):
    """Parts whose file exists on disk but contributed nothing.

    A part that is merely absent is fine - it has not been written yet. A
    part whose file exists and yields zero rows is a module that failed to
    import or exported the wrong name, and that must not pass quietly:
    several hundred rows disappear and every check still reports clean.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    return [n for n in names
            if not LOADED.get(n) and os.path.exists(os.path.join(here, n + ".py"))]
