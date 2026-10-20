"""Voice command detection: turn a transcript into structured `StreamEvent`s.

The HUD / stream-element agent subscribes to these events. autoclip does not
decide *what* to render — it only detects intent and forwards it. The HUD agent
maps `target` to its own scene graph.

Two parser backends:

  regex  (default) : pattern match against `transcript.words`. Fast, offline.
  llm              : ask an OpenAI-compatible model for a strict JSON event.
                     Use this when commands are phrased loosely and you want
                     natural-language understanding.

Trigger phrase examples (see `DEFAULT_PATTERNS`):

  "show the compass"            -> intent=show target=compass
  "hide health bar"             -> intent=hide target=health bar
  "set weather to snow"         -> intent=set target=weather value=snow
  "play dragon roar"            -> intent=play target=dragon roar
  "add subtitle: hello there"   -> intent=add target=subtitle value=hello there

Privacy blur (see docs/PRIVACY_BLUR.md):

  "blur faces"                  -> intent=blur   target=faces
  "privacy mode on"             -> intent=blur   target=faces
  "unblur faces"                -> intent=unblur target=faces
  "stop blurring"               -> intent=unblur target=faces
  "toggle face blur"            -> intent=toggle target=face blur

OBS control (driven by autoclip itself, see docs/OBS_VOICE_CONTROL.md):

  "switch to the map scene"     -> intent=scene target=map
  "mute the mic"                -> intent=mute target=mic
  "volume 50"                   -> intent=volume value=50
  "start recording"             -> intent=record
  "stop recording"              -> intent=unrecord
  "start the virtual camera"    -> intent=vcam
  "start streaming"             -> intent=broadcast   (OBS's own output)
  "stop broadcasting"           -> intent=unbroadcast
  "save the replay"             -> intent=replay

Live multi-streaming (see docs/LIVE_STREAMING.md):

  "go live on twitch"           -> intent=stream target=twitch
  "stop twitch"                 -> intent=unstream target=twitch

A bare transcript with no triggers returns `[]`. The HUD treats silence as
"do nothing".
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from .transcript import Transcript


# --------------------------------------------------------------------------- event
@dataclass
class StreamEvent:
    """One thing the HUD should react to. Times are seconds from window start."""
    type: str = "voice_command"        # voice_command | transcript_chunk | system
    ts: float = 0.0                    # wall-clock when emitted
    window_t: float = 0.0              # seconds into the current window
    text: str = ""                     # raw transcript text that triggered
    intent: str = ""                   # show | hide | set | play | add | toggle | unknown
    target: str = ""                   # the noun (what to act on)
    value: str = ""                    # optional value (set X to Y, add X: Y)
    confidence: float = 0.0
    source: str = "regex"              # regex | llm | manual
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type, "ts": round(self.ts, 3),
            "window_t": round(self.window_t, 3),
            "text": self.text, "intent": self.intent, "target": self.target,
            "value": self.value, "confidence": round(self.confidence, 3),
            "source": self.source, "extra": self.extra,
        }


# --------------------------------------------------------------------------- patterns
DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    # -------------------------------------------------------------- privacy blur
    # "blur faces" / "unblur" — the toggle the wearer reaches for when they
    # walk into a crowd. Must sit first: the generic "stop X" rule further
    # down would otherwise read "stop blurring faces" as "stop <platform>".
    {"intent": "blur",   "re": r"^\s*(?:blur|censor|pixelate|mask|hide)\s+"
                               r"(?:all\s+|every(?:one'?s|body'?s)?\s+|the\s+)?"
                               r"(?P<target>faces?|people|bystanders?|crowd)\s*\.?\s*$"},
    {"intent": "blur",   "re": r"^\s*blur\s+(?:all|every(?:one|body)|them)\s*\.?\s*$",
     "target_literal": "faces"},
    {"intent": "blur",   "re": r"^\s*(?:turn|switch)\s+(?:the\s+)?privacy\s+(?:mode\s+)?on\s*\.?\s*$",
     "target_literal": "faces"},
    {"intent": "blur",   "re": r"^\s*privacy\s+(?:mode\s+)?(?:on|please)\s*\.?\s*$",
     "target_literal": "faces"},
    {"intent": "blur",   "re": r"^\s*(?:start|begin)\s+blurring\s*\.?\s*$",
     "target_literal": "faces"},
    {"intent": "unblur", "re": r"^\s*(?:unblur|uncensor|show)\s+"
                               r"(?:all\s+|the\s+)?"
                               r"(?P<target>faces?|people|bystanders?)\s*\.?\s*$"},
    {"intent": "unblur", "re": r"^\s*(?:stop|end)\s+blurring\s*(?:(?:the\s+)?faces?)?\s*\.?\s*$",
     "target_literal": "faces"},
    {"intent": "unblur", "re": r"^\s*(?:turn|switch)\s+(?:the\s+)?privacy\s+(?:mode\s+)?off\s*\.?\s*$",
     "target_literal": "faces"},
    {"intent": "unblur", "re": r"^\s*privacy\s+(?:mode\s+)?off\s*\.?\s*$",
     "target_literal": "faces"},
    # "toggle face blur" -> toggle, which the privacy manager owns
    {"intent": "toggle", "re": r"^\s*toggle\s+(?:the\s+)?(?P<target>face\s*blur|privacy(?:\s*mode)?|blur)\s*\.?\s*$"},
    # ------------------------------------------------------------------ hud
    # "show X" / "show the X"
    {"intent": "show",   "re": r"^\s*show\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$"},
    # "hide X"
    {"intent": "hide",   "re": r"^\s*hide\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$"},
    # "toggle X"
    {"intent": "toggle", "re": r"^\s*toggle\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$"},
    # ------------------------------------------------------------------ volume
    # Must precede the generic "set X to Y" rule, which would otherwise grab
    # these and treat "mic volume" / "transition" as a HUD source name.
    # "set mic volume to 50" / "set the music volume to 20%"
    {"intent": "volume", "re": r"^\s*set\s+(?:the\s+)?(?P<target>.+?)\s+volume\s+to\s+(?P<value>\d{1,3}(?:\.\d+)?)\s*%?\s*\.?\s*$"},
    # "set volume to 50" / "volume 50" / "volume 50%"
    {"intent": "volume", "re": r"^\s*(?:set\s+)?volume\s+(?:to\s+)?(?P<value>\d{1,3}(?:\.\d+)?)\s*%?\s*\.?\s*$"},
    # "turn the volume up" / "volume down"
    {"intent": "volume", "re": r"^\s*turn\s+(?:the\s+)?volume\s+(?P<value>up|down|louder|quieter|softer|higher|lower)\s*\.?\s*$"},
    {"intent": "volume", "re": r"^\s*volume\s+(?P<value>up|down|louder|quieter|softer|higher|lower)\s*\.?\s*$"},
    # -------------------------------------------------------------- transition
    # "set transition to fade" / "transition cut"
    {"intent": "transition", "re": r"^\s*(?:set\s+)?transition\s+(?:to\s+)?(?P<target>.+?)\s*\.?\s*$"},
    # "set X to Y"
    {"intent": "set",    "re": r"^\s*set\s+(?:the\s+)?(?P<target>.+?)\s+to\s+(?P<value>.+?)\s*\.?\s*$"},
    # "play X"
    {"intent": "play",   "re": r"^\s*play\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$"},
    # "add <thing>: <value>"   or   "add <thing> <value>"
    {"intent": "add",    "re": r"^\s*add\s+(?:a\s+|an\s+|the\s+)?(?P<target>.+?)\s*[:\-]\s*(?P<value>.+?)\s*\.?\s*$"},
    {"intent": "add",    "re": r"^\s*add\s+(?:a\s+|an\s+|the\s+)?(?P<target>.+?)\s+(?P<value>[^\s].+?)\s*\.?\s*$"},
    # "subtitle: hello"  /  "caption: hello"
    {"intent": "add",    "re": r"^\s*(?:subtitle|caption)\s*[:\-]\s*(?P<value>.+?)\s*\.?\s*$",
     "target_literal": "subtitle"},
    # "clip this"
    {"intent": "clip",   "re": r"^\s*clip\s+(?:this|that|now)\s*\.?\s*$"},
    # "start a clip" / "save this clip"
    {"intent": "clip",   "re": r"^\s*(?:start|save|mark)\s+(?:a\s+|the\s+)?clip\s*\.?\s*$"},
    # -------------------------------------------------------------- obs control
    # These drive OBS itself (scene switching, recording, mute, ...), as
    # opposed to the live-stream block below, which drives autoclip's own
    # per-platform republishers. Both can be live at once.
    #
    # Scene switching: "switch to the map scene" / "go to ending scene"
    {"intent": "scene", "re": r"^\s*(?:switch|change|go|cut|jump)\s+(?:to\s+)?(?:the\s+)?(?P<target>.+?)\s+scene\s*\.?\s*$"},
    # "scene map" / "cut to the map"
    {"intent": "scene", "re": r"^\s*scene\s+(?P<target>.+?)\s*\.?\s*$"},
    {"intent": "scene", "re": r"^\s*cut\s+to\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$"},
    # Mute: "mute the mic" / "mute" (bare = default audio input)
    {"intent": "mute",   "re": r"^\s*mute\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$"},
    {"intent": "mute",   "re": r"^\s*mute\s*\.?\s*$"},
    {"intent": "unmute", "re": r"^\s*unmute\s+(?:the\s+)?(?P<target>.+?)\s*\.?\s*$"},
    {"intent": "unmute", "re": r"^\s*unmute\s*\.?\s*$"},
    # Recording: "start recording" / "record this" / "stop recording"
    {"intent": "record",   "re": r"^\s*(?:start|begin)\s+recording\s*\.?\s*$"},
    {"intent": "record",   "re": r"^\s*record\s+(?:this|that|now|the\s+stream)\s*\.?\s*$"},
    {"intent": "unrecord", "re": r"^\s*(?:stop|end|finish)\s+recording\s*\.?\s*$"},
    # Virtual camera
    {"intent": "vcam",   "re": r"^\s*start\s+(?:the\s+)?virtual\s*cam(?:era)?\s*\.?\s*$"},
    {"intent": "unvcam", "re": r"^\s*stop\s+(?:the\s+)?virtual\s*cam(?:era)?\s*\.?\s*$"},
    # OBS's own stream output. Bare "start streaming" = OBS; the
    # multi-stream block below only fires when a platform is named
    # ("start streaming on twitch"). Must precede the generic stop rule.
    {"intent": "broadcast",   "re": r"^\s*(?:start|begin)\s+(?:the\s+)?(?:obs\s+)?stream(?:ing)?\s*\.?\s*$"},
    {"intent": "broadcast",   "re": r"^\s*(?:start|begin)\s+broadcast(?:ing)?\s*\.?\s*$"},
    {"intent": "unbroadcast", "re": r"^\s*(?:stop|end)\s+(?:the\s+)?(?:obs\s+)?stream(?:ing)?\s*\.?\s*$"},
    {"intent": "unbroadcast", "re": r"^\s*(?:stop|end)\s+broadcast(?:ing)?\s*\.?\s*$"},
    # Replay buffer: "save the replay" / "replay that"
    {"intent": "replay", "re": r"^\s*(?:save|mark|grab)\s+(?:the\s+)?replay\s*\.?\s*$"},
    {"intent": "replay", "re": r"^\s*replay\s+(?:that|this)\s*\.?\s*$"},
    # -------------------------------------------------------------- live stream
    # "go live everywhere" / "go live on all platforms" — must precede the
    # generic "go live on X" rule below, or it captures "all platforms".
    {"intent": "stream",   "re": r"^\s*go\s+live\s+(?:on\s+)?(?:all(?:\s+platforms)?|everywhere)\s*\.?\s*$",
     "target_literal": "all"},
    # "go live on twitch" / "live on youtube"
    {"intent": "stream",   "re": r"^\s*(?:go\s+)?live\s+(?:on|to|at)\s+(?P<target>.+?)\s*\.?\s*$"},
    # "start streaming on twitch" / "start streaming to youtube"
    {"intent": "stream",   "re": r"^\s*start\s+streaming\s+(?:on|to|at)\s+(?P<target>.+?)\s*\.?\s*$"},
    # "start twitch" (implicit: start streaming on <platform>)
    {"intent": "stream",   "re": r"^\s*start\s+(?P<target>twitch|youtube|kick|rumble|instagram|facebook|tiktok|x)\s*\.?\s*$"},
    # "stop all streams" / "stop all live" — also before the generic rule
    {"intent": "unstream", "re": r"^\s*stop\s+all\s+(?:streams|live)\s*\.?\s*$",
     "target_literal": "all"},
    # "stop streaming to youtube" / "stop streaming on twitch"
    {"intent": "unstream", "re": r"^\s*stop\s+streaming\s+(?:on|to|at)\s+(?P<target>.+?)\s*\.?\s*$"},
    # "end the youtube stream" / "finish the twitch stream"
    {"intent": "unstream", "re": r"^\s*(?:end|finish)\s+(?:the\s+)?(?P<target>.+?)\s+stream\s*\.?\s*$"},
    # "stop youtube" / "stop twitch" — last, and only fires for known platforms
    {"intent": "unstream", "re": r"^\s*stop\s+(?P<target>.+?)\s*\.?\s*$"},
]

# Words that are almost always noise, not commands.
STOPWORDS = {"a", "an", "the", "please", "now", "right"}


# --------------------------------------------------------------------------- parsers
class VoiceCommandParser(Protocol):
    name: str

    def parse(self, transcript: Transcript, window_t: float = 0.0) -> List[StreamEvent]:
        ...


class RegexParser:
    """Default: pattern-match sentence boundaries in the transcript."""

    name = "regex"

    def __init__(self, patterns: Optional[List[Dict[str, Any]]] = None,
                 min_confidence: float = 0.5):
        self.patterns = patterns or DEFAULT_PATTERNS
        self.compiled = []
        for p in self.patterns:
            flags = re.IGNORECASE
            self.compiled.append((p, re.compile(p["re"], flags)))
        self.min_confidence = float(min_confidence)

    def _emit(self, p: dict, m: re.Match, text: str, window_t: float) -> StreamEvent:
        gd = m.groupdict()
        target = str(gd.get("target") or "").strip()
        value = str(gd.get("value") or "").strip()
        if not target and p.get("target_literal"):
            target = str(p["target_literal"])
        # clean filler
        target = self._clean(target)
        value = value.strip(' "\'')
        # Patterns with no target (e.g. "clip this") are still useful commands.
        return StreamEvent(
            ts=time.time(),
            window_t=window_t,
            text=text.strip(),
            intent=p["intent"],
            target=target,
            value=value,
            confidence=0.7 if target else 0.6,
            source="regex",
        )

    @staticmethod
    def _clean(s: str) -> str:
        words = [w for w in re.split(r"\s+", s.strip()) if w and w.lower() not in STOPWORDS]
        return " ".join(words)

    def parse(self, transcript: Transcript, window_t: float = 0.0) -> List[StreamEvent]:
        out: List[StreamEvent] = []
        if not transcript or not transcript.text:
            return out

        # Split into sentences on period/question-mark boundaries. Whisper
        # already produces text segments; here we coarse-split for speed.
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", transcript.text) if s.strip()]

        # Slide the window so we attribute the event to the time the words
        # were actually spoken (midpoint of first..last word in the sentence).
        word_starts = {i: (w.t0, w.t1) for i, w in enumerate(transcript.words)}
        # sentences come in order, so each one is searched for after the last
        # one found; otherwise a second "show ..." got the first one's time
        cursor = 0

        for sentence in sentences:
            for p, rx in self.compiled:
                m = rx.match(sentence)
                if not m:
                    continue
                # try to locate the sentence inside the word list
                first = self._first_word_of(sentence, transcript, cursor)
                if first is not None:
                    cursor = first + 1
                wt = (word_starts[first][0] + word_starts[first][1]) / 2 if first is not None else window_t
                ev = self._emit(p, m, sentence, wt)
                if ev.confidence >= self.min_confidence:
                    out.append(ev)
                break  # one intent per sentence
        return out

    @staticmethod
    def _first_word_of(sentence: str, tr: Transcript, start: int = 0) -> Optional[int]:
        s = sentence.lower().strip(" .!?")
        if not s:
            return None
        for i in range(start, len(tr.words)):
            if tr.words[i].text.lower().strip(" .!?,").startswith(s.split()[0][:4]):
                return i
        return None


class LLMParser:
    """OpenAI-compatible LLM parser. Use when commands are phrased loosely."""

    name = "llm"

    PROMPT = (
        "You watch a live POV stream and listen for voice commands to control "
        "an on-screen HUD (compass, health bar, subtitles, sound effects, ...).\n\n"
        "Given the transcript chunk between <transcript> and </transcript>, return "
        "STRICT JSON: an array of objects, one per detected command.\n"
        "\"blur faces\" / \"privacy mode on\" -> intent=blur target=faces; "
        "\"unblur\" / \"stop blurring\" / \"privacy off\" -> intent=unblur target=faces.\n"
        "Schema per object:\n"
        '  {"intent": "show|hide|toggle|set|play|add|clip|scene|mute|unmute|'
        'volume|record|unrecord|vcam|unvcam|broadcast|unbroadcast|replay|'
        'transition|stream|unstream|blur|unblur|unknown",\n'
        '   "target": "<noun or empty>",\n'
        '   "value":  "<value or empty>",\n'
        '   "text":   "<the exact sentence>",\n'
        '   "confidence": <0..1>}\n\n'
        "Return [] when nothing is a command. Be conservative: only emit a "
        "command when the speaker is clearly instructing the HUD."
    )

    def __init__(self, cfg: dict):
        import os
        self.base_url = cfg.get("base_url", "https://api.openai.com/v1")
        self.model = cfg.get("model", "gpt-4o-mini")
        key = os.environ.get(cfg.get("api_key_env", "OPENAI_API_KEY"), "")
        self.api_key = key
        self.timeout = float(cfg.get("timeout", 30))

    def parse(self, transcript: Transcript, window_t: float = 0.0) -> List[StreamEvent]:
        if not self.api_key or not transcript.text:
            return []
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.PROMPT},
                {"role": "user", "content": f"<transcript>\n{transcript.text}\n</transcript>"},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:  # noqa: S310
                data = json.loads(r.read())
        except Exception:
            return []
        try:
            content = data["choices"][0]["message"]["content"]
            arr = json.loads(content)
            if isinstance(arr, dict) and "commands" in arr:
                arr = arr["commands"]
        except Exception:
            return []
        out: List[StreamEvent] = []
        for item in arr or []:
            if not isinstance(item, dict):
                continue
            out.append(StreamEvent(
                ts=time.time(), window_t=window_t,
                text=str(item.get("text", "")),
                intent=str(item.get("intent", "unknown")),
                target=str(item.get("target", "")).strip(),
                value=str(item.get("value", "")).strip(),
                confidence=float(item.get("confidence", 0.6)),
                source="llm",
            ))
        return out


def build_parser(cfg: dict) -> VoiceCommandParser:
    name = str(cfg.get("name", "regex")).lower()
    if name == "llm":
        return LLMParser(cfg.get("llm", {}))
    if name == "off" or name == "none" or name == "disabled":
        class _Noop:
            name = "off"
            def parse(self, transcript, window_t=0.0): return []
        return _Noop()
    return RegexParser(cfg.get("patterns"), cfg.get("min_confidence", 0.5))
