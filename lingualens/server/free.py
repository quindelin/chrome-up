"""Free response: grading an answer nobody wrote in advance.

Repetition can be graded against a known line. This cannot. The audio is
transcribed first (`asr.py`), then:

  1. did you answer rather than repeat the question?
  2. did you say enough to count as a sentence?
  3. did you actually use the point of the question? (keywords from the lesson)
  4. was it intelligible? - the normal gate, eased a little, because
     composing your own sentence while speaking it is much harder than
     repeating one you have just heard.
  5. and, when an LLM is configured: is the answer actually *right*?

Step 5 is what steps 1-4 cannot do. Relevance is currently decided by
character overlap, which means sharing one or two characters with the
question counts as answering it. At HSK 5-6 that is not good enough: a
question like 你怎么看信息过载 can be "passed" with any answer containing
平台 and 责任, whatever it actually said, and the learner is told "good".
The overlap check stays as a fast pre-filter with no network; the LLM is
asked to judge grammar, whether it answers the question, and register.

It fails open. A missing key, a slow network or a malformed reply must never
block a learner who has actually answered - so every failure path returns
None and the deterministic grading stands.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from .course import LANG_NAMES, normalize
from .curriculum import content_chars
from .models import Score
from .pronunciation import coverage_of, evaluate, normalize_text

# keys the gate uses that we relax for free speech
_RELIEVED = ("min_pron_score", "min_accuracy", "min_completeness", "min_tone_score",
             "min_phone_score")

# The LLM is asked for this; a missing key or a dead network is not an error.
_GRADER_SYSTEM = {
    "zh": (
        "You are grading a spoken answer in Mandarin for a language learner. "
        "You are given the question and the learner's answer as transcribed by "
        "speech recognition, so minor transcription errors are not the learner's "
        "fault - judge the language, not the ASR.\n"
        "Decide: (a) does it actually answer the question, (b) is the grammar "
        "acceptable Mandarin, (c) is the register right - it should be spoken "
        "Chinese, not written Chinese, unless the question is formal.\n"
        "Be strict on grammar and on actually answering the question. Be lenient "
        "on missing particles and on anything the transcriber may have dropped.\n"
        "Reply with JSON only: {\"ok\": true|false, \"reason\": one short sentence "
        "in English, \"better\": a corrected version in simplified Chinese}. "
        "If it is acceptable, \"reason\" is empty and \"better\" is empty."
    ),
    "ja": (
        "You are grading a spoken answer in Japanese for a language learner. "
        "You are given the question and the learner's answer as transcribed by "
        "speech recognition, so minor transcription errors are not the learner's "
        "fault - judge the language, not the ASR.\n"
        "Decide: (a) does it actually answer the question, (b) is the grammar "
        "acceptable Japanese, (c) is the register right - です/ます for ordinary "
        "polite speech, not written or literary forms.\n"
        "Be strict on grammar and on actually answering the question. Be lenient "
        "on missing particles and on anything the transcriber may have dropped.\n"
        "Reply with JSON only: {\"ok\": true|false, \"reason\": one short sentence "
        "in English, \"better\": a corrected version in Japanese}. "
        "If it is acceptable, \"reason\" is empty and \"better\" is empty."
    ),
}


def llm_check(
    question: str,
    sample: str,
    said: str,
    band: int,
    cfg: Dict,
    lang: str = "zh",
    rubric: str = "",
) -> Tuple[Optional[bool], str]:
    """Ask a model whether the answer is actually a correct answer.

    Returns (None, "") when it cannot be asked - no key, no config, wrong
    band, network down, unparseable reply - so the caller falls back to the
    deterministic grading rather than punishing the learner for our outage.
    """
    free_cfg = cfg.get("free") or {}
    if not free_cfg.get("llm_check", True):
        return None, ""
    if int(band or 0) < int(free_cfg.get("llm_min_band", 4) or 4):
        return None, ""

    think_cfg = cfg.get("think") or {}
    key_env = think_cfg.get("api_key_env") or "OPENAI_API_KEY"
    key = os.getenv(key_env) if key_env else None
    if not key:
        return None, ""

    lang = normalize(lang)
    name = LANG_NAMES.get(lang, lang)
    # the model answer is a reference, not a required wording - say so, or the
    # grader marks a perfectly good answer wrong for not being this one
    user = (
        f"Question ({name}): {question}\n"
        f"Model answer (one possible answer, not the required wording): {sample}\n"
        f"Learner's answer (ASR): {said}\n"
        f"Level: HSK {band} (1 lowest, 6 highest)."
    )
    if rubric:
        user += f"\n{rubric}"
    payload = {
        "model": think_cfg.get("model", "gpt-4o-mini"),
        "temperature": 0.0,
        "max_tokens": 200,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": _GRADER_SYSTEM.get(lang, _GRADER_SYSTEM["zh"])},
            {"role": "user", "content": user},
        ],
    }
    base = (think_cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            req, timeout=float(free_cfg.get("llm_timeout", 10) or 10)
        ) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None, ""
    try:
        data = json.loads(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, ValueError):
        return None, ""

    ok = data.get("ok")
    if not isinstance(ok, bool):
        return None, ""
    reason = (data.get("reason") or "").strip()
    better = (data.get("better") or "").strip()
    if not ok:
        parts = [reason or "That isn't quite right."]
        if better:
            parts.append(f"Try: {better}")
        return False, " ".join(parts)
    return True, ""


def grade(
    score: Score,
    step,
    gate: Dict,
    cfg: Dict,
    lang: str = "zh",
    band: int = 0,
) -> Tuple[bool, List[str]]:
    """(passed, reasons) for one free-form answer."""
    free_cfg = cfg.get("free") or {}
    said = (score.recognized or "").strip()

    if score.error:
        return False, [score.error]
    if not said:
        return False, ["I couldn't make out an answer - say it again."]

    said_n = normalize_text(said)
    asked_n = normalize_text(step.text)

    # 1. echoing the question is not an answer
    if asked_n and coverage_of(asked_n, said_n) > 0.85 and len(said_n) <= len(asked_n) + 2:
        return False, ["You repeated the question - answer it."]

    # 2. long enough to count
    min_chars = int(step.min_chars or free_cfg.get("min_chars", 0) or 0)
    if min_chars and len(said_n) < min_chars:
        return False, [f"Too short - answer in a full sentence ({min_chars}+ characters)."]

    # 3. is it an answer to *this* question?
    #     Shared meaning-carrying characters, not exact words.
    if free_cfg.get("require_relevance", True):
        asked = content_chars(step.text, lang)
        sample = content_chars(getattr(step, "sample_text", "") or "", lang)
        answered = content_chars(said, lang)
        need = 1 if len(asked) <= 6 else 2
        on_topic = len(asked & answered) >= need
        like_model = bool(sample) and len(sample & answered) >= need
        generous = bool(min_chars) and len(said_n) >= 2 * min_chars
        if asked and not (on_topic or like_model or generous):
            hint = " / ".join((getattr(step, "keywords", []) or [])[:2])
            return False, [
                "That doesn't answer the question"
                + (f" - try to use {hint}" if hint else " - listen again")
            ]

    # 4. pronunciation, eased
    soft = dict(gate)
    relief = float(free_cfg.get("gate_relief", 6.0) or 0.0)
    for key in _RELIEVED:
        if soft.get(key):
            soft[key] = max(0.0, float(soft[key]) - relief)
    soft["require_recognized_match"] = False
    soft["min_reference_coverage"] = 0.0

    passed, reasons = evaluate(score, soft)
    reasons = list(reasons)

    # 5. and is it actually right? Only asked once everything else has passed,
    #    and only from the band where "roughly the right characters" stops
    #    being good enough. Fails open - see llm_check.
    if passed:
        ok, comment = llm_check(
            step.text,
            getattr(step, "sample_text", "") or "",
            said,
            band,
            cfg,
            lang,
        )
        if ok is False and comment:
            return False, [comment]

    if passed:
        reasons.insert(0, f"Good - you said: {said}")
    elif not reasons:
        reasons.append("Try again - say the whole answer.")
    return passed, reasons


def grade_writing(
    score: Score, step, gate: Dict, cfg: Dict, lang: str = "zh", band: int = 0
) -> Tuple[bool, List[str]]:
    """(passed, reasons) for a 缩写 - a summary of a passage just read.

    Different from `grade` in the one way that matters: there is no correct
    wording, so nothing is checked against a reference and the relevance
    check is wrong for it. What is graded is whether the key points survived
    the shortening - a summary that is fluent and grammatical and leaves out
    the point has failed, and character overlap with the prompt would never
    notice that.
    """
    free_cfg = cfg.get("free") or {}
    write_cfg = cfg.get("writing") or {}

    if score.error:
        return False, [str(score.error)]
    said = normalize_text(score.recognized or "")
    if not said:
        return False, ["I couldn't make out a summary - say it again."]

    # A one-line summary is not a summary. The exam asks for a third of the
    # original; a clause and a half means the point was not kept.
    min_chars = int(getattr(step, "min_chars", 0)
                    or write_cfg.get("min_chars", 0) or 0)
    if min_chars and len(said) < min_chars:
        return False, [
            f"Too short to be a summary ({min_chars}+ characters) - say what "
            "the passage was about, not just its subject."
        ]

    soft = dict(gate)
    relief = float(free_cfg.get("gate_relief", 6.0) or 0.0)
    for key in _RELIEVED:
        if key in soft:
            soft[key] = max(0.0, float(soft[key]) - relief)

    passed, reasons = evaluate(score, soft)
    reasons = list(reasons)

    if passed:
        # coverage, not wording: the points the summary has to keep
        keywords = list(getattr(step, "keywords", []) or [])
        need = max(1, (len(keywords) + 1) // 2)
        if keywords:
            kept = [k for k in keywords if k in said]
            if len(kept) < need:
                missing = [k for k in keywords if k not in kept]
                return False, [
                    f"You left out the point: {', '.join(missing[:2])}. "
                    "A summary has to keep it even when it drops everything else."
                ]

    if passed:
        ok, comment = llm_check(
            step.text,
            getattr(step, "sample_text", "") or "",
            said,
            band,
            cfg,
            lang,
            # a summary is graded on what it kept, not on how it says it
            "This is a 缩写 - a summary of a longer text. Judge whether the key "
            "points survived the shortening, not whether the wording matches. Do "
            "not require it to be short to the point of dropping the point.",
        )
        if ok is False and comment:
            return False, [comment]

    if passed:
        reasons.insert(0, f"Good - you said: {said}")
    elif not reasons:
        reasons.append("Try again - say the whole summary.")
    return passed, reasons
