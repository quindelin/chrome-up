"""Course packages, one per language.

    server/course/zh/   Mandarin  - HSK 1 -> HSK 6
    server/course/ja/   Japanese  - JLPT N5 -> N1, plus an above-N1 band
    server/course/es/   Spanish   - CEFR A1 -> C2

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
import importlib.util
import os
import pkgutil
import unicodedata
from typing import Any, Dict, List, Tuple

DEFAULT_LANG = "zh"

# discovered from the filesystem: a course is a package, not an entry in a list
_LOADED: Dict[str, Any] = {}


# -- per-language metadata ----------------------------------------------------
#
# Everything the engine needs to know about a language lives in that
# language's own folder, in `meta.py`: its name, aliases, level label,
# whether it is matched by word or by character, and optionally its function
# words, fillers, prompts, UI labels and config defaults. See
# docs/NEW_COURSE.md. That is what lets a new course be added as one folder
# and one config file, by several agents at once, without any of them
# editing a shared engine file.
#
# meta.py is loaded as a standalone file, not through the package: importing
# the package loads the whole course, and a course that is half-written must
# not stop the registry from knowing the others.

_META: Dict[str, Any] = {}


def _discover_meta() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    for m in pkgutil.iter_modules([here]):
        if not m.ispkg or m.name in _META:
            continue
        path = os.path.join(here, m.name, "meta.py")
        if not os.path.exists(path):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"lingualens_meta_{m.name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception:  # a broken meta.py hides that course, not the others
            continue
        _META[m.name] = mod


_discover_meta()


def meta(lang: str):
    """The language's meta module, or None."""
    return _META.get(normalize(lang))


def meta_get(lang: str, attr: str, default: Any = None) -> Any:
    m = meta(lang)
    value = getattr(m, attr, None) if m else None
    return default if value is None else value


LANG_NAMES: Dict[str, str] = {code: getattr(m, "NAME", code) for code, m in _META.items()}

_ALIASES: Dict[str, str] = {}
for _code, _m in _META.items():
    for _alias in getattr(_m, "ALIASES", ()) or ():
        _ALIASES[str(_alias).strip().lower()] = _code


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
    return _ALIASES.get(key, DEFAULT_LANG)


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


#: languages written with spaces between words (meta.TOKENS == "spaced").
#: Every "which characters carry meaning" heuristic in the engine was built
#: for 汉字 and かな, where one character is a unit of meaning; for these, a
#: word is the unit instead. Languages without spaces (zh, ja, th) are "char".
SPACED = {code for code, m in _META.items() if getattr(m, "TOKENS", "char") == "spaced"}


def is_spaced(lang: str) -> bool:
    return normalize(lang) in SPACED


def words(text: str) -> List[str]:
    """Lower-cased words of a space-delimited line, in any script.

    Splits on whitespace and drops punctuation, symbols and digits, but keeps
    combining marks: a regex on \\w breaks Devanagari and Arabic words apart
    at every vowel sign, which is the letter-by-letter matching this is here
    to avoid.
    """
    out: List[str] = []
    for raw in (text or "").casefold().split():
        w = "".join(ch for ch in raw
                    if not unicodedata.category(ch)[0] in ("P", "S", "Z")
                    and not unicodedata.category(ch) == "Nd")
        if w:
            out.append(w)
    return out


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
    found = meta_get(lang, "BAND_LABEL")
    if found:
        return found
    label = getattr(package_for(lang), "LABEL", None)
    return label or "Level"


def native_label(lang: str) -> str:
    """The course in its own language: 中文 / 日本語 / Español."""
    return meta_get(lang, "NATIVE") or LANG_NAMES.get(normalize(lang), lang)


__all__ = [
    "DEFAULT_LANG", "LANG_NAMES", "SPACED", "is_spaced", "words", "meta", "meta_get", "supported", "normalize", "package_for", "module_for",
    "course_data", "scenes", "speech_lang", "band_label", "native_label", "zh", "ja", "es",
]
