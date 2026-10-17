"""The agent plug-in surface.

Anyone (a human-written heuristic, an LLM, a remote service, another coding agent
with its own tools) can become the "editor" by returning a list of ClipDecisions.
Three built-ins ship:

  heuristic : rules over the local signal analysis (no network, always works)
  llm       : OpenAI-compatible chat-completions endpoint, optionally vision over frames
  remote    : POST the context JSON to any URL, read {"clips": [...]} back

Register your own with `register_agent("name", MyAgent)`.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

from .signals import Analysis
from .transcript import Transcript
from .util import clamp


# --------------------------------------------------------------------------- types
@dataclass
class ClipDecision:
    """One proposed clip. Times are seconds *relative to the start of the window*."""
    start: float
    end: float
    score: float = 0.5
    title: str = ""
    caption: str = ""
    hashtags: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    hook: str = ""
    why: str = ""
    publish: bool = True

    @classmethod
    def from_any(cls, raw: Any, constraints: dict) -> Optional["ClipDecision"]:
        """Tolerant parse: agents produce messy JSON, we still want their intent."""
        if not isinstance(raw, dict):
            return None
        start = _num(raw.get("start", raw.get("start_s", raw.get("from"))))
        end = _num(raw.get("end", raw.get("end_s", raw.get("to"))))
        if start is None:
            return None
        if end is None:
            length = _num(raw.get("duration", raw.get("length"))) or constraints.get(
                "target_clip_seconds", 25)
            end = start + length
        duration = max(0.0, end - start)
        min_s = float(constraints.get("min_clip_seconds", 10))
        max_s = float(constraints.get("max_clip_seconds", 30))
        if duration <= 0.5:
            return None
        if duration < min_s:
            pad = (min_s - duration) / 2
            start, end = start - pad, end + pad
        if duration > max_s:
            end = start + max_s
        hashtags = raw.get("hashtags") or []
        if isinstance(hashtags, str):
            hashtags = [h for h in hashtags.replace(",", " ").split() if h]
        platforms = raw.get("platforms") or constraints.get("platforms") or []
        if isinstance(platforms, str):
            platforms = [p.strip() for p in platforms.split(",") if p.strip()]
        return cls(
            start=max(0.0, float(start)),
            end=max(0.0, float(end)),
            score=float(clamp(_num(raw.get("score")) if _num(raw.get("score")) is not None
                              else 0.5, 0.0, 1.0)),
            title=str(raw.get("title") or "").strip(),
            caption=str(raw.get("caption") or raw.get("description") or "").strip(),
            hashtags=[str(h) for h in hashtags][:12],
            platforms=[str(p) for p in platforms],
            hook=str(raw.get("hook") or "").strip(),
            why=str(raw.get("why") or raw.get("reason") or raw.get("rationale") or "").strip(),
            publish=bool(raw.get("publish", True)),
        )

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict:
        return {"start": round(self.start, 2), "end": round(self.end, 2),
                "score": round(self.score, 3), "title": self.title, "caption": self.caption,
                "hashtags": self.hashtags, "platforms": self.platforms, "hook": self.hook,
                "why": self.why, "publish": self.publish}


def _num(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class AgentContext:
    """Everything the editor agent gets to look at."""
    window: dict                       # Window.to_dict()
    analysis: Analysis
    transcript: Transcript
    frames: List[dict] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    previous: List[dict] = field(default_factory=list)   # clips already posted recently
    source: dict = field(default_factory=dict)

    # ---------------------------------------------------------------- payloads
    def brief(self) -> dict:
        """Compact JSON the agent reasons over (no giant arrays)."""
        return {
            "window": {k: v for k, v in self.window.items() if k != "segments"},
            "duration": round(self.analysis.duration, 2),
            "notes": self.analysis.notes,
            "moments": [m.to_dict() for m in self.analysis.moments][:12],
            "per_second": [s.to_dict() for s in self.analysis.per_second],
            "transcript": {
                "engine": self.transcript.engine,
                "language": self.transcript.language,
                "text": self.transcript.text[:4000],
            },
            "frames": [{"t": f["t"], "path": f["path"]} for f in self.frames],
            "constraints": self.constraints,
            "previous_clips": self.previous[-10:],
            "source": self.source,
        }

    def to_dict(self) -> dict:
        return self.brief()


# --------------------------------------------------------------------------- protocol
class ClipAgent(Protocol):
    name: str

    def propose(self, ctx: AgentContext) -> List[ClipDecision]:
        ...


# --------------------------------------------------------------------------- heuristic
class HeuristicAgent:
    """Deterministic editor: turns signal 'moments' into clips. Zero dependencies."""

    name = "heuristic"

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def propose(self, ctx: AgentContext) -> List[ClipDecision]:
        max_clips = int(ctx.constraints.get("max_clips_per_window", 3))
        out: List[ClipDecision] = []
        for moment in ctx.analysis.moments[:max_clips]:
            text = ctx.transcript.slice(moment.start, moment.end).text.strip()
            title = _title_from(text) or f"Highlight @ {int(moment.start)}s"
            out.append(ClipDecision(
                start=moment.start,
                end=moment.end,
                score=round(moment.score, 3),
                title=title[:100],
                caption=_caption_from(text),
                hashtags=ctx.constraints.get("default_tags", []) or [],
                platforms=ctx.constraints.get("platforms", []),
                hook=_hook_from(text),
                why="; ".join(moment.reasons),
            ))
        return out


def _title_from(text: str) -> str:
    words = (text or "").split()
    if len(words) < 4:
        return ""
    chunk = " ".join(words[:12]).strip(" ,.;:!?")
    return chunk[:1].upper() + chunk[1:] if chunk else ""


def _hook_from(text: str) -> str:
    words = (text or "").split()
    if len(words) < 6:
        return ""
    return " ".join(words[:6])


def _caption_from(text: str) -> str:
    words = (text or "").split()
    if not words:
        return ""
    return " ".join(words[:28])


# --------------------------------------------------------------------------- llm
SYSTEM_PROMPT = """You are a short-form video editor watching a rolling buffer of a
live POV stream (smart-glasses / OBS footage).

You are given:
  - `per_second`: one row per second with rms_db (loudness), speech, motion, brightness, cut
  - `moments`: pre-computed candidate windows with heuristic scores
  - `transcript`: what was said (may be empty)
  - `frames`: stills you may be shown as images, each with its timestamp `t`

Decide which moments are worth posting as vertical short-form clips to
Instagram Reels / YouTube Shorts / X. Be selective: return 0 clips when nothing
is genuinely interesting. Prefer moments with a clear hook, a payoff, and an
obvious ending. Avoid silence, static shots, black frames, and mid-sentence cuts.

Length matters more than coverage: these are built to loop and be re-watched, so
aim for target_clip_seconds and never exceed max_clip_seconds. If a moment is
longer than the cap, choose its single best sub-window — do not start at the
beginning of the moment by default. One tight clip beats one padded clip.

Return STRICT JSON and nothing else:
{"clips": [{"start": <seconds into window>, "end": <seconds>, "score": <0..1>,
            "title": <string>, "caption": <string>, "hashtags": [<string>],
            "platforms": ["instagram","youtube","x"], "hook": <string>,
            "why": <string>}]}

Constraints are in `constraints`; do not exceed max_clips_per_window, min_clip_seconds
or max_clip_seconds. `start`/`end` are seconds from the START of the window."""


class LLMAgent:
    """OpenAI-compatible /chat/completions, optionally with vision over frames."""

    name = "llm"

    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.base_url = str(self.cfg.get("base_url", "https://api.openai.com/v1")).rstrip("/")
        self.model = str(self.cfg.get("model", "gpt-4o-mini"))
        self.api_key_env = str(self.cfg.get("api_key_env", "OPENAI_API_KEY"))
        self.temperature = float(self.cfg.get("temperature", 0.2))
        self.send_frames = bool(self.cfg.get("send_frames", True))
        self.max_frames = int(self.cfg.get("max_frames", 12))

    @property
    def api_key(self) -> str:
        return os.environ.get(self.api_key_env, "")

    def propose(self, ctx: AgentContext) -> List[ClipDecision]:
        if not self.api_key:
            return HeuristicAgent({}).propose(ctx)

        content: List[dict] = [{"type": "text", "text":
                                "Analyze this window and propose clips.\n\n"
                                + json.dumps(ctx.brief(), indent=2)[:24000]}]
        if self.send_frames and ctx.frames:
            for frame in ctx.frames[: self.max_frames]:
                b64 = _b64_image(Path(frame["path"]))
                if not b64:
                    continue
                content.append({"type": "text", "text": f"[frame t={frame['t']}s]"})
                content.append({"type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        }
        data = _post_json(f"{self.base_url}/chat/completions", payload,
                          {"Authorization": f"Bearer {self.api_key}"},
                          timeout=float(self.cfg.get("timeout", 180)))
        text = _extract_message(data)
        clips = _parse_clips(text)
        decisions = [d for d in (ClipDecision.from_any(c, ctx.constraints) for c in clips) if d]
        # enforce ordering + count
        decisions.sort(key=lambda d: d.score, reverse=True)
        return decisions[: int(ctx.constraints.get("max_clips_per_window", 3))]


def _b64_image(path: Path) -> str:
    try:
        return base64.b64encode(path.read_bytes()).decode("ascii")
    except Exception:
        return ""


def _extract_message(data: dict) -> str:
    try:
        return data["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


def _parse_clips(text: str) -> List[dict]:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < 0:
        return []
    try:
        obj = json.loads(cleaned[start: end + 1])
    except Exception:
        return []
    if isinstance(obj, dict):
        clips = obj.get("clips") or obj.get("decisions") or []
        return clips if isinstance(clips, list) else []
    if isinstance(obj, list):
        return obj
    return []


# --------------------------------------------------------------------------- remote
class RemoteAgent:
    """POST the context to any HTTP endpoint; expect {"clips": [...]} back.

    This is the escape hatch: point it at your own agent, a Cloudflare Worker,
    an n8n webhook, a Slack bot, whatever.
    """

    name = "remote"

    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.url = str(self.cfg.get("url", ""))
        self.headers = dict(self.cfg.get("headers") or {})
        self.timeout = float(self.cfg.get("timeout", 120))

    def propose(self, ctx: AgentContext) -> List[ClipDecision]:
        if not self.url:
            return HeuristicAgent({}).propose(ctx)
        try:
            data = _post_json(self.url, ctx.brief(), self.headers, timeout=self.timeout)
        except Exception:
            return []
        clips = data.get("clips") if isinstance(data, dict) else data
        if not isinstance(clips, list):
            return []
        decisions = [d for d in (ClipDecision.from_any(c, ctx.constraints) for c in clips) if d]
        decisions.sort(key=lambda d: d.score, reverse=True)
        return decisions[: int(ctx.constraints.get("max_clips_per_window", 3))]


def _post_json(url: str, payload: dict, headers: dict, timeout: float = 60.0) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, str(v))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


# --------------------------------------------------------------------------- registry
_REGISTRY: Dict[str, Callable[[dict], Any]] = {
    "heuristic": HeuristicAgent,
    "llm": LLMAgent,
    "remote": RemoteAgent,
}


def register_agent(name: str, factory: Callable[[dict], Any]) -> None:
    """`register_agent("my-agent", lambda cfg: MyAgent(cfg))`"""
    _REGISTRY[name] = factory


def list_agents() -> List[str]:
    return sorted(_REGISTRY)


def build_agent(cfg: dict) -> Any:
    """cfg = the `agent:` block of autoclip.yaml."""
    name = str(cfg.get("name", "heuristic")).lower()
    factory = _REGISTRY.get(name)
    if factory is None:
        raise RuntimeError(f"unknown agent {name!r}; registered: {list_agents()}")
    return factory(cfg.get(name, {}) if isinstance(cfg.get(name), dict) else {})
