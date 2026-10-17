"""Course registry: one server, many courses, loaded lazily and safely.

The same LinguaLens process can teach Mandarin and Japanese side by side.
A course package may be half-written while the agent that authors it is
still working; that must never stop the other course from running. This
module is the single point that decides what is "ready", caches successful
imports, and produces the descriptors the web app uses to render the
switcher and the progress screens.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from . import course as course_pkg
from .config import course_config, default_course, enabled_courses
from .curriculum import Course


class CourseNotReady(Exception):
    """Raised when the caller asks for a course whose package failed to import."""


class Registry:
    """Lazily builds one `Course` per language, caches the good ones.

    The first time you ask for a course, the import runs. A broken package
    raises `CourseNotReady` and is recorded so the next call returns the
    same error in O(1) until the server is restarted. This makes the
    "Japanese coming soon" path a feature, not a crash.
    """

    #: how long a failed import is remembered before we try again. A course is
    #: authored by hand, so "broken right now" often means "fixed in a minute".
    RETRY_AFTER = 30.0

    def __init__(self, cfg: Dict[str, Any]) -> None:
        self.cfg = cfg
        self._lock = threading.Lock()
        self._courses: Dict[str, Course] = {}
        self._errors: Dict[str, str] = {}
        self._failed_at: Dict[str, float] = {}
        self._cfgs: Dict[str, Dict[str, Any]] = {}
        # Probe everything at boot so the menu knows what is available.
        for lang in enabled_courses(cfg):
            try:
                self._load(lang)
            except Exception:
                pass  # the error is cached and surfaced by `describe()`

    # -- internal ------------------------------------------------------------
    def _load(self, lang: str) -> Course:
        lang = course_pkg.normalize(lang)
        with self._lock:
            if lang in self._courses:
                return self._courses[lang]
            if lang in self._errors and time.time() - self._failed_at.get(lang, 0.0) < self.RETRY_AFTER:
                raise CourseNotReady(self._errors[lang])
            try:
                course = Course(lang)
            except Exception as exc:
                msg = f"{type(exc).__name__}: {exc}".splitlines()[0][:200]
                self._errors[lang] = msg
                self._failed_at[lang] = time.time()
                raise CourseNotReady(msg) from exc
            self._errors.pop(lang, None)
            self._failed_at.pop(lang, None)
            self._courses[lang] = course
            self._cfgs[lang] = course_config(self.cfg, lang)
            return course

    # -- public --------------------------------------------------------------
    def get(self, lang: str) -> Course:
        return self._load(lang)

    def config_for(self, lang: str) -> Dict[str, Any]:
        """The merged config a `Session` should use for this course."""
        self._load(lang)  # ensure cached + surfaces the error if broken
        return self._cfgs[lang]

    def provider_for(self, lang: str, resolver):
        """Resolve a pronunciation provider using the course's own config."""
        return resolver(self.config_for(lang))

    def ready(self, lang: str) -> bool:
        lang = course_pkg.normalize(lang)
        return lang in self._courses

    def error(self, lang: str) -> Optional[str]:
        return self._errors.get(course_pkg.normalize(lang))

    def languages(self) -> List[str]:
        """Every course the operator enabled, in menu order."""
        return enabled_courses(self.cfg)

    def default_lang(self) -> str:
        return default_course(self.cfg)

    def describe(self, lang: str) -> Dict[str, Any]:
        """One row for the course switcher / progress screen."""
        lang = course_pkg.normalize(lang)
        native = course_pkg.native_label(lang)
        name = course_pkg.LANG_NAMES.get(lang, lang)
        if not self.ready(lang):
            return {
                "id": lang,
                "name": name,
                "native": native,
                "ready": False,
                "error": self._errors.get(lang, "not loaded"),
                "lessons": 0, "vocab": 0, "prompts": 0,
                "speech_lang": None,
            }
        c = self._courses[lang]
        return {
            "id": lang,
            "name": name,
            "native": native,
            "ready": True,
            "lessons": len(c.lesson_ids),
            "vocab": c.vocab_count(),
            "prompts": c.prompt_count(),
            "speech_lang": c.speech_lang,
            "band_label": course_pkg.band_label(lang),
        }

    def all(self) -> List[Dict[str, Any]]:
        return [self.describe(lang) for lang in self.languages()]

    # -- lifecycle -----------------------------------------------------------
    def invalidate(self, lang: Optional[str] = None) -> None:
        """Drop a cached course so the next call re-imports it.

        Useful in tests and after an authoring change.
        """
        with self._lock:
            targets = [course_pkg.normalize(lang)] if lang else list(self._courses)
            for k in targets:
                self._courses.pop(k, None)
                self._cfgs.pop(k, None)
                self._errors.pop(k, None)
                self._failed_at.pop(k, None)
