"""Course packages, one per language.

    server/course/zh/   Mandarin  - HSK 1 -> HSK 6
    server/course/ja/   Japanese  - JLPT N5 -> N1, plus an above-N1 band
    server/course/es/   Spanish   - CEFR A1 -> (A2 … C1 being written)

Each package exports the same four things, so everything above this line is
language-agnostic:

    LEVELS       list of raw level dicts -> units -> lessons
    VOCAB        {band: [topic, ...]}   the word bank
    PROMPTS      {lesson_id: [free-response prompt, ...]}
    SPEECH_LANG  BCP-47 tag handed to TTS / dictation

Packages are imported **lazily and independently**. A course is a lot of hand
authored data, so at any moment one of them may be half-written by whoever is
working on it; that must never stop the other course from running. `package_for`
raises ImportError for a broken package and the registry reports it as
"not ready" instead of crashing the server.
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Dict, List, Tuple

DEFAULT_LANG = "zh"

LANG_NAMES = {"zh": "Mandarin", "ja": "Japanese", "es": "Spanish"}

# discovered from the filesystem: a course is a package, not an entry in a list
_LOADED: Dict[str, Any] = {}


def supported() -> List[str]:
    """Every course package that exists on disk, in a stable order."""
    order = ["zh", "ja", "es"]
    found = [m.name for m in pkgutil.iter_modules(__path__) if m.ispkg]
    return [k for k in order if k in found] + sorted(k for k in found if k not in order)


def normalize(lang: str) -> str:
    """Map anything the caller might pass onto a real package key."""
    key = (lang or "").strip().lower()
    if key in LANG_NAMES or key in _LOADED:
        return key
    aliases = {
        "chinese": "zh", "zh-cn": "zh", "zh_cn": "zh", "mandarin": "zh", "cn": "zh",
        "japanese": "ja", "ja-jp": "ja", "ja_jp": "ja", "jp": "ja", "nihongo": "ja",
        "spanish": "es", "es-mx": "es", "es-es": "es", "es_mx": "es", "es_es": "es",
        "espanol": "es", "español": "es", "castellano": "es",
    }
    return aliases.get(key, DEFAULT_LANG)


def package_for(lang: str):
    """Import one course package. Raises ImportError when it is not loadable."""
    key = normalize(lang)
    if key in _LOADED:
        return _LOADED[key]
    try:
        mod = importlib.import_module(f".{key}", __name__)
    except ImportError as exc:
        # do not cache: the author may fix it and reload the page
        raise ImportError(f"course '{key}' is not loadable: {exc}") from exc
    _LOADED[key] = mod
    globals()[key] = mod
    return mod


#: languages written with spaces between words. Every "which characters carry
#: meaning" heuristic in the engine was built for 汉字 and かな, where one
#: character is a unit of meaning; for these, a word is the unit instead.
SPACED = {"es"}


def is_spaced(lang: str) -> bool:
    return normalize(lang) in SPACED


def __getattr__(name: str):
    """`from .course import ja` still works, lazily."""
    if name in LANG_NAMES and name not in _LOADED:
        return package_for(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def module_for(lang: str, name: str):
    """One optional content module from one course package.

    Literacy, reading and grammar used to be imported directly from
    `course.ja` and gated on `lang == "ja"`, which meant a Mandarin
    `readings.py` could exist on disk and still never run. Resolving by name
    is what makes those modules a per-course thing rather than a Japanese
    thing: a package without `hanzi.py` gets no hanzi steps, and nothing else
    has to know which languages wrote which.

    Returns None when the module is missing or broken - a course is authored
    by hand, so "not written yet" must shrink the lesson, not break it.
    """
    key = normalize(lang)
    try:
        return importlib.import_module(f".{name}", f"{__name__}.{key}")
    except Exception:
        return None


def course_data(lang: str) -> Tuple[List[Dict[str, Any]], Dict[int, Any], Dict[int, Any]]:
    """(LEVELS, VOCAB, PROMPTS) for one language."""
    pkg = package_for(lang)
    return list(pkg.LEVELS), dict(pkg.VOCAB), dict(pkg.PROMPTS)


def scenes(lang: str) -> Dict[int, str]:
    """{lesson_id: one English sentence} - the scene before each conversation.

    Optional per course; a package with no SCENES (or none at all) simply gets
    an empty map, and the engine falls back to the lesson's goal line.
    """
    return dict(getattr(package_for(lang), "SCENES", None) or {})


def speech_lang(lang: str) -> str:
    return getattr(package_for(lang), "SPEECH_LANG", "en-US")


def band_label(lang: str) -> str:
    """What the menu calls a band: HSK / JLPT / CEFR…"""
    pkg = package_for(lang)
    label = getattr(pkg, "LABEL", None)
    return {"zh": "HSK", "ja": "JLPT", "es": "CEFR"}.get(normalize(lang), label or "Level")


def native_label(lang: str) -> str:
    """The course in its own language: 中文 / 日本語 / Español."""
    return {"zh": "中文", "ja": "日本語", "es": "Español"}.get(normalize(lang), LANG_NAMES.get(normalize(lang), lang))


__all__ = [
    "DEFAULT_LANG", "LANG_NAMES", "SPACED", "is_spaced", "supported", "normalize", "package_for", "module_for",
    "course_data", "scenes", "speech_lang", "band_label", "native_label", "zh", "ja", "es",
]
