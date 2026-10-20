"""REST + OpenAPI surface. Any agent that can make an HTTP call can drive this.

GET  /api/autoclip/schema            -> machine-readable list of every operation
GET  /api/autoclip/status            -> source/window/publisher diagnostics
POST /api/autoclip/refresh           -> pull new footage into the rolling buffer
POST /api/autoclip/window            -> materialize the past N minutes as one file
POST /api/autoclip/analyze           -> signals + transcript + frames for a window
POST /api/autoclip/propose           -> ask the agent for clip decisions
POST /api/autoclip/render            -> cut + caption one clip
POST /api/autoclip/publish           -> push a clip to platforms
POST /api/autoclip/run               -> one full cycle (the whole product)
GET  /api/autoclip/clips             -> everything produced so far
GET  /api/autoclip/pending           -> clips held for approval
GET  /api/autoclip/stack             -> whole-box health for the companion app
POST /api/autoclip/approve/{id}      -> publish a held clip
POST /api/autoclip/reject/{id}       -> drop a held clip

Voice / HUD integration (see docs/VOICE_COMMANDS.md):
GET  /api/autoclip/events            -> Server-Sent Events stream of StreamEvents
GET  /api/autoclip/events/history    -> last N events (JSON)
POST /api/autoclip/command           -> inject a manual voice event (testing / hotkeys)
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agents import ClipDecision
from .buffer import Window
from .clips import render_clip
from .config import load_config
from .pipeline import Pipeline, build_pipeline
from .publishers import available_platforms, publish_all
from .stack import stack_status


# --------------------------------------------------------------------------- schemas
class AnalyzeRequest(BaseModel):
    window_path: Optional[str] = None
    with_frames: bool = True


class ProposeRequest(BaseModel):
    window_path: Optional[str] = None
    agent: Optional[str] = None
    with_frames: bool = True


class RenderRequest(BaseModel):
    window_path: str
    start: float
    end: float
    title: str = ""
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    score: float = 1.0
    name: Optional[str] = None


class PublishRequest(BaseModel):
    clip_path: str
    platforms: List[str] = Field(default_factory=list)
    title: str = ""
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    live: bool = False


class RunRequest(BaseModel):
    agent: Optional[str] = None
    publish: Optional[bool] = None
    with_frames: bool = True


class CommandRequest(BaseModel):
    """Manually inject a voice event (used by HUD hotkeys, tests, WebSocket bridges)."""
    text: str
    intent: str = ""
    target: str = ""
    value: str = ""
    source: str = "manual"
    confidence: float = 1.0


class OBSRequest(BaseModel):
    """Run one OBS voice action directly, bypassing speech."""
    intent: str
    target: str = ""
    value: str = ""


class PrivacyRequest(BaseModel):
    """Face blur switch: on / off / toggle."""
    on: Optional[bool] = None
    toggle: bool = False


# --------------------------------------------------------------------------- app
def create_app(pipeline: Optional[Pipeline] = None, config_path: str = "autoclip.yaml") -> FastAPI:
    cfg = pipeline.cfg if pipeline else load_config(config_path)
    rt = pipeline or build_pipeline(config_path)

    app = FastAPI(title="autoclip", version="0.1.0",
                  description="Rolling-buffer clip agent for POV streams (OBS -> glasses -> social).")
    app.state.pipeline = rt
    app.state.cfg = cfg

    # The OBS browser overlay runs on a different port, so it needs CORS to
    # read /api/autoclip/privacy and subscribe to /api/autoclip/events.
    scfg = cfg.get("server", {}) or {}
    if scfg.get("cors", True):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(scfg.get("cors_origins") or ["*"]),
            allow_methods=["*"], allow_headers=["*"], allow_credentials=False)

    outbox = Path(cfg["workdir"]) / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    app.mount("/outbox", StaticFiles(directory=str(outbox)), name="outbox")

    async def auth(authorization: str = Header(default="")) -> None:
        token = str(cfg.get("server", {}).get("api_token") or "")
        if not token:
            return
        if authorization != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="bad or missing bearer token")

    # ------------------------------------------------------------------ schema
    @app.get("/api/autoclip/schema")
    async def schema() -> JSONResponse:
        """Self-describing contract: an agent can read this and know everything."""
        return JSONResponse({
            "version": "0.1.0",
            "operations": [
                {"name": "status", "method": "GET", "path": "/api/autoclip/status",
                 "description": "source/window/publisher diagnostics"},
                {"name": "refresh", "method": "POST", "path": "/api/autoclip/refresh",
                 "description": "pull new footage into the rolling buffer"},
                {"name": "window", "method": "POST", "path": "/api/autoclip/window",
                 "description": "materialize the last N seconds into one file"},
                {"name": "analyze", "method": "POST", "path": "/api/autoclip/analyze",
                 "body": {"window_path": "optional absolute path; default = capture a fresh window",
                          "with_frames": "bool"}},
                {"name": "propose", "method": "POST", "path": "/api/autoclip/propose",
                 "body": {"agent": "heuristic | llm | remote", "with_frames": "bool"}},
                {"name": "render", "method": "POST", "path": "/api/autoclip/render",
                 "body": {"window_path": "str", "start": "seconds", "end": "seconds",
                          "title": "str", "caption": "str", "hashtags": ["str"],
                          "platforms": ["str"]}},
                {"name": "publish", "method": "POST", "path": "/api/autoclip/publish",
                 "body": {"clip_path": "str", "platforms": ["str"], "live": "bool"}},
                {"name": "run", "method": "POST", "path": "/api/autoclip/run",
                 "description": "one full cycle: capture -> analyze -> decide -> clip -> publish",
                 "body": {"agent": "optional", "publish": "optional bool"}},
                {"name": "clips", "method": "GET", "path": "/api/autoclip/clips"},
                {"name": "pending", "method": "GET", "path": "/api/autoclip/pending"},
                {"name": "approve", "method": "POST", "path": "/api/autoclip/approve/{id}"},
                {"name": "reject", "method": "POST", "path": "/api/autoclip/reject/{id}"},
                {"name": "events", "method": "GET", "path": "/api/autoclip/events",
                 "description": "SSE stream of voice_command + transcript_chunk events"},
                {"name": "events_history", "method": "GET", "path": "/api/autoclip/events/history",
                 "description": "last N events as JSON (for polling HUD agents)"},
                {"name": "command", "method": "POST", "path": "/api/autoclip/command",
                 "body": {"text": "str", "intent": "str?", "target": "str?",
                          "value": "str?", "source": "str?"}},
                {"name": "stack", "method": "GET", "path": "/api/autoclip/stack",
                 "description": "whole-box health: ingest/program live + bitrate, restreams, host, queue"},
                {"name": "live_status", "method": "GET", "path": "/api/autoclip/live",
                 "description": "per-platform live status"},
                {"name": "live_start", "method": "POST",
                 "path": "/api/autoclip/live/start/{name}"},
                {"name": "live_stop", "method": "POST",
                 "path": "/api/autoclip/live/stop/{name}"},
                {"name": "live_start_all", "method": "POST",
                 "path": "/api/autoclip/live/start_all"},
                {"name": "live_stop_all", "method": "POST",
                 "path": "/api/autoclip/live/stop_all"},
                {"name": "obs_status", "method": "GET",
                 "path": "/api/autoclip/obs",
                 "description": "OBS scenes, sources, armed intents"},
                {"name": "obs_command", "method": "POST",
                 "path": "/api/autoclip/obs/command",
                 "body": {"intent": "str", "target": "str?", "value": "str?"}},
                {"name": "privacy_status", "method": "GET",
                 "path": "/api/autoclip/privacy",
                 "description": "face blur: on/off, which drivers, faces seen"},
                {"name": "privacy_set", "method": "POST",
                 "path": "/api/autoclip/privacy",
                 "body": {"on": "bool?", "toggle": "bool"}},
            ],
            "agents": ["heuristic", "llm", "remote"],
            "voice_parsers": ["regex", "llm", "off"],
            "voice_intents": ["show", "hide", "toggle", "set", "play", "add",
                              "clip", "stream", "unstream", "scene", "mute",
                              "unmute", "volume", "record", "unrecord", "vcam",
                              "unvcam", "broadcast", "unbroadcast", "replay",
                              "transition", "blur", "unblur"],
            "event_types": ["voice_command", "transcript_chunk", "stream_gap",
                            "stream_status", "obs_status", "privacy_status"],
            "obs_intents": sorted((cfg.get("obs", {}).get("voice", {})
                                   or {}).get("intents", []) or []),
            "live_platforms": [t.get("name") for t in
                               (cfg.get("live_streams", {}).get("targets") or [])],
            "platforms": available_platforms(),
            "defaults": {
                "window_seconds": cfg.get("window", {}).get("seconds"),
                "publish_mode": cfg.get("publish", {}).get("mode"),
                "platforms": cfg.get("publish", {}).get("platforms"),
                "auto_approve_score": cfg.get("agent", {}).get("auto_approve_score"),
                "voice_parser": cfg.get("voice", {}).get("name"),
            },
        })

    # ------------------------------------------------------------------ status
    @app.get("/api/autoclip/status")
    async def status(_: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse({
            "workdir": str(rt.workdir),
            "source": rt.source.status(),
            "window": rt.window.to_dict(),
            "agent": getattr(rt.agent, "name", "?"),
            "agents_available": ["heuristic", "llm", "remote"],
            "platforms_available": available_platforms(),
            "publish_mode": cfg.get("publish", {}).get("mode"),
            "pending": len(rt.pending()),
            "cycles": len(rt.state.get("cycles", [])),
        })

    @app.post("/api/autoclip/refresh")
    async def refresh(_: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(rt.refresh))

    @app.post("/api/autoclip/window")
    async def window(_: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        try:
            win: Window = await run_in_threadpool(rt.capture_window)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=409, detail=str(exc))
        return JSONResponse(win.to_dict())

    # ------------------------------------------------------------------ analysis
    @app.post("/api/autoclip/analyze")
    async def analyze(body: AnalyzeRequest, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(_analyze, rt, body))

    def _analyze(rt: Pipeline, body: AnalyzeRequest) -> dict:
        if body.window_path:
            win = Window(path=Path(body.window_path), start_wall=0.0,
                         duration=0.0, source="external")
        else:
            win = rt.capture_window()
        analysis = rt.analyze(win, with_frames=body.with_frames)
        transcript = rt.transcribe(win)
        return {"window": win.to_dict(), "analysis": analysis.to_dict(),
                "transcript": transcript.to_dict()}

    @app.post("/api/autoclip/propose")
    async def propose(body: ProposeRequest, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(_propose, rt, body))

    def _propose(rt: Pipeline, body: ProposeRequest) -> dict:
        from .agents import build_agent

        if body.window_path:
            win = Window(path=Path(body.window_path), start_wall=0.0,
                         duration=0.0, source="external")
        else:
            win = rt.capture_window()
        analysis = rt.analyze(win, with_frames=body.with_frames)
        transcript = rt.transcribe(win)
        ctx = rt.context(win, analysis, transcript)

        agent = rt.agent
        if body.agent:
            acfg = dict(rt.cfg.get("agent", {}))
            acfg["name"] = body.agent
            agent = build_agent(acfg)
        decisions = agent.propose(ctx) or []
        return {"window": win.to_dict(), "agent": getattr(agent, "name", "?"),
                "decisions": [d.to_dict() for d in decisions],
                "moments": [m.to_dict() for m in analysis.moments],
                "transcript": transcript.to_dict()}

    # ------------------------------------------------------------------ render
    @app.post("/api/autoclip/render")
    async def render(body: RenderRequest, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(_render, rt, body))

    def _render(rt: Pipeline, body: RenderRequest) -> dict:
        decision = ClipDecision(start=body.start, end=body.end, score=body.score,
                                title=body.title, caption=body.caption,
                                hashtags=body.hashtags, platforms=body.platforms)
        clip = render_clip(Path(body.window_path), decision, rt.cfg.get("render", {}),
                           out_dir=rt.clips_dir, name=body.name)
        return clip.to_dict()

    @app.post("/api/autoclip/publish")
    async def publish(body: PublishRequest, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(_publish, rt, body))

    def _publish(rt: Pipeline, body: PublishRequest) -> dict:
        from .clips import Clip

        path = Path(body.clip_path)
        decision = ClipDecision(start=0.0, end=0.0, score=1.0, title=body.title,
                                caption=body.caption, hashtags=body.hashtags,
                                platforms=body.platforms)
        clip = Clip(path=path, start=0.0, end=0.0, duration=0.0, decision=decision)
        pub_cfg = dict(rt.cfg.get("publish", {}))
        if body.live:
            pub_cfg["mode"] = "live"
        results = publish_all(clip, body.platforms or pub_cfg.get("platforms", ["local"]),
                              pub_cfg, rt.workdir)
        return {"results": [r.to_dict() for r in results]}

    # ------------------------------------------------------------------ run
    @app.post("/api/autoclip/run")
    async def run(body: RunRequest, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        result = await run_in_threadpool(
            rt.run_cycle, body.with_frames, body.publish, body.agent)
        return JSONResponse(result.to_dict())

    @app.get("/api/autoclip/clips")
    async def clips(_: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        out = []
        for cycle in rt.state.get("cycles", []):
            for clip in cycle.get("clips", []):
                out.append({"cycle": cycle["id"], "ts": cycle["ts"], **clip})
        return JSONResponse({"clips": out[-100:]})

    @app.get("/api/autoclip/pending")
    async def pending(_: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse({"pending": rt.pending()})

    @app.post("/api/autoclip/approve/{item_id}")
    async def approve(item_id: str, platforms: Optional[List[str]] = None,
                      _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        try:
            return JSONResponse({"results": await run_in_threadpool(rt.approve, item_id, platforms)})
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @app.post("/api/autoclip/reject/{item_id}")
    async def reject(item_id: str, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse({"rejected": await run_in_threadpool(rt.reject, item_id)})

    @app.get("/", response_model=None)
    async def index(request: Request):
        # browsers get the approval queue page; agents get the pointer JSON
        if "text/html" in request.headers.get("accept", ""):
            return HTMLResponse((Path(__file__).parent / "approve.html").read_text(encoding="utf-8"))
        return {"service": "autoclip", "docs": "/docs", "schema": "/api/autoclip/schema"}

    @app.get("/api/autoclip/outbox/{name}")
    async def outbox_file(name: str) -> FileResponse:
        path = outbox / name
        if not path.exists():
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(path)

    # ------------------------------------------------------------------ events
    @app.get("/api/autoclip/events")
    async def events(_: None = Depends(auth)):
        """Server-Sent Events: HUD agent subscribes here to react in real time.

        Wire format is one JSON object per line, prefixed with "data: " as per
        the SSE spec. Clients can use any EventSource implementation.
        """
        rt: Pipeline = app.state.pipeline
        queue = rt.events.subscribe()
        sentinel = object()

        async def stream():
            try:
                # initial heartbeat
                yield ": connected\n\n"
                while True:
                    ev = await run_in_threadpool(_next_with_timeout, queue, 15.0, sentinel)
                    if ev is sentinel:
                        yield ": keepalive\n\n"
                        continue
                    yield f"data: {json.dumps(ev.to_dict())}\n\n"
            finally:
                rt.events.unsubscribe(queue)

        from starlette.responses import StreamingResponse
        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    @app.get("/api/autoclip/events/history")
    async def events_history(n: int = 100,
                             type: Optional[str] = None,
                             _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        items = [e.to_dict() for e in rt.events.history(int(n))]
        if type:
            items = [e for e in items if e.get("type") == type]
        return JSONResponse({"events": items})

    @app.post("/api/autoclip/command")
    async def command(body: CommandRequest, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        ev = rt.inject_command(text=body.text, intent=body.intent,
                               target=body.target, value=body.value,
                               source=body.source)
        ev.confidence = float(body.confidence)
        return JSONResponse({"event": ev.to_dict()})

    # ------------------------------------------------------------------ stack
    @app.get("/api/autoclip/stack")
    async def stack(_: None = Depends(auth)) -> JSONResponse:
        """Everything the companion app shows, in one poll."""
        return JSONResponse(await run_in_threadpool(stack_status, cfg, app.state.pipeline))

    # ------------------------------------------------------------------ live
    @app.get("/api/autoclip/live")
    async def live_status(_: None = Depends(auth)) -> JSONResponse:
        """Per-platform live status: which targets exist and which are active."""
        rt: Pipeline = app.state.pipeline
        return JSONResponse(rt.live_status())

    @app.post("/api/autoclip/live/start/{name}")
    async def live_start(name: str, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(rt.live_start, name))

    @app.post("/api/autoclip/live/stop/{name}")
    async def live_stop(name: str, _: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(rt.live_stop, name))

    @app.post("/api/autoclip/live/start_all")
    async def live_start_all(_: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse({"results": await run_in_threadpool(rt.live_start_all)})

    @app.post("/api/autoclip/live/stop_all")
    async def live_stop_all(_: None = Depends(auth)) -> JSONResponse:
        rt: Pipeline = app.state.pipeline
        return JSONResponse({"results": await run_in_threadpool(rt.live_stop_all)})

    # ------------------------------------------------------------------- obs
    @app.get("/api/autoclip/obs")
    async def obs_status(_: None = Depends(auth)) -> JSONResponse:
        """OBS connection state, scene/source inventory, armed intents."""
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(rt.obs_status))

    @app.post("/api/autoclip/obs/command")
    async def obs_command(body: OBSRequest, _: None = Depends(auth)) -> JSONResponse:
        """Run one OBS action: {"intent":"scene","target":"map"}."""
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(
            rt.obs_action, body.intent, body.target, body.value))

    # ---------------------------------------------------------------- privacy
    @app.get("/api/autoclip/privacy")
    async def privacy_status(_: None = Depends(auth)) -> JSONResponse:
        """Face blur: is it on, what does it cover, what did the detector see."""
        rt: Pipeline = app.state.pipeline
        return JSONResponse(await run_in_threadpool(rt.privacy_status))

    @app.post("/api/autoclip/privacy")
    async def privacy_set(body: PrivacyRequest, _: None = Depends(auth)) -> JSONResponse:
        """Switch face blurring: {"on": true}, {"on": false} or {"toggle": true}."""
        rt: Pipeline = app.state.pipeline
        if body.toggle or body.on is None:
            return JSONResponse(await run_in_threadpool(rt.privacy_toggle))
        return JSONResponse(await run_in_threadpool(rt.privacy_set, bool(body.on)))

    return app


def _next_with_timeout(queue, timeout: float, sentinel):
    """Block up to `timeout` seconds on a queue; return `sentinel` on timeout."""
    import queue as _q
    try:
        return queue.popleft()
    except IndexError:
        pass
    # The deque doesn't have a blocking pop, so spin briefly. Good enough
    # for an in-process pub/sub; the SSE layer's `run_in_threadpool` is
    # what yields control back to the event loop.
    import time
    end = time.time() + timeout
    while time.time() < end:
        try:
            return queue.popleft()
        except IndexError:
            time.sleep(0.25)
    return sentinel


def serve(config_path: str = "autoclip.yaml", host: str | None = None, port: int | None = None,
          loop: bool = False, every: float | None = None) -> None:
    """REST server. With `loop`, the cycle loop runs on a thread of the same
    process, so voice commands, live restreams and the approval queue the API
    shows are the ones the loop actually drives."""
    import threading
    import uvicorn

    cfg = load_config(config_path)
    rt = build_pipeline(config_path)
    app = create_app(pipeline=rt)
    if loop:
        threading.Thread(target=rt.loop, kwargs={"seconds": every},
                         name="autoclip-loop", daemon=True).start()
    # behind a path-stripping proxy (Caddy /autoclip/*) so /docs finds its schema
    uvicorn.run(app, host=host or cfg["server"].get("host", "0.0.0.0"),
                port=int(port or cfg["server"].get("port", 8899)), log_level="info",
                root_path=str(cfg["server"].get("root_path") or ""))
