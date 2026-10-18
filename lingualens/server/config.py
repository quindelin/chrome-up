"""Config loading with deep-merged defaults + environment secrets.

One codebase, two courses. `language: zh | ja` picks which course package is
loaded (see `server/course/`), and `LANG_DEFAULTS` below supplies the
language-specific pronunciation engine, gate floor and reading ladder.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .course import DEFAULT_LANG, LANG_NAMES, normalize, supported

DEFAULTS: Dict[str, Any] = {
    "language": "zh",   # zh = Mandarin (HSK 1-6) | ja = Japanese (JLPT N5-N1) | es = Spanish (CEFR)
    # One server can teach several courses at once and keeps their progress
    # apart. Empty list = every course package that loads.
    "courses": {"enabled": [], "default": None},
    "server": {"host": "0.0.0.0", "port": 8899},
    "pronunciation": {
        "provider": "auto",   # auto | iflytek | azure | mock
        "prefer": "iflytek",  # which engine auto picks first
        "language": "zh-CN",
        "region": None,
        "key": None,
        "key_env": "AZURE_SPEECH_KEY",
        "region_env": "AZURE_SPEECH_REGION",
        "enable_miscue": True,
        # azure granularity: phoneme needs a locale that supports it. If the
        # service rejects it, set this to word.
        "granularity": "phoneme",
        "phoneme_nbest": 0,
        "iflytek": {
            "endpoint": "https://ise-api.xfyun.cn/v2/ise",
            "iat_endpoint": "https://iat-api.xfyun.cn/v2/iat",
            "appid_env": "IFLYTEK_APPID",
            "apikey_env": "IFLYTEK_API_KEY",
            "apisecret_env": "IFLYTEK_API_SECRET",
            "language": "zh_cn",
            "category": "auto",
            "result_level": "entirety",
            "extra_ability": "multi_dimension",
            "timeout": 20,
        },
    },
    # base values are the easiest band's floor; each band tightens them
    "gate": {
        "min_pron_score": 60.0,
        "min_accuracy": 60.0,
        "min_completeness": 75.0,
        # suprasegmental score: 声调 (zh) / 高低アクセント (ja). Only enforced
        # when the provider actually reports one.
        "min_tone_score": 58.0,
        "min_phone_score": 0.0,
        "require_recognized_match": True,
        "min_reference_coverage": 0.75,
        "max_attempts": 0,
        "reveal_after_attempts": 2,
        "slow_replay_after_attempts": 2,
    },
    "think": {
        "provider": "auto",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "timeout": 12,
    },
    "audio": {
        "target_sample_rate": 16000,
        "min_seconds": 0.4,
        "max_seconds": 15.0,
        "noise_gate_rms": 0.005,
        # seconds of speech expected per character of reference text - the mock
        # scorer uses it to tell a rushed line from a full one
        "seconds_per_char": 0.32,
    },
    # Pimsleur "graduated interval recall": same item comes back at growing gaps.
    # anticipation_seconds is a different thing and is Pimsleur's "principle of
    # anticipation": the silent pause at the top of a recall item, BEFORE the
    # English cue appears. You try to retrieve with nothing on the screen; if
    # you draw a blank the English arrives and rescues you. 0 = cue at once.
    "recall": {"intervals": [10, 30, 75], "rounds": 3, "anticipation_seconds": 5.0},
    # --- literacy -----------------------------------------------------------
    # Japanese is the one major language you cannot read without being taught
    # the writing system explicitly: two 46-character syllabaries get you
    # started, but the kanji stand between a learner and every sign, menu,
    # article and book. Without this module the course produces a learner who
    # can speak and can read nothing, which cuts them off from the input that
    # fluency depends on.
    "kana": {
        "enabled": True,
        "per_lesson": 5,      # kana drilled alongside the early lessons
        "through_lesson": 8,  # stop once both syllabaries have been seen
    },
    "kanji": {
        "enabled": True,
        "per_lesson": 3,         # kanji drawn from the lesson's own vocabulary
        "recall_in_session": 2,  # how often a kanji returns inside one lesson
    },
    # Mandarin's counterpart. There is no syllabary to teach, so this was
    # never written - and it turned out to matter more, not less: pinyin only
    # ever builds sound -> meaning, so the moment it is faded out the learner
    # has nothing under them, and HSK 5-6 is mostly a reading exam.
    "hanzi": {
        "enabled": True,
        "per_lesson": 3,          # characters drawn from the lesson's vocabulary
        "recognition": True,      # drill character -> pinyin + meaning as well
    },
    # --- reading ------------------------------------------------------------
    # 7,500 characters of dialogue across 73 lessons is a skeleton, not a
    # corpus. Passages are the cheapest way to put real volume in front of a
    # learner: the only place in the course where the language arrives in
    # paragraphs rather than in isolated sentences.
    "reading": {
        "enabled": True,
        "per_lesson": 1,
        "read_aloud": True,     # gate the passage on reading it out loud
        "comprehension": True,  # follow it with a question about the text
    },
    # --- listening ----------------------------------------------------------
    # Everything a learner hears is synthesised in the browser, by whichever
    # voice happens to match the language first. Real listening means several
    # voices, at something closer to natural speed.
    "listening": {
        "enabled": True,
        "rotate_voices": True,  # cycle every available voice, not just the first
        "vary_pitch": True,     # a different speaker, not merely a slower one
        "rate": {"model": 0.95, "slow": 0.6, "listen": 1.0, "drill": 0.85},
        # Every line in a lesson is printed while it is spoken, so nothing in
        # the course is actually listening practice. `comprehension` adds one
        # audio-only step per lesson: the line plays with a blank screen and
        # the question afterwards can only be answered from the audio.
        "comprehension": True,
    },
    "storage": {"path": "state.json"},
    "ui": {
        "show_english_default": False,
        "display_size": 600,
        # The reading line (pinyin / kana) is a crutch: with it always on you
        # never really read the characters. mode:
        #   auto   -> use reading_by_level (recommended)
        #   always -> reading on every line
        #   fade   -> reading when a line is taught, hidden when retrieved
        #   reveal -> hidden until you have failed twice
        #   never  -> characters only
        "reading_mode": "auto",
        # 7 is "never": by HSK 7-9 the pinyin has outlived its use. A romanised
        # line above real text is a second text to read, and it teaches the eye
        # to go to the wrong one - you stop reading 鉴于 and read jiàn yú.
        "reading_by_level": {1: "always", 2: "always", 3: "fade", 4: "fade", 5: "reveal", 6: "reveal", 7: "never"},
        # The English scene printed before a conversation. It is a signpost, so
        # it fades the same way the reading line does - by the top bands you
        # should be able to work out where you are from the first line:
        #   auto   -> use scene_by_level (recommended)
        #   always -> every lesson opens with its scene
        #   first  -> only the first lesson of each unit
        #   tip    -> never shown; one press of the tip key reveals it
        #   never  -> no scene at all
        "scene_mode": "auto",
        "scene_by_level": {1: "always", 2: "always", 3: "first", 4: "first", 5: "tip", 6: "tip", 7: "tip"},
        "scene_seconds": 6.0,   # how long it stays up; a tap skips it
        "vocab_label": "词汇",
    },
    "vocab": {
        "enabled": True,
        "inject_per_lesson": 4,   # new words folded into every lesson
        "recall_rounds": 2,       # rounds inside a dedicated vocab session
    },
    "free": {
        "enabled": True,
        "per_lesson": 2,
        "require_keywords": True,
        "min_chars": 0,           # 0 = derive from the sample answer
        "gate_relief": 6.0,       # free speech is harder; ease the gate
        "require_relevance": True,
        "asr": "auto",            # auto | client | iflytek | azure | mock
        # Relevance is decided by character overlap, which is a pre-filter and
        # nothing more: sharing one character with the question counts as
        # answering it. From HSK 4 up the answer is also sent to the model -
        # does it answer the question, is the grammar right, is the register
        # right. Uses the same key as `think`; with no key it is simply off,
        # and any network failure falls back to the overlap check rather than
        # blocking a learner who has actually answered.
        "llm_check": True,
        "llm_min_band": 4,
        "llm_timeout": 10,
    },
    # --- writing ------------------------------------------------------------
    # HSK 6 写作 is a 缩写: read a long text, produce a short one, in ten
    # minutes. The skill is deciding what to drop while keeping the point,
    # and that is exactly as hard spoken as written - which is the only form
    # of it that fits a course you use with your voice. Typing is not
    # offered: there is no keyboard on a pair of glasses, and handwriting
    # recognition would be a different product.
    # Graded on coverage of the passage's key points, not on wording. Needs
    # the same key as `think` for the full check; without one, coverage of
    # the keywords alone decides it.
    "writing": {
        "enabled": True,
        "min_band": 6,     # below HSK 6 a summary is not worth asking for
        "min_chars": 30,
    },
    # --- fluency ------------------------------------------------------------
    # Every gate key is segmental accuracy on a line you were given: did you
    # pronounce it. HSK 5-6 speaking is a rate-and-repair problem, not a
    # pronunciation problem - the tones are fine by then and the answer still
    # sounds foreign because of the pauses. So: how fast, and how much of it
    # was filler. Both are derived from the timing the score already carries,
    # so no new audio handling is needed. Off by default until tuned against
    # real recordings; `min_chars_per_second: 0` disables either half.
    "fluency": {
        "enabled": False,
        "min_chars_per_second": 2.0,  # chars of the reference per second spoken
        "max_filler_ratio": 0.20,     # 那个/嗯/就是… as a share of what you said
        "min_band": 5,                # below this, fluency is not graded
    },
}

# ---- what actually differs between the two courses -------------------------
LANG_DEFAULTS: Dict[str, Any] = {
    "zh": {
        "pronunciation": {
            "prefer": "iflytek",
            "language": "zh-CN",
            "iflytek": {"language": "zh_cn"},
        },
        "gate": {"min_tone_score": 58.0},
        "ui": {
            # 7 is "never": by HSK 7-9 the pinyin has outlived its use. A
            # romanised line above real text is a second text to read, and it
            # teaches the eye to go to the wrong one - you stop reading 鉴于
            # and read jiàn yú instead.
            "reading_by_level": {1: "always", 2: "always", 3: "fade", 4: "fade", 5: "reveal", 6: "reveal", 7: "never"},
            "scene_by_level": {1: "always", 2: "always", 3: "first", 4: "first", 5: "tip", 6: "tip", 7: "tip"},
            "vocab_label": "词汇",
        },
        "audio": {"seconds_per_char": 0.32},
        # Hanzi are the Chinese reading problem: there is no syllabary to fall
        # back on, so a character either is known or the line is opaque.
        "hanzi": {"per_lesson": 3, "recognition": True},
        "reading": {"per_lesson": 1, "read_aloud": True, "comprehension": True},
        "storage": {"path": "state.json"},
    },
    "ja": {
        "pronunciation": {
            "prefer": "azure",
            "language": "ja-JP",
            "iflytek": {"language": "ja_jp"},
        },
        "gate": {"min_tone_score": 58.0},
        "ui": {
            # kanji is a much bigger reading problem than hanzi, so the kana
            # crutch survives one band longer than pinyin does
            "reading_by_level": {1: "always", 2: "always", 3: "always", 4: "fade", 5: "fade", 6: "reveal"},
            # and for the same reason the English scene survives one band
            # longer too: at N3 you still cannot guess the setting from one
            # spoken line
            "scene_by_level": {1: "always", 2: "always", 3: "always", 4: "first", 5: "first", 6: "tip"},
            "vocab_label": "単語",
        },
        "audio": {"seconds_per_char": 0.16},
        # Literacy is a Japanese problem in a way it is not a Chinese one:
        # the syllabaries have to be taught outright, and a kanji is worth
        # drilling on its own terms rather than only as part of a word.
        "kana": {"per_lesson": 5, "through_lesson": 8},
        "kanji": {"per_lesson": 3},
        # Reading matters more here too: the jump from a spoken line to a
        # newspaper is wider, so passages start early and stay.
        "reading": {"per_lesson": 1, "read_aloud": True, "comprehension": True},
        "storage": {"path": "state.ja.json"},
    },
    "es": {
        "pronunciation": {
            "prefer": "azure",
            # The course lines are Peninsular (billete, zumo, ¿qué le pongo?),
            # so the scorer and the voice are too. es-MX scores the same
            # lines fine - set it in config.es.yaml for a Latin American voice.
            "language": "es-ES",
            # iFlytek ISE has no Spanish evaluation. Without this, `auto`
            # with Chinese keys in the environment scores Spanish as Chinese.
            "iflytek": {"enabled": False},
        },
        # Spanish has no lexical tone; nothing reports one, so leave it off.
        "gate": {"min_tone_score": 0.0},
        "ui": {
            # The line is already phonetic: there is no second script to fall
            # back on, so the reading slot is used only for stress/linking
            # hints on the odd hard line and is otherwise empty.
            "reading_by_level": {1: "always", 2: "fade", 3: "reveal", 4: "never",
                                 5: "never", 6: "never"},
            "scene_by_level": {1: "always", 2: "always", 3: "first", 4: "first",
                               5: "tip", 6: "tip"},
            "vocab_label": "Vocabulario",
        },
        # ~12 letters/s in natural speech, vs ~3 kana/s
        "audio": {"seconds_per_char": 0.075},
        # Bands count up here (1 = A1 ... 6 = C2): spoken summaries from C1,
        # fluency from B2. The rate is letters a second with the spaces
        # gone, so it is about four times the Mandarin number.
        "writing": {"min_band": 5, "min_chars": 80},
        "fluency": {"min_chars_per_second": 9.0, "min_band": 4},
        "reading": {"per_lesson": 1, "read_aloud": True, "comprehension": True},
        "storage": {"path": "state.es.json"},
    },
}


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path = "config.yaml") -> Dict[str, Any]:
    raw: Dict[str, Any] = {}
    p = Path(path)
    if p.exists():
        with p.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

    lang = normalize(raw.get("language") or DEFAULTS["language"])
    cfg = _merge(_merge(DEFAULTS, LANG_DEFAULTS.get(lang, {})), raw)
    cfg["language"] = lang
    cfg["language_name"] = LANG_NAMES.get(lang, lang)

    # secrets come from the environment, never from the yaml file
    pron = cfg["pronunciation"]
    if not pron.get("key") and pron.get("key_env"):
        pron["key"] = os.getenv(pron["key_env"]) or None
    if not pron.get("region") and pron.get("region_env"):
        pron["region"] = os.getenv(pron["region_env"]) or None

    ise = pron.setdefault("iflytek", {})
    ise["appid"] = os.getenv(ise.get("appid_env") or "IFLYTEK_APPID") or None
    ise["apikey"] = os.getenv(ise.get("apikey_env") or "IFLYTEK_API_KEY") or None
    ise["apisecret"] = os.getenv(ise.get("apisecret_env") or "IFLYTEK_API_SECRET") or None
    return cfg


def course_config(cfg: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """The config as seen by one course.

    Everything that is language-specific (speech locale, gate floor, reading
    ladder, pacing) comes from LANG_DEFAULTS; everything else (keys, ports,
    authoring knobs) is whatever the operator wrote. One shared storage file
    holds every course's progress, so switching language never loses anything.
    """
    key = normalize(lang)
    out = _merge(cfg, LANG_DEFAULTS.get(key, {}))
    out["language"] = key
    out["language_name"] = LANG_NAMES.get(key, key)
    out["storage"] = _merge(cfg.get("storage") or {}, {})
    out["storage"]["path"] = (cfg.get("storage") or {}).get("path") or DEFAULTS["storage"]["path"]
    return out


def enabled_courses(cfg: Dict[str, Any]) -> List[str]:
    """Which courses to load, in menu order. Unknown / broken ones are dropped."""
    want = (cfg.get("courses") or {}).get("enabled") or []
    keys = [normalize(w) for w in want if normalize(w) in LANG_NAMES]
    if not keys:
        keys = [normalize(cfg.get("language") or DEFAULT_LANG)] or [DEFAULT_LANG]
    for extra in supported():
        if extra not in keys:
            keys.append(extra)  # still discoverable; the registry marks it unready
    return keys


def default_course(cfg: Dict[str, Any]) -> str:
    explicit = (cfg.get("courses") or {}).get("default")
    if explicit and normalize(explicit) in LANG_NAMES:
        return normalize(explicit)
    return normalize(cfg.get("language") or DEFAULT_LANG)


def azure_ready(cfg: Dict[str, Any]) -> bool:
    pron = cfg["pronunciation"]
    return bool(pron.get("key")) and bool(pron.get("region"))


def iflytek_ready(cfg: Dict[str, Any]) -> bool:
    ise = cfg["pronunciation"].get("iflytek") or {}
    if ise.get("enabled") is False:  # e.g. Spanish: ISE cannot score it
        return False
    return bool(ise.get("appid")) and bool(ise.get("apikey"))


def resolve_provider(cfg: Dict[str, Any]) -> str:
    """auto: prefer the language's best engine, then the other, then the mock."""
    provider = (cfg["pronunciation"].get("provider") or "auto").lower()
    if provider != "auto":
        if provider == "iflytek" and not iflytek_ready(cfg):
            return "mock"
        if provider == "azure" and not azure_ready(cfg):
            return "mock"
        return provider

    order = ["iflytek", "azure"]
    prefer = (cfg["pronunciation"].get("prefer") or "iflytek").lower()
    if prefer in order:
        order.remove(prefer)
        order.insert(0, prefer)
    for name in order:
        if name == "iflytek" and iflytek_ready(cfg):
            return "iflytek"
        if name == "azure" and azure_ready(cfg):
            return "azure"
    return "mock"


def resolve_asr(cfg: Dict[str, Any]) -> str:
    """Who turns free-form speech into text: client | iflytek | azure | mock."""
    want = (cfg.get("free", {}).get("asr") or "auto").lower()
    if want != "auto":
        if want == "iflytek" and not iflytek_ready(cfg):
            return "mock"
        if want == "azure" and not azure_ready(cfg):
            return "mock"
        return want
    order = ["iflytek", "azure"] if cfg.get("language") == "zh" else ["azure", "iflytek"]
    for name in order:
        if name == "iflytek" and iflytek_ready(cfg):
            return "iflytek"
        if name == "azure" and azure_ready(cfg):
            return "azure"
    return "mock"


def reading_mode_for(cfg: Dict[str, Any], level_id: int) -> str:
    """How much of the reading line this band shows. auto -> per-band ladder."""
    ui = cfg.get("ui") or {}
    mode = (ui.get("reading_mode") or "auto").lower()
    if mode != "auto":
        return mode
    by_level = ui.get("reading_by_level") or {}
    value = by_level.get(level_id) or by_level.get(str(level_id))
    return (value or "always").lower()


def scene_mode_for(cfg: Dict[str, Any], level_id: int) -> str:
    """How much English orientation this band gets before a conversation."""
    ui = cfg.get("ui") or {}
    mode = (ui.get("scene_mode") or "auto").lower()
    if mode != "auto":
        return mode
    by_level = ui.get("scene_by_level") or {}
    value = by_level.get(level_id) or by_level.get(str(level_id))
    return (value or "always").lower()
