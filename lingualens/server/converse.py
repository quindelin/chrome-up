"""Role-play: the other speaker in the lesson's scene, played by a model.

Every exchange in a lesson is one question and one answer, and nothing ever
replies to what the learner actually said. So turn-taking, follow-ups,
clarifying and repair - the four things the B1 interaction descriptors ask
for - are never practised. This module is the other half of a short
conversation: given the scene and what has been said so far, it returns the
partner's next line, plus one possible reply for the learner (shown only
after two misses, the same way a free answer's sample is).

Same client pattern as `free.llm_check` and `think._llm`: an
OpenAI-compatible `/chat/completions`, the `think` model and key. It fails
closed rather than open, because there is nothing deterministic to fall back
to: with no key the step is left out of the lesson (`available`), and a
failure mid-conversation ends the scene early (`reply` returns None).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from .course import LANG_NAMES, normalize

_SYSTEM = (
    "You are role-playing with a {name} learner (level: {level}). You are "
    "the other speaker in this scene: {scene}\n"
    "Stay in character and in {name} only. Reply to what the learner actually "
    "said - pick up their details, ask a natural follow-up, and if what they "
    "said was unclear or wrong for the scene, ask them to clarify as a real "
    "person would. One or two short sentences, at the learner's level, using "
    "the lesson's language where it fits: {focus}\n"
    "Reply with JSON only: {{\"reply\": your line in {name}, \"reply_en\": its "
    "English, \"hint\": one short thing the learner could say back, in "
    "{name}, \"hint_en\": its English, \"done\": true if the scene has reached "
    "a natural end}}."
)


def _key(cfg: Dict) -> Optional[str]:
    think_cfg = cfg.get("think") or {}
    key_env = think_cfg.get("api_key_env") or "OPENAI_API_KEY"
    return os.getenv(key_env) if key_env else None


def available(cfg: Dict) -> bool:
    """Whether a role-play can run at all: enabled, and a key to run it with."""
    if not (cfg.get("converse") or {}).get("enabled", True):
        return False
    return bool(_key(cfg))


def reply(
    scene: str,
    focus: str,
    history: List[Dict],
    cfg: Dict,
    lang: str,
    level: str = "",
) -> Optional[Dict]:
    """The partner's next line, or None when the model cannot be asked.

    `history` is [{"who": "them"|"you", "text": ...}, ...], oldest first.
    Returns {"reply", "reply_en", "hint", "hint_en", "done"}.
    """
    key = _key(cfg)
    if not key:
        return None
    lang = normalize(lang)
    name = LANG_NAMES.get(lang, lang)
    think_cfg = cfg.get("think") or {}
    conv_cfg = cfg.get("converse") or {}
    messages = [{
        "role": "system",
        "content": _SYSTEM.format(name=name, level=level or "beginner",
                                  scene=scene or "an everyday conversation",
                                  focus=focus or "everyday phrases"),
    }]
    # from the model's side: its own lines are the assistant, the learner's
    # are the user - so the conversation reads the way it was held
    for turn in history:
        if turn.get("who") == "them":
            messages.append({"role": "assistant",
                             "content": json.dumps({"reply": turn.get("text", "")},
                                                   ensure_ascii=False)})
        else:
            messages.append({"role": "user",
                             "content": f"Learner (speech recognition): {turn.get('text', '')}"})
    payload = {
        "model": think_cfg.get("model", "gpt-4o-mini"),
        "temperature": 0.7,
        "max_tokens": 250,
        "response_format": {"type": "json_object"},
        "messages": messages,
    }
    base = (think_cfg.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            req, timeout=float(conv_cfg.get("timeout", 12) or 12)
        ) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        data = json.loads(body["choices"][0]["message"]["content"])
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            ValueError, KeyError, IndexError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    line = str(data.get("reply") or "").strip()
    if not line:
        return None
    return {
        "reply": line,
        "reply_en": str(data.get("reply_en") or "").strip(),
        "hint": str(data.get("hint") or "").strip(),
        "hint_en": str(data.get("hint_en") or "").strip(),
        "done": bool(data.get("done")),
    }
