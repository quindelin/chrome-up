"""The orchestrator: source -> rolling window -> analyze -> agent -> clip -> publish.

One `run_cycle()` is the whole product. Everything else (CLI, REST, MCP) is a
thin shell over it, which is what makes it agent-operable.
"""
from __future__ import annotations

import json
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .agents import AgentContext, ClipDecision, build_agent
from .buffer import RollingWindow, Window
from .clips import Clip, render_clip
from .config import load_config
from .dispatcher import CommandDispatcher
from .events import EventBus
from .ingest import ReplayBufferSource, Source, build_source, refresh_window
from .livestream import LiveStreamManager
from .obs import OBSClient
from .obsctl import OBSController
from .posting import ClipPoster, new_record
from .privacy import build_privacy
from .publishers import PublishResult, publish_all
from .signals import Analysis, analyze_window
from .stream_title import StreamTitle
from .transcript import Transcript, transcript_for_window
from .util import ensure_dir
from .voice import StreamEvent, build_parser


@dataclass
class CycleResult:
    id: str
    window: Optional[dict] = None
    analysis: Optional[dict] = None
    decisions: List[dict] = field(default_factory=list)
    clips: List[dict] = field(default_factory=list)
    results: List[dict] = field(default_factory=list)
    events: List[dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    source: dict = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "ts": round(self.ts, 3),
            "window": self.window, "analysis": self.analysis,
            "decisions": self.decisions, "clips": self.clips,
            "results": self.results, "events": self.events,
            "notes": self.notes, "source": self.source,
        }


class Pipeline:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.workdir = ensure_dir(Path(cfg["workdir"]))
        self.windows_dir = ensure_dir(self.workdir / "windows")
        self.clips_dir = ensure_dir(self.workdir / "clips")
        self.frames_dir = ensure_dir(self.workdir / "frames")
        self.state_path = self.workdir / "state.json"

        src_cfg = dict(cfg.get("source", {}))
        src_cfg["workdir"] = str(self.workdir)
        src_cfg["obs"] = cfg.get("obs", {})
        self.source: Source = build_source(src_cfg)

        self.window = RollingWindow(float(cfg.get("window", {}).get("seconds", 300)),
                                   self.workdir / "buffer")
        self.agent = build_agent(cfg.get("agent", {}))
        self.voice = build_parser(cfg.get("voice", {}))
        self.events = EventBus(self.workdir / "events.jsonl")
        self.state: Dict[str, Any] = self._load_state()
        self._last_cycle_end_wall = 0.0
        # `serve --loop` runs cycles on a thread while the API approves and
        # rejects: one cycle at a time, and state edits never interleave.
        self._cycle_lock = threading.Lock()
        self._state_lock = threading.RLock()

        # Voice -> OBS. Opt-in: no obs-websocket connection is opened at all
        # unless obs.voice.enabled is true.
        obs_cfg = cfg.get("obs", {}) or {}
        obs_voice = obs_cfg.get("voice", {}) or {}
        self.obs: Optional[OBSController] = None
        if bool(obs_voice.get("enabled", False)):
            self.obs = OBSController(OBSClient(obs_cfg), obs_voice)

        # Live multi-streaming is opt-in: no ffmpeg subprocess is spawned and no
        # watchdog thread is started unless live_streams.enabled is true.
        self.live: Optional[LiveStreamManager] = None
        if bool(cfg.get("live_streams", {}).get("enabled", False)):
            self.live = LiveStreamManager(cfg["live_streams"],
                                          self.workdir / "live")

        # Stream title on every platform that has an API for it. Always
        # built: without credentials each platform just answers ok=false.
        live_cfg = cfg.get("live_streams", {}) or {}
        self.title = StreamTitle(cfg.get("stream_title", {}) or {}, self.workdir,
                                 platforms=[t.get("name") for t in live_cfg.get("targets") or []
                                            if t.get("name")] or None,
                                 on_change=self._title_event)
        if self.live is not None:
            self.live.on_start = self.title.reapply_async

        # The approval queue the phone edits and posts from (docs/CLIP_POSTING.md)
        self.poster = ClipPoster(cfg, self.workdir, self.state, self._state_lock,
                                 self._save_state, on_status=self._clip_event)

        # Privacy blur (face blur, togglable by voice). The OBS driver only
        # needs a socket when it is actually switched on, so the client is
        # created lazily on first use.
        self.privacy = build_privacy(cfg, self.workdir, bus=self.events,
                                     obs_client=self._privacy_obs_client())

        # One dispatcher serves every effect family; only started if at least
        # one of them is actually enabled.
        self.dispatcher: Optional[CommandDispatcher] = None
        if self.obs is not None or self.live is not None or self.privacy.enabled:
            self.dispatcher = CommandDispatcher(self.events, self.live, self.obs,
                                                privacy=self.privacy)
            self.dispatcher.start()
        self.privacy.start()
        # Replay transcript-derived events on warm start (state.jsonl already
        # stores them; the bus does too via the events.jsonl tail).

    def _privacy_obs_client(self):
        """The OBS socket the privacy driver rides on, or None."""
        pcfg = self.cfg.get("privacy", {}) or {}
        if not pcfg.get("enabled", False):
            return None
        if str(pcfg.get("mode", "clip")).lower() not in ("obs", "both"):
            return None
        if self.obs is not None:
            return self.obs.client
        return OBSClient(self.cfg.get("obs", {}) or {})

    # ------------------------------------------------------------------- obs
    def obs_status(self) -> dict:
        """OBS connection + scene/source inventory + which intents are armed."""
        if self.obs is None:
            return {"enabled": False, "connected": False,
                    "message": "obs.voice.enabled is false"}
        return self.obs.status()

    def obs_action(self, intent: str, target: str = "", value: str = "") -> dict:
        """Run one OBS voice action directly (REST / MCP / CLI)."""
        if self.obs is None:
            return {"ok": False, "action": intent, "target": target,
                    "message": "obs voice control disabled (set obs.voice.enabled)"}
        return self.obs.handle(intent, target, value).to_dict()

    # ------------------------------------------------------------------ title
    def _title_event(self, result: dict) -> None:
        self.events.publish(StreamEvent(
            type="stream_title", ts=time.time(), text=result.get("title", ""),
            source="manual", extra={"results": result.get("results", [])}))

    def _clip_event(self, status: dict) -> None:
        self.events.publish(StreamEvent(
            type="clip_status", ts=time.time(), text=status.get("message", ""),
            target=status.get("platform", ""), value=status.get("state", ""),
            source="manual", extra=status))

    def title_status(self) -> dict:
        return self.title.status()

    def title_set(self, title: str, platforms: Optional[List[str]] = None) -> dict:
        return self.title.set(title, platforms)

    # ------------------------------------------------------------------ live
    def live_status(self) -> dict:
        if self.live is None:
            return {"enabled": False, "targets": [], "active_count": 0,
                    "message": "live_streams.enabled is false"}
        return {"enabled": True, **self.live.status()}

    def live_start(self, name: str) -> dict:
        if self.live is None:
            return {"ok": False, "message": "live_streams disabled"}
        return self.live.start(name)

    def live_stop(self, name: str) -> dict:
        if self.live is None:
            return {"ok": False, "message": "live_streams disabled"}
        return self.live.stop(name)

    def live_start_all(self) -> List[dict]:
        return self.live.start_all() if self.live else []

    def live_stop_all(self) -> List[dict]:
        return self.live.stop_all() if self.live else []

    # ------------------------------------------------------------------ privacy
    def privacy_status(self) -> dict:
        """Face-blur switch: is it on, what does it cover, what did it see."""
        return self.privacy.status()

    def privacy_set(self, on: bool) -> dict:
        """Turn face blurring on/off (REST / MCP / CLI / voice)."""
        return self.privacy.set(bool(on))

    def privacy_toggle(self) -> dict:
        return self.privacy.toggle()

    def shutdown(self) -> None:
        """Stop the dispatcher, live ffmpeg processes, and the OBS socket."""
        if self.dispatcher:
            self.dispatcher.stop()
        if self.live:
            self.live.shutdown()
        if self.privacy:
            self.privacy.shutdown()
        if self.obs:
            try:
                self.obs.client.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ state
    def _load_state(self) -> Dict[str, Any]:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"cycles": [], "pending": []}

    def _save_state(self) -> None:
        with self._state_lock:
            self._save_state_to(self.state_path)

    def _save_state_to(self, path: Path) -> None:
        self.state["cycles"] = self.state.get("cycles", [])[-50:]
        path.write_text(json.dumps(self.state, indent=2, default=str), encoding="utf-8")

    # ------------------------------------------------------------------ ingest
    def refresh(self) -> dict:
        refresh_window(self.source, self.window)
        return self.window.to_dict()

    def capture_window(self) -> Window:
        """The 'past five minutes' as one analyzable file."""
        # Fast path: OBS replay buffer already holds exactly that.
        if isinstance(self.source, ReplayBufferSource):
            seg = self.source.save()
            if seg is not None:
                return Window(path=seg.path, start_wall=seg.start_wall,
                              duration=seg.duration, source="replay_buffer",
                              segments=[seg])
        self.refresh()
        wcfg = self.cfg.get("window", {})
        now = time.time()
        end = now
        start = now - float(wcfg.get("seconds", 300))
        return self.window.materialize(start, end, out_dir=self.windows_dir,
                                       name=f"window_{int(now)}")

    # ------------------------------------------------------------------ analysis
    def analyze(self, window: Window, with_frames: bool = True) -> Analysis:
        # Candidate moments are shaped by the same bounds the agent is given, so
        # what the signal layer proposes is already post-able.
        acfg = dict(self.cfg.get("analysis", {}))
        agent_cfg = self.cfg.get("agent", {})
        acfg.setdefault("min_moment_seconds", agent_cfg.get("min_clip_seconds", 10))
        acfg.setdefault("target_moment_seconds", agent_cfg.get("target_clip_seconds", 25))
        acfg.setdefault("max_moment_seconds", agent_cfg.get("max_clip_seconds", 30))
        return analyze_window(window.path, acfg,
                              frames_dir=self.frames_dir if with_frames else None,
                              with_frames=with_frames)

    def transcribe(self, window: Window) -> Transcript:
        return transcript_for_window(window.path, self.cfg.get("analysis", {}))

    def context(self, window: Window, analysis: Analysis,
                transcript: Transcript) -> AgentContext:
        agent_cfg = self.cfg.get("agent", {})
        pub_cfg = self.cfg.get("publish", {})
        constraints = {
            "max_clips_per_window": int(agent_cfg.get("max_clips_per_window", 3)),
            "min_clip_seconds": float(agent_cfg.get("min_clip_seconds", 10)),
            "target_clip_seconds": float(agent_cfg.get("target_clip_seconds", 25)),
            "max_clip_seconds": float(agent_cfg.get("max_clip_seconds", 30)),
            "platforms": list(pub_cfg.get("platforms", [])),
            "default_tags": list(pub_cfg.get("default_tags", [])),
            "window_seconds": float(self.cfg.get("window", {}).get("seconds", 300)),
        }
        # Clip times are relative to their own window, and windows slide every
        # cycle, so the agent is told where recent clips fall in THIS window.
        previous = []
        for a, b, title in self._recent_spans():
            previous.append({"start": round(a - window.start_wall, 2),
                             "end": round(b - window.start_wall, 2), "title": title})
        return AgentContext(
            window=window.to_dict(),
            analysis=analysis,
            transcript=transcript,
            frames=list(analysis.frames),
            constraints=constraints,
            previous=previous,
            source=self.source.status(),
        )

    # ------------------------------------------------------------------ one cycle
    def run_cycle(self, with_frames: bool = True, publish: Optional[bool] = None,
                  agent_name: Optional[str] = None) -> CycleResult:
        with self._cycle_lock:
            return self._run_cycle(with_frames, publish, agent_name)

    def _run_cycle(self, with_frames: bool, publish: Optional[bool],
                   agent_name: Optional[str]) -> CycleResult:
        result = CycleResult(id=uuid.uuid4().hex[:12])
        agent = self.agent
        if agent_name:
            cfg = dict(self.cfg.get("agent", {}))
            cfg["name"] = agent_name
            agent = build_agent(cfg)

        try:
            window = self.capture_window()
        except Exception as exc:  # noqa: BLE001
            result.notes.append(f"capture failed: {exc}")
            self._record(result)
            return result
        result.window = window.to_dict()
        result.source = self.source.status()

        analysis = self.analyze(window, with_frames=with_frames)
        result.analysis = analysis.to_dict()

        transcript = self.transcribe(window)
        if transcript.note:
            result.notes.append(f"transcript: {transcript.note}")

        # Voice command detection: always emit a transcript_chunk event so HUD
        # agents can render live captions; emit voice_command events when the
        # parser recognises an intent.
        self._emit_transcript_chunks(window, transcript)
        result.events.extend(self._emit_voice_commands(window, transcript))

        ctx = self.context(window, analysis, transcript)
        try:
            decisions = agent.propose(ctx) or []
        except Exception as exc:  # noqa: BLE001
            result.notes.append(f"agent {getattr(agent, 'name', '?')} failed: {exc}")
            decisions = []

        threshold = float(self.cfg.get("agent", {}).get("auto_approve_score", 0.62))
        decisions.sort(key=lambda d: d.score, reverse=True)
        decisions, dropped = self._drop_repeats(window, decisions)
        if dropped:
            result.notes.append(f"{dropped} candidate(s) skipped: already clipped in an earlier window")
        decisions = decisions[: int(self.cfg.get("agent", {}).get("max_clips_per_window", 3))]
        approved = [d for d in decisions if d.score >= threshold]
        result.decisions = [d.to_dict() for d in decisions]
        result.notes.append(
            f"{len(decisions)} candidate(s), {len(approved)} above score {threshold}")

        pub_cfg = self.cfg.get("publish", {})
        do_publish = publish if publish is not None else True
        require_approval = bool(pub_cfg.get("require_approval", True))
        live = str(pub_cfg.get("mode", "dry_run")).lower() == "live"
        # queue: always -> every clip waits for the phone, dry_run or not;
        # publish.mode then only decides whether Post reaches the platforms
        queue = require_approval and (
            live or str(pub_cfg.get("queue", "always")).lower() == "always")

        for i, decision in enumerate(approved):
            try:
                clip = render_clip(window.path, decision, self.cfg.get("render", {}),
                                   out_dir=self.clips_dir,
                                   transcript=transcript.slice(decision.start, decision.end),
                                   name=f"{result.id}_{i}", privacy=self.privacy)
            except Exception as exc:  # noqa: BLE001
                result.notes.append(f"render failed for {decision.start:.1f}s: {exc}")
                continue
            clip_info = clip.to_dict()
            clip_info["abs_start"] = round(window.start_wall + decision.start, 3)
            clip_info["abs_end"] = round(window.start_wall + decision.end, 3)
            result.clips.append(clip_info)
            result.notes.extend(clip.notes)

            platforms = decision.platforms or pub_cfg.get("platforms", [])
            if not platforms:
                platforms = ["local"]

            if not do_publish:
                continue
            if queue:
                for res in publish_all(clip, ["local"], {"mode": "dry_run"}, self.workdir):
                    res.message = f"pending approval (publish.mode={'live' if live else 'dry_run'})"
                    result.results.append(res.to_dict())
                with self._state_lock:
                    self.state.setdefault("pending", []).append(
                        new_record(f"{result.id}_{i}", result.id, clip, platforms))
                continue

            for res in publish_all(clip, platforms, pub_cfg, self.workdir):
                result.results.append(res.to_dict())

        self._record(result)
        return result

    def _record(self, result: CycleResult) -> None:
        with self._state_lock:
            cycles = self.state.setdefault("cycles", [])
            cycles.append(result.to_dict())
            keep = int(self._retention().get("cycles", 50))
            if len(cycles) > keep:
                del cycles[:-keep]
            self._save_state()
        try:
            self._cleanup(current=(result.window or {}).get("path"))
        except Exception as exc:  # noqa: BLE001 - housekeeping must never kill a cycle
            result.notes.append(f"cleanup failed: {exc}")

    # ------------------------------------------------------------------ dedupe + retention
    def _retention(self) -> Dict[str, Any]:
        return self.cfg.get("retention", {}) or {}

    def _recent_spans(self) -> List[tuple]:
        """Wall-clock (start, end, title) of clips from recent cycles."""
        out = []
        for cycle in self.state.get("cycles", [])[-10:]:
            for clip in cycle.get("clips", []):
                a, b = clip.get("abs_start"), clip.get("abs_end")
                if a is not None and b is not None:
                    out.append((float(a), float(b), clip.get("decision", {}).get("title", "")))
        return out

    def _drop_repeats(self, window: Window, decisions: List[ClipDecision]):
        """Drop candidates that cover a moment already clipped. Without this the
        same moment is re-proposed every cycle for as long as it stays inside
        the sliding window (5 x at the defaults)."""
        frac = float(self._retention().get("dedupe_overlap", 0.5))
        taken = [(a, b) for a, b, _ in self._recent_spans()]
        kept, dropped = [], 0
        for d in decisions:
            a, b = window.start_wall + d.start, window.start_wall + d.end
            length = max(0.1, b - a)
            if any(max(0.0, min(b, y) - max(a, x)) >= frac * min(length, y - x) for x, y in taken):
                dropped += 1
                continue
            kept.append(d)
            taken.append((a, b))      # two picks in one window must not overlap either
        return kept, dropped

    def _cleanup(self, current: Optional[str] = None) -> None:
        ret = self._retention()
        # windows: keep the newest few (the API's render call may still want one)
        wins = sorted(self.windows_dir.glob("*.mkv"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in wins[int(ret.get("keep_windows", 2)):]:
            if current and str(p) == str(current):
                continue
            p.unlink(missing_ok=True)

        # clips: by age, then by total size; never anything awaiting approval
        pending = {Path(i.get("clip", {}).get("path", "")).stem for i in self.state.get("pending", [])}
        groups: Dict[str, List[Path]] = {}
        outbox = self.workdir / "outbox"       # dry-run / static-hosting copies
        for p in [*self.clips_dir.iterdir(), *(outbox.iterdir() if outbox.is_dir() else [])]:
            if p.is_file():
                groups.setdefault(p.name.split(".")[0], []).append(p)
            elif p.is_dir() and p.name.endswith("_caps"):
                shutil.rmtree(p, ignore_errors=True)      # PNG caption frames: render-time only
        def newest(files): return max(f.stat().st_mtime for f in files)
        order = sorted(groups.items(), key=lambda kv: newest(kv[1]))          # oldest first
        cutoff = time.time() - float(ret.get("clip_hours", 72)) * 3600
        budget = float(ret.get("max_clips_gb", 4.0)) * 1024 ** 3
        total = sum(f.stat().st_size for files in groups.values() for f in files)
        for stem, files in order:
            if stem in pending:
                continue
            if newest(files) < cutoff or total > budget:
                total -= sum(f.stat().st_size for f in files)
                for f in files:
                    f.unlink(missing_ok=True)

    # ------------------------------------------------------------------ approvals
    def pending(self) -> List[dict]:
        return self.poster.pending()

    def approve(self, item_id: str, platforms: Optional[List[str]] = None) -> List[dict]:
        """Post a held clip and wait for it (CLI / MCP / web page). publish.mode
        decides whether it reaches the platforms; the phone uses post()."""
        self.poster.post(item_id, platforms or None, wait=True)
        return self.poster.results(item_id)

    def reject(self, item_id: str) -> bool:
        return self.poster.reject(item_id)

    # ------------------------------------------------------------------ events
    def _emit_transcript_chunks(self, window: Window, transcript: Transcript,
                                 max_chars: int = 140) -> int:
        """Fan out the transcript as `transcript_chunk` events (one per sentence
        or ~max_chars group). HUD agents use these to draw live captions."""
        if not transcript or not transcript.words:
            return 0
        # sentence-ish split using the timing of words
        chunks: List[StreamEvent] = []
        cur_words = []
        for w in transcript.words:
            cur_words.append(w)
            text = " ".join(x.text for x in cur_words)
            if (len(text) >= max_chars
                    or text.rstrip().endswith((".", "!", "?"))):
                self._push_chunk(window, transcript, cur_words, chunks)
                cur_words = []
        if cur_words:
            self._push_chunk(window, transcript, cur_words, chunks)
        for ev in chunks:
            self.events.publish(ev)
        return len(chunks)

    def _push_chunk(self, window: Window, transcript: Transcript,
                    words, out: List[StreamEvent]) -> None:
        if not words:
            return
        t0 = words[0].t0
        t1 = words[-1].t1
        text = " ".join(w.text for w in words).strip()
        if not text:
            return
        out.append(StreamEvent(
            type="transcript_chunk",
            ts=time.time(),
            window_t=t0,
            text=text,
            extra={"t0": t0, "t1": t1,
                   "window_start_wall": window.start_wall,
                   "window_end_wall": window.start_wall + window.duration},
        ))

    def _emit_voice_commands(self, window: Window,
                             transcript: Transcript) -> List[dict]:
        """Run the configured voice parser; publish + return events."""
        events = self.voice.parse(transcript, window_t=0.0)
        # The window spans 300 s but slides 60 s per cycle, so a command stays
        # in view for ~5 cycles. Fire each one once: only commands spoken after
        # the last one already handled (wall clock) go out.
        mark = float(self.state.get("voice_mark", 0.0))
        newest = mark
        out: List[dict] = []
        for ev in events:
            if not ev.intent or ev.intent == "unknown":
                continue
            spoken = window.start_wall + float(ev.window_t or 0.0)
            if spoken <= mark + 0.5:
                continue
            newest = max(newest, spoken)
            # attach window timing metadata for the HUD
            ev.extra.setdefault("window_start_wall", window.start_wall)
            self.events.publish(ev)
            out.append(ev.to_dict())
        if newest > mark:
            self.state["voice_mark"] = newest
        return out

    def inject_command(self, text: str, intent: str = "", target: str = "",
                       value: str = "", source: str = "manual") -> StreamEvent:
        """Manually inject a voice event (e.g. from the REST API or a hotkey).

        With no intent, the text goes through the same grammar as speech, so
        "show lingualens" typed on the phone does what saying it would.
        """
        if not intent and text:
            from .transcript import Transcript
            parsed = self.voice.parse(Transcript(text=text.strip().rstrip(".") + "."))
            if parsed and parsed[0].intent and parsed[0].intent != "unknown":
                intent, target = parsed[0].intent, target or parsed[0].target
                value = value or parsed[0].value
        ev = StreamEvent(
            type="voice_command",
            ts=time.time(),
            window_t=0.0,
            text=text,
            intent=intent or "manual",
            target=target or text,
            value=value,
            confidence=1.0,
            source=source,
        )
        self.events.publish(ev)
        return ev

    # ------------------------------------------------------------------ loop
    def loop(self, seconds: float | None = None, max_cycles: int | None = None) -> None:
        """Run cycles forever (or `max_cycles` times) at window.cycle_seconds."""
        interval = seconds or float(self.cfg.get("window", {}).get("cycle_seconds", 60))
        n = 0
        while max_cycles is None or n < max_cycles:
            try:
                result = self.run_cycle()
                print(f"[autoclip] cycle {result.id}: "
                      f"{len(result.clips)} clip(s), {len(result.results)} publish result(s)")
                for note in result.notes:
                    print(f"[autoclip]   {note}")
            except Exception as exc:  # noqa: BLE001
                print(f"[autoclip] cycle error: {exc}")
            n += 1
            time.sleep(max(1.0, interval))

    def close(self) -> None:
        self.source.close()


def build_pipeline(config_path: str | Path = "autoclip.yaml") -> Pipeline:
    return Pipeline(load_config(config_path))
