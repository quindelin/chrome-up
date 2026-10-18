"""Voice -> OBS. Turns high-level intents into obs-websocket v5 requests.

`obs.py` is a thin protocol client; this module is the *semantic* layer:

  * resolves what the speaker said ("compass") to what OBS calls it
    ("Compass Image") — exact, alias, substring, then fuzzy
  * refuses anything dangerous or out of policy before it reaches OBS
  * returns a uniform `OBSResult` so REST / MCP / CLI / the dispatcher can
    all report the same shape

Guardrails are the point. Streaming live by voice is fine; accidentally
*ending* a broadcast because the mic picked up a false positive is not.
So: opt-in per intent, a scene allowlist, and a hard gate on destructive
actions. Nothing talks to OBS unless `obs.voice.enabled` is true.
"""
from __future__ import annotations

import difflib
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .obs import OBSClient

# Transitions OBS ships with. Used to fuzzy-match "fade" -> "Fade".
KNOWN_TRANSITIONS = ["Cut", "Fade", "Swipe", "Slide", "Fade to Color",
                     "Stinger", "Luma Wipe"]


def normalize(s: str) -> str:
    """Fold a name for comparison: lowercase, drop everything non-alphanumeric."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


@dataclass
class OBSResult:
    ok: bool
    action: str
    target: str = ""
    message: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "action": self.action, "target": self.target,
                "message": self.message, "detail": self.detail}


class OBSController:
    """Executes voice intents against OBS, with name resolution and policy.

    `intents` narrows which intents this controller will act on. The HUD
    intents (show/hide/toggle/set/play) are deliberately NOT enabled by
    default, because a HUD agent attached to the SSE stream usually owns
    them — enabling both means every "show the compass" fires twice.
    """

    SUPPORTED = {"scene", "show", "hide", "toggle", "set", "play",
                 "mute", "unmute", "volume", "record", "unrecord",
                 "vcam", "unvcam", "broadcast", "unbroadcast",
                 "replay", "clip", "transition"}

    # Actions the speaker can't undo and the audience immediately notices.
    DANGEROUS = {"unbroadcast", "unrecord", "unvcam"}

    DEFAULT_INTENTS = ["scene", "mute", "unmute", "volume", "record",
                       "unrecord", "vcam", "unvcam", "broadcast",
                       "unbroadcast", "replay", "clip"]

    def __init__(self, client: OBSClient, cfg: dict | None = None):
        self.client = client
        cfg = dict(cfg or {})
        self.enabled = bool(cfg.get("enabled", False))
        # NOTE: not `self.scene` — that would shadow the scene() method.
        self.pinned_scene = str(cfg.get("scene", "") or "")
        self.scene_allow = [normalize(s) for s in (cfg.get("scenes") or []) if s]
        # show/hide/toggle only these sources ([] = any). Lets OBS own e.g.
        # "show lingualens" while the HUD keeps "show the compass".
        self.visibility_allow = [normalize(s) for s in
                                 (cfg.get("visibility_sources") or []) if s]
        self.allow_dangerous = bool(cfg.get("allow_dangerous", False))
        self.aliases = {normalize(k): v for k, v in
                        (cfg.get("aliases") or {}).items()}
        self.scene_aliases = {normalize(k): v for k, v in
                              (cfg.get("scene_aliases") or {}).items()}
        self.default_audio = str(cfg.get("default_audio", "") or "")
        self.cutoff = float(cfg.get("match_cutoff", 0.6))
        self.cache_seconds = float(cfg.get("cache_seconds", 5.0))
        self.intents = {str(i).lower() for i in
                        (cfg.get("intents") or self.DEFAULT_INTENTS)}
        self._cache: Dict[str, Any] = {}
        self._cache_ts = 0.0

    # ------------------------------------------------------------------ policy
    def handles(self, intent: str) -> bool:
        """True if this controller should act on the intent. Lets the
        dispatcher skip OBS entirely for HUD-owned intents."""
        i = (intent or "").lower().strip()
        if i not in self.SUPPORTED:
            return False
        return i in self.intents

    def _guard(self, intent: str) -> Optional[OBSResult]:
        """Return an OBSResult to short-circuit on, or None to proceed."""
        if not self.enabled:
            return OBSResult(False, intent, "", "obs voice control disabled "
                                                "(set obs.voice.enabled)")
        if intent not in self.intents:
            return OBSResult(False, intent, "", f"intent '{intent}' not enabled for obs")
        if intent in self.DANGEROUS and not self.allow_dangerous:
            return OBSResult(False, intent, "",
                             f"'{intent}' is destructive; set obs.voice.allow_dangerous")
        if not self.client.connect():
            return OBSResult(False, intent, "",
                             f"obs unreachable: {self.client.last_error}")
        return None

    # ------------------------------------------------------------------ lookup
    def _fresh(self) -> bool:
        return bool(self._cache) and \
            (time.time() - self._cache_ts) < self.cache_seconds

    def _refresh(self) -> None:
        d = self.client.get_scene_list() or {}
        self._cache = {
            "current_scene": d.get("currentProgramSceneName") or "",
            "scenes": [str(s.get("sceneName")) for s in (d.get("scenes") or [])
                       if s.get("sceneName")],
            "inputs": self.client.get_input_list() or [],
        }
        self._cache_ts = time.time()

    def scenes(self) -> List[str]:
        if not self._fresh():
            self._refresh()
        return list(self._cache.get("scenes") or [])

    def inputs(self) -> List[dict]:
        if not self._fresh():
            self._refresh()
        return list(self._cache.get("inputs") or [])

    def invalidate(self) -> None:
        self._cache = {}
        self._cache_ts = 0.0

    def active_scene(self) -> str:
        """The scene source ops apply to: the pinned one, else whatever is live."""
        if self.pinned_scene:
            return self.pinned_scene
        if not self._fresh():
            self._refresh()
        return str(self._cache.get("current_scene") or "")

    @staticmethod
    def _match(query: str, candidates: List[str], cutoff: float) -> Optional[str]:
        """exact -> substring (either direction) -> fuzzy. Returns the
        candidate's original spelling, never the query."""
        q = normalize(query)
        if not q or not candidates:
            return None
        by_norm = {normalize(c): c for c in candidates}
        if q in by_norm:
            return by_norm[q]
        for c in candidates:
            n = normalize(c)
            if q in n or (len(q) >= 4 and n in q):
                return c
        close = difflib.get_close_matches(q, list(by_norm), n=1, cutoff=cutoff)
        return by_norm.get(close[0]) if close else None

    def resolve_source(self, name: str) -> Optional[str]:
        if not name:
            return None
        alias = self.aliases.get(normalize(name))
        if alias:
            return alias
        names = [str(i.get("inputName")) for i in self.inputs() if i.get("inputName")]
        hit = self._match(name, names, self.cutoff)
        if hit:
            return hit
        # Groups and nested scenes are scene items, not global inputs.
        items = self.client.get_scene_item_list(self.active_scene()) or []
        return self._match(name, [str(i.get("sourceName")) for i in items
                                  if i.get("sourceName")], self.cutoff)

    def resolve_scene(self, name: str) -> Optional[str]:
        alias = self.scene_aliases.get(normalize(name))
        if alias:
            return alias
        return self._match(name, self.scenes(), self.cutoff)

    def _audio_input(self) -> Optional[str]:
        """Which input to act on for bare "mute" / "volume 50"."""
        if self.default_audio:
            return self.default_audio
        for i in self.inputs():
            k = str(i.get("inputKind") or "").lower()
            if "audio" in k or "wasapi" in k:
                return str(i.get("inputName"))
        return "Mic/Aux"

    def _item_id(self, scene: str, source: str) -> Optional[int]:
        return self.client.get_scene_item_id(scene, source)

    # ------------------------------------------------------------------ actions
    def scene(self, name: str) -> OBSResult:
        g = self._guard("scene")
        if g:
            return g
        hit = self.resolve_scene(name)
        if hit is None:
            return OBSResult(False, "scene", name, f"no scene matching '{name}'")
        if self.scene_allow and normalize(hit) not in self.scene_allow:
            return OBSResult(False, "scene", hit,
                             f"scene '{hit}' is not voice-switchable "
                             f"(see obs.voice.scenes)")
        ok = self.client.set_current_scene(hit)
        return OBSResult(ok, "scene", hit, f"switched to '{hit}'" if ok
                         else f"could not switch to '{hit}'")

    def _visibility(self, name: str, visible: bool, intent: str) -> OBSResult:
        g = self._guard(intent)
        if g:
            return g
        src = self.resolve_source(name)
        if src is None:
            return OBSResult(False, intent, name, f"no source matching '{name}'")
        if not self._visibility_allowed(src):
            return OBSResult(False, intent, src, f"'{src}' is not voice-controllable "
                                                 f"(see obs.voice.visibility_sources)")
        scene = self.active_scene()
        item = self._item_id(scene, src)
        if item is None:
            return OBSResult(False, intent, src,
                             f"'{src}' is not an item in scene '{scene}'")
        ok = self.client.set_scene_item_enabled(scene, item, visible)
        verb = "shown" if visible else "hidden"
        return OBSResult(ok, intent, src, f"{verb} '{src}'" if ok
                         else f"could not {intent} '{src}'")

    def _visibility_allowed(self, src: str) -> bool:
        return not self.visibility_allow or normalize(src) in self.visibility_allow

    def show(self, name: str) -> OBSResult:
        return self._visibility(name, True, "show")

    def hide(self, name: str) -> OBSResult:
        return self._visibility(name, False, "hide")

    def toggle(self, name: str) -> OBSResult:
        g = self._guard("toggle")
        if g:
            return g
        src = self.resolve_source(name)
        if src is None:
            return OBSResult(False, "toggle", name, f"no source matching '{name}'")
        if not self._visibility_allowed(src):
            return OBSResult(False, "toggle", src, f"'{src}' is not voice-controllable "
                                                   f"(see obs.voice.visibility_sources)")
        scene = self.active_scene()
        item = self._item_id(scene, src)
        if item is None:
            return OBSResult(False, "toggle", src,
                             f"'{src}' is not an item in scene '{scene}'")
        current = True
        for it in (self.client.get_scene_item_list(scene) or []):
            if int(it.get("sceneItemId", -1)) == item:
                current = bool(it.get("sceneItemEnabled", True))
                break
        ok = self.client.set_scene_item_enabled(scene, item, not current)
        verb = "hidden" if current else "shown"
        return OBSResult(ok, "toggle", src, f"{verb} '{src}'" if ok
                         else f"could not toggle '{src}'")

    def set(self, name: str, value: str) -> OBSResult:
        g = self._guard("set")
        if g:
            return g
        src = self.resolve_source(name)
        if src is None:
            return OBSResult(False, "set", name, f"no source matching '{name}'")
        ok = self.client.set_text(src, value)
        return OBSResult(ok, "set", src, f"set '{src}' to '{value}'" if ok
                         else f"'{src}' is not a text source (or OBS refused)")

    def play(self, name: str) -> OBSResult:
        g = self._guard("play")
        if g:
            return g
        src = self.resolve_source(name)
        if src is None:
            return OBSResult(False, "play", name, f"no source matching '{name}'")
        kind = ""
        for i in self.inputs():
            if str(i.get("inputName")) == src:
                kind = str(i.get("inputKind") or "").lower()
                break
        if "browser" in kind:
            ok = self.client.refresh_browser_source(src)
            msg = f"refreshed browser source '{src}'"
        elif any(k in kind for k in ("media", "vlc", "ffmpeg")):
            ok = self.client.trigger_media_action(src, "restart")
            msg = f"restarted media source '{src}'"
        else:
            # "play the dragon counter" — not media; just reveal it.
            return self._visibility(name, True, "play")
        return OBSResult(ok, "play", src, msg if ok else f"could not play '{src}'")

    def mute(self, name: str, muted: bool = True) -> OBSResult:
        intent = "mute" if muted else "unmute"
        g = self._guard(intent)
        if g:
            return g
        src = self.resolve_source(name) if name else self._audio_input()
        if src is None:
            return OBSResult(False, intent, name or "", "no audio input to mute")
        ok = self.client.set_input_mute(src, muted)
        verb = "muted" if muted else "unmuted"
        return OBSResult(ok, intent, src, f"{verb} '{src}'" if ok
                         else f"could not {intent} '{src}'")

    def volume(self, name: str, value: str) -> OBSResult:
        g = self._guard("volume")
        if g:
            return g
        src = self.resolve_source(name) if name else self._audio_input()
        if src is None:
            return OBSResult(False, "volume", name or "", "no audio input to adjust")
        v = str(value or "").strip().lower()
        if v in {"up", "louder", "higher"}:
            cur = self.client.get_input_volume(src)
            mul = (0.5 if cur is None else cur) + 0.1
        elif v in {"down", "quieter", "softer", "lower"}:
            cur = self.client.get_input_volume(src)
            mul = (0.5 if cur is None else cur) - 0.1
        else:
            m = re.search(r"(\d+(?:\.\d+)?)", v)
            if not m:
                return OBSResult(False, "volume", src,
                                 f"can't read a volume from '{value}'")
            num = float(m.group(1))
            # "50" -> 50%; "0.5" -> 50%. >1 is percent, <=1 is a multiplier.
            mul = num / 100.0 if num > 1.0 else num
        mul = max(0.0, min(1.0, mul))
        ok = self.client.set_input_volume(src, mul)
        return OBSResult(ok, "volume", src, f"volume {round(mul * 100)}%",
                         {"mul": round(mul, 3)})

    def record(self, start: bool = True) -> OBSResult:
        intent = "record" if start else "unrecord"
        g = self._guard(intent)
        if g:
            return g
        ok = self.client.start_record() if start else self.client.stop_record()
        verb = "started recording" if start else "stopped recording"
        return OBSResult(ok, intent, "recording", verb if ok else f"could not {intent}")

    def broadcast(self, start: bool = True) -> OBSResult:
        intent = "broadcast" if start else "unbroadcast"
        g = self._guard(intent)
        if g:
            return g
        ok = self.client.start_stream() if start else self.client.stop_stream()
        verb = "started the OBS stream" if start else "stopped the OBS stream"
        return OBSResult(ok, intent, "stream", verb if ok else f"could not {intent}")

    def vcam(self, start: bool = True) -> OBSResult:
        intent = "vcam" if start else "unvcam"
        g = self._guard(intent)
        if g:
            return g
        ok = self.client.start_virtualcam() if start else self.client.stop_virtualcam()
        verb = "started the virtual camera" if start else "stopped the virtual camera"
        return OBSResult(ok, intent, "virtualcam", verb if ok else f"could not {intent}")

    def replay(self) -> OBSResult:
        g = self._guard("replay")
        if g:
            return g
        ok = self.client.save_replay_buffer()
        return OBSResult(ok, "replay", "replay-buffer",
                         "replay buffer saved" if ok else "could not save replay buffer")

    def transition(self, name: str) -> OBSResult:
        g = self._guard("transition")
        if g:
            return g
        hit = self._match(name, KNOWN_TRANSITIONS, self.cutoff)
        if hit is None:
            return OBSResult(False, "transition", name,
                             f"no transition matching '{name}'")
        ok = self.client.set_current_transition(hit)
        return OBSResult(ok, "transition", hit,
                         f"transition set to '{hit}'" if ok else "could not set transition")

    # ------------------------------------------------------------------ entry
    def handle(self, intent: str, target: str = "", value: str = "") -> OBSResult:
        """One call for REST / MCP / CLI / the dispatcher."""
        i = (intent or "").lower().strip()
        t = (target or "").strip()
        v = (value or "").strip()
        if i not in self.SUPPORTED:
            return OBSResult(False, i, t, f"obs cannot handle intent '{i}'")
        if i not in self.intents:
            return OBSResult(False, i, t, f"intent '{i}' not enabled for obs")
        if i == "scene":       return self.scene(t)
        if i == "show":        return self.show(t)
        if i == "hide":        return self.hide(t)
        if i == "toggle":      return self.toggle(t)
        if i == "set":         return self.set(t, v)
        if i == "play":        return self.play(t)
        if i == "mute":        return self.mute(t, True)
        if i == "unmute":      return self.mute(t, False)
        if i == "volume":      return self.volume(t, v)
        if i == "record":      return self.record(True)
        if i == "unrecord":    return self.record(False)
        if i == "vcam":        return self.vcam(True)
        if i == "unvcam":      return self.vcam(False)
        if i == "broadcast":   return self.broadcast(True)
        if i == "unbroadcast": return self.broadcast(False)
        if i == "transition":  return self.transition(t)
        if i in {"replay", "clip"}: return self.replay()
        return OBSResult(False, i, t, f"obs cannot handle intent '{i}'")

    # ------------------------------------------------------------------ status
    def status(self) -> dict:
        out: Dict[str, Any] = {
            "enabled": self.enabled,
            "connected": False,
            "error": None,
            "configured_scene": self.pinned_scene,
            "scene_allowlist": sorted(self.scene_allow),
            "allow_dangerous": self.allow_dangerous,
            "intents": sorted(self.intents),
            "supported_intents": sorted(self.SUPPORTED),
        }
        if not self.enabled:
            out["message"] = "obs.voice.enabled is false"
            return out
        if not self.client.connect():
            out["error"] = self.client.last_error
            return out
        out["connected"] = True
        out["scene"] = self.client.get_current_scene()
        out["scenes"] = self.client.scene_names()
        out["recording"] = self.client.is_recording()
        out["streaming"] = self.client.is_streaming()
        out["replay_active"] = bool(
            (self.client.get_replay_buffer_status() or {}).get("outputActive"))
        try:
            out["virtualcam"] = self.client.get_virtualcam_status()
        except Exception:
            out["virtualcam"] = None
        out["sources"] = [str(i.get("inputName")) for i in
                          (self.client.get_input_list() or [])
                          if i.get("inputName")]
        return out
