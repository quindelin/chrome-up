"""Voice command dispatcher: subscribes to the EventBus and runs side effects.

The bus itself is a pure pub/sub. The dispatcher is the only place that
*does* anything in response to an event. Today it routes two families:

  * OBS control      (scene / mute / volume / record / broadcast / vcam …)
                     -> OBSController over obs-websocket v5
  * live re-stream   (stream / unstream, per platform)
                     -> LiveStreamManager (one ffmpeg per platform)
  * privacy blur     (blur / unblur / "toggle face blur")
                     -> PrivacyManager (clip ffmpeg patches + OBS patch scene)

Tomorrow it can drive anything else that has side effects.

Why split: a pure bus is easy to test (just append, assert history); a
dispatcher is the integration seam against ffmpeg subprocesses, sockets,
and the rest of the world. Mixing them makes the bus hard to test and
the dispatcher impossible to bypass.

The dispatcher runs in a background thread. `start()` is idempotent. Stop
it with `stop()` (called by `Pipeline.shutdown`).
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional

from .events import EventBus
from .livestream import LiveStreamManager, resolve_name
from .obsctl import OBSController
from .privacy import PrivacyManager, is_privacy_target
from .voice import StreamEvent


class CommandDispatcher:
    """Map voice_command events to side effects.

    Intents handled:
      stream   -> start the named target (or all if target is "all" / "*")
      unstream -> stop the named target (or all)
      blur     -> switch face blurring on
      unblur   -> switch it off
      toggle   -> flip it, when the target is faces/privacy/blur
    """

    def __init__(self, bus: EventBus, live: Optional[LiveStreamManager] = None,
                 obs: Optional["OBSController"] = None,
                 events_log: Path | None = None,
                 privacy: Optional["PrivacyManager"] = None):
        self.bus = bus
        self.live = live
        self.obs = obs
        self.privacy = privacy
        self._queue = bus.subscribe()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.processed = 0
        self.last_action: Optional[dict] = None
        self.last_error: Optional[str] = None
        self.events_log = events_log

    def set_live(self, live: LiveStreamManager) -> None:
        self.live = live

    def set_obs(self, obs: "OBSController") -> None:
        self.obs = obs

    def set_privacy(self, privacy: PrivacyManager) -> None:
        self.privacy = privacy

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="command-dispatcher", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    # ------------------------------------------------------------------ loop
    def _loop(self) -> None:
        while not self._stop.is_set():
            self._loop_iteration()
            time.sleep(0.1)

    def _loop_iteration(self) -> None:
        """One drain pass. Exposed so tests can step the dispatcher without
        starting its background thread."""
        while True:
            try:
                ev = self._queue.popleft()
            except IndexError:
                return
            try:
                self._handle(ev)
            except Exception as exc:  # noqa: BLE001
                # never let a handler kill the dispatcher — but record it,
                # otherwise a broken handler looks like a silent no-op
                self.last_error = f"{ev.intent}:{ev.target} -> {exc}"
                if self.events_log:
                    try:
                        with open(self.events_log, "a", encoding="utf-8") as fh:
                            fh.write(f"[dispatcher-error] {ev.text!r} -> {exc}\n")
                    except Exception:
                        pass

    def _handle(self, ev: StreamEvent) -> None:
        if ev.type != "voice_command":
            return
        intent = (ev.intent or "").lower().strip()
        target_raw = (ev.target or "").strip()
        target = resolve_name(target_raw)
        action = None
        status_type = "stream_status"
        emit_status = True

        # Privacy blur first: "blur faces" is unambiguous, and a privacy-ish
        # target on toggle/set belongs to it rather than to the HUD. The
        # manager publishes its own privacy_status event, so don't double up.
        if self.privacy is not None and self.privacy.wants(intent, target_raw):
            res = self.privacy.handle(intent, target_raw, ev.value)
            action = {"intent": "privacy", "target": "faces", "result": res}
            status_type = "privacy_status"
            emit_status = False
        # OBS first: an intent like "record" or "scene" is unambiguously OBS,
        # and `handles()` already filtered out anything the operator didn't
        # enable — so HUD-owned intents (show/hide/…) fall through untouched
        # unless obs.voice.intents opts into them.
        if self.obs is not None and self.obs.handles(intent):
            res = self.obs.handle(intent, target_raw, ev.value)
            action = {"intent": intent, "target": res.target,
                      "result": res.to_dict()}
            status_type = "obs_status"
        elif intent == "stream" and self.live is not None:
            if target in ("all", "*", ""):
                results = self.live.start_all()
                action = {"intent": "stream", "target": "all",
                          "results": results}
            elif target in self.live.targets:
                action = {"intent": "stream", "target": target,
                          "result": self.live.start(target)}
            else:
                action = {"intent": "stream", "target": target_raw,
                          "result": {"ok": False, "message": "unknown target"}}
        elif intent == "unstream" and self.live is not None:
            if target in ("all", "*", ""):
                results = self.live.stop_all()
                action = {"intent": "unstream", "target": "all",
                          "results": results}
            elif target in self.live.targets:
                action = {"intent": "unstream", "target": target,
                          "result": self.live.stop(target)}
            else:
                action = {"intent": "unstream", "target": target_raw,
                          "result": {"ok": False, "message": "unknown target"}}

        if action is not None:
            self.processed += 1
            self.last_action = action
            if not emit_status:
                return
            # publish a status event so HUD agents see the outcome
            self.bus.publish(StreamEvent(
                type=status_type,
                ts=time.time(),
                window_t=ev.window_t,
                text=ev.text,
                intent=action["intent"],
                target=action["target"],
                value=ev.value,
                source="dispatcher",
                confidence=1.0,
                extra={"result": action.get("result") or action.get("results")},
            ))
