#!/usr/bin/env python3
"""The gate a course has to pass before it is merged.

    .venv/bin/python tools/validate_course.py fr          # one course
    .venv/bin/python tools/validate_course.py --all       # every course on disk

Every rule here is something a real course got wrong at least once (see
docs/COURSE_AUDIT.md, docs/SPANISH_AUDIT.md, docs/LEARNING_SCIENCE.md).
Exit status 0 = ready to merge. Warnings are reported but do not fail.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server import course as course_pkg  # noqa: E402
from server.config import load_config  # noqa: E402
from server.curriculum import Course  # noqa: E402
from server.engine import Session, inject_count  # noqa: E402
from server.main import default_config  # noqa: E402

REQUIRED_META = ("CODE", "NAME", "NATIVE", "ALIASES", "BAND_LABEL", "TOKENS", "SPEECH_LANG")
NEW_COURSE_META = ("GRADER_PROMPT", "THINK_PROMPT", "UI", "NOTES", "DEFAULTS")
HEARD = ("listen", "speak", "read", "hanzi", "kanji", "kana", "answer", "hear", "converse")


def validate(code: str, strict: bool) -> tuple:
    errors, warnings = [], []
    err, warn = errors.append, warnings.append

    # -- meta.py -----------------------------------------------------------
    m = course_pkg.meta(code)
    if m is None or course_pkg.normalize(code) != code:
        return [f"no server/course/{code}/meta.py (or it failed to load)"], []
    for f in REQUIRED_META:
        if getattr(m, f, None) in (None, "", []):
            err(f"meta.py: {f} missing")
    if getattr(m, "CODE", code) != code:
        err(f"meta.py: CODE is {m.CODE!r}, folder is {code!r}")
    if getattr(m, "TOKENS", "") not in ("spaced", "char"):
        err("meta.py: TOKENS must be 'spaced' or 'char'")
    for f in NEW_COURSE_META:
        if not getattr(m, f, None):
            (err if strict else warn)(f"meta.py: {f} missing (see docs/NEW_COURSE.md)")
    if course_pkg.is_spaced(code) and not getattr(m, "FUNCTION_WORDS", None):
        (err if strict else warn)("meta.py: FUNCTION_WORDS missing - answer relevance will be weak")

    # -- config ------------------------------------------------------------
    cfg_name = default_config(code)
    if code != "zh" and cfg_name == "config.yaml":
        err(f"config.{code}.yaml missing")
    cfg = load_config(ROOT / cfg_name)
    if cfg.get("language") != code:
        err(f"{cfg_name}: language is {cfg.get('language')!r}, want {code!r}")

    # -- the course loads ----------------------------------------------------
    try:
        c = Course(code)
    except Exception as exc:  # noqa: BLE001
        return errors + [f"course does not load: {type(exc).__name__}: {exc}"], warnings
    if not c.levels:
        err("no LEVELS")
    if c.lesson_ids != list(range(1, len(c.lesson_ids) + 1)):
        err("lesson ids are not 1..N without gaps")
    if c.duplicate_words:
        err(f"{len(c.duplicate_words)} words in two topics, e.g. {c.duplicate_words[:3]}")

    grammar = course_pkg.module_for(code, "grammar")
    readings = course_pkg.module_for(code, "readings")
    if readings and hasattr(readings, "check"):
        for p in (readings.check() or [])[:5]:
            err(f"readings: {p}")

    lesson_words = {v.text for l in c.lessons.values() for v in l.vocab}
    for lid in c.lesson_ids:
        l = c.lessons[lid]
        where = f"L{lid}"
        if len(l.patterns) < 2 or any(not p.kind for p in l.patterns):
            err(f"{where}: needs 2+ drill patterns, each with a kind")
        if any("{x}" not in p.text for p in l.patterns):
            err(f"{where}: a pattern has no {{x}} slot")
        if sum(1 for t in l.dialogue if t.speaker == "you") < 3:
            err(f"{where}: fewer than 3 learner lines")
        if len(l.prompts) < 2:
            err(f"{where}: fewer than 2 free-response prompts")
        if not l.scene:
            err(f"{where}: no scene")
        if grammar and hasattr(grammar, "for_lesson") and not grammar.for_lesson(lid):
            err(f"{where}: no grammar page")
        if readings and hasattr(readings, "get"):
            if len((readings.get(lid) or {}).get("questions") or []) < 2:
                err(f"{where}: passage needs a read and a listen question")
        if any("+" in v.text for v in l.vocab):
            err(f"{where}: a vocab item is a formula, not something you can say")
        if any(t.speaker == "them" and t.text.startswith("(") for t in l.dialogue):
            err(f"{where}: a stage direction would be read aloud")

        # the running lesson: state, glasses card, hear-it-first
        try:
            s = Session(c, cfg, {"lesson_id": lid, "completed": [], "mastery": {},
                                 "words": {}, "stats": {}})
            heard = set()
            for i, st in enumerate(s.steps):
                if st.kind == "recall" and not st.prior and s._units(st.text) - heard:
                    err(f"{where}: asks for '{st.text}' before it was heard")
                    break
                if st.kind in HEARD:
                    heard |= s._units(st.text or getattr(st, "audio_text", "") or "")
            for i in range(len(s.steps)):
                s.pos, s.attempts = i, 0
                card = s.state()["glasses"]
                if not card["target"].strip():
                    err(f"{where} step {i} ({s.steps[i].kind}): blank glasses card")
                    break
        except Exception as exc:  # noqa: BLE001
            err(f"{where}: session fails: {type(exc).__name__}: {exc}")

    # -- every bank word is reached, once, inside a lesson ---------------------
    vocab_cfg = cfg.get("vocab") or {}
    for band in c.vocab_by_band:
        per = inject_count(vocab_cfg, band)
        got = [w.text for l in c.lessons_of_band(band) for w in c.vocab_for_lesson(l, per)]
        bank = len(c.vocab_words(band))
        if bank and (len(set(got)) != bank or len(got) != bank):
            err(f"band {band}: bank {bank} words, lessons reach {len(set(got))} "
                f"({len(got)} injections) - size the bank to lessons x inject_by_band")
        overlap = [w for w in got if w in lesson_words]
        if overlap:
            err(f"band {band}: bank repeats lesson vocab, e.g. {overlap[:3]}")
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("code", nargs="?", help="course folder, e.g. fr")
    ap.add_argument("--all", action="store_true", help="every course on disk")
    ap.add_argument("--lenient", action="store_true",
                    help="treat new-course meta fields as warnings (for zh / ja)")
    args = ap.parse_args()
    codes = course_pkg.supported() if args.all else [args.code]
    if not codes or not codes[0]:
        ap.error("give a course code or --all")
    failed = 0
    for code in codes:
        strict = not args.lenient and code not in ("zh", "ja")
        errors, warnings = validate(code, strict)
        mark = "PASS" if not errors else "FAIL"
        print(f"{mark} {code}: {len(errors)} errors, {len(warnings)} warnings")
        for e in errors[:40]:
            print(f"   x {e}")
        if len(errors) > 40:
            print(f"   … {len(errors) - 40} more")
        for w in warnings[:10]:
            print(f"   ! {w}")
        failed += bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
