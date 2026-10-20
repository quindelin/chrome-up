"""MCP server so any MCP-capable agent gets autoclip as native tools.

Install the SDK:  pip install mcp

Then register it (Claude Code / Cursor / Codex / anything MCP):

  {
    "mcpServers": {
      "autoclip": {
        "command": "python",
        "args": ["-m", "autoclip.mcp_server", "--config", "autoclip.yaml"]
      }
    }
  }

Tools: status, refresh, window, analyze, propose, render, publish, run,
       clips, pending, approve, reject, events_history, command,
       live_status, live_start, live_stop, obs_status, obs_command,
       privacy_status, privacy_set.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .pipeline import Pipeline, build_pipeline
from .util import duration_of

_GLOBAL: Dict[str, Any] = {"pipeline": None}


def _rt(config_path: str) -> Pipeline:
    if _GLOBAL["pipeline"] is None:
        _GLOBAL["pipeline"] = build_pipeline(config_path)
    return _GLOBAL["pipeline"]


def _j(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def build_tools(config_path: str) -> List[dict]:
    """Tool metadata (also used to generate docs / agent instructions)."""
    return [
        {"name": "autoclip_status", "description":
         "Diagnostics: which source is active, how much footage is buffered, "
         "which agent and platforms are available."},
        {"name": "autoclip_refresh", "description":
         "Pull newly recorded footage into the rolling buffer."},
        {"name": "autoclip_window", "description":
         "Materialize the last N seconds (default 300) into one analyzable file."},
        {"name": "autoclip_analyze", "description":
         "Local signals for a window: per-second audio/motion/brightness/scene-cuts, "
         "candidate moments, transcript, and frame stills."},
        {"name": "autoclip_propose", "description":
         "Ask the configured agent (heuristic/llm/remote) which clips to cut."},
        {"name": "autoclip_render", "description":
         "Cut start..end out of a window file, reframe to vertical, burn captions."},
        {"name": "autoclip_publish", "description": "Post a rendered clip to platforms."},
        {"name": "autoclip_run", "description":
         "One full cycle: capture -> analyze -> decide -> clip -> publish."},
        {"name": "autoclip_clips", "description": "List clips produced so far."},
        {"name": "autoclip_pending", "description": "List clips held for human approval."},
        {"name": "autoclip_approve", "description": "Publish a pending clip."},
        {"name": "autoclip_events_history",
         "description": "Last N events (voice_command / transcript_chunk)."},
        {"name": "autoclip_command",
         "description": "Inject a voice command event manually (HUD hotkeys, tests)."},
        {"name": "autoclip_live_status",
         "description": "Per-platform live streaming status."},
        {"name": "autoclip_live_start",
         "description": "Start live streaming to one platform (or 'all')."},
        {"name": "autoclip_live_stop",
         "description": "Stop live streaming to one platform (or 'all')."},
        {"name": "autoclip_obs_status",
         "description": "OBS connection, scenes, sources, armed voice intents."},
        {"name": "autoclip_obs_command",
         "description": "Drive OBS by voice intent: scene switch, mute, volume, "
                        "record, broadcast, virtualcam, replay, show/hide."},
        {"name": "autoclip_privacy_status",
         "description": "Face blur: on/off, which drivers are active, faces seen."},
        {"name": "autoclip_privacy_set",
         "description": "Switch face blurring on, off, or toggle it."},
    ]


def run_stdio(config_path: str = "autoclip.yaml") -> None:
    """Minimal JSON-RPC 2.0 MCP server over stdio (no SDK required)."""
    import sys

    rt = _rt(config_path)
    methods: Dict[str, Any] = {}

    def window_from(arg: Optional[str]) -> Any:
        from .buffer import Window
        if arg:
            return Window(path=Path(arg), start_wall=0.0, duration=duration_of(arg),
                          source="external")
        return rt.capture_window()

    def tool(name: str, desc: str, schema: dict, handler):
        methods[f"tools/call::{name}"] = handler
        return {"name": name, "description": desc, "inputSchema": schema}

    tools = [
        tool("autoclip_status", "Diagnostics for source, buffer, agent and platforms.",
             {"type": "object", "properties": {}},
             lambda a: {"source": rt.source.status(), "window": rt.window.to_dict(),
                        "agent": getattr(rt.agent, "name", "?"),
                        "publish_mode": rt.cfg.get("publish", {}).get("mode")}),
        tool("autoclip_window", "Materialize the last N seconds into one file.",
             {"type": "object", "properties": {}},
             lambda a: rt.capture_window().to_dict()),
        tool("autoclip_analyze", "Signals + transcript + frames for a window.",
             {"type": "object",
              "properties": {"window_path": {"type": "string"},
                             "with_frames": {"type": "boolean"}}},
             lambda a: (lambda w: {
                 "window": w.to_dict(),
                 "analysis": rt.analyze(w, bool(a.get("with_frames", True))).to_dict(),
                 "transcript": rt.transcribe(w).to_dict()})(window_from(a.get("window_path")))),
        tool("autoclip_propose", "Ask the agent for clip decisions.",
             {"type": "object",
              "properties": {"window_path": {"type": "string"}, "agent": {"type": "string"}}},
             lambda a: _propose(rt, a)),
        tool("autoclip_render", "Cut and caption one clip.",
             {"type": "object",
              "properties": {"window_path": {"type": "string"}, "start": {"type": "number"},
                             "end": {"type": "number"}, "title": {"type": "string"},
                             "caption": {"type": "string"},
                             "platforms": {"type": "array", "items": {"type": "string"}}},
              "required": ["window_path", "start", "end"]},
             lambda a: _render(rt, a)),
        tool("autoclip_publish", "Publish a rendered clip.",
             {"type": "object",
              "properties": {"clip_path": {"type": "string"},
                             "platforms": {"type": "array", "items": {"type": "string"}},
                             "live": {"type": "boolean"}},
              "required": ["clip_path"]},
             lambda a: _publish(rt, a)),
        tool("autoclip_run", "Run one full cycle.",
             {"type": "object",
              "properties": {"agent": {"type": "string"}, "publish": {"type": "boolean"}}},
             lambda a: rt.run_cycle(publish=a.get("publish"), agent_name=a.get("agent")).to_dict()),
        tool("autoclip_clips", "List produced clips.",
             {"type": "object", "properties": {}},
             lambda a: {"clips": [c for cyc in rt.state.get("cycles", [])
                                  for c in cyc.get("clips", [])][-50:]}),
        tool("autoclip_pending", "Clips awaiting approval.",
             {"type": "object", "properties": {}},
             lambda a: {"pending": rt.pending()}),
        tool("autoclip_approve", "Publish a pending clip.",
             {"type": "object",
              "properties": {"id": {"type": "string"},
                             "platforms": {"type": "array", "items": {"type": "string"}}},
              "required": ["id"]},
             lambda a: {"results": rt.approve(a["id"], a.get("platforms"))}),
        tool("autoclip_events_history", "Recent voice/transcript events (for polling).",
             {"type": "object",
              "properties": {"n": {"type": "integer", "default": 50},
                             "type": {"type": "string"}}},
             lambda a: {"events": [e.to_dict() for e in
                                    rt.events.history(int(a.get("n", 50)))]}),
        tool("autoclip_command", "Inject a voice command event.",
             {"type": "object",
              "properties": {"text": {"type": "string"},
                             "intent": {"type": "string"},
                             "target": {"type": "string"},
                             "value": {"type": "string"},
                             "source": {"type": "string", "default": "mcp"}},
              "required": ["text"]},
             lambda a: {"event": rt.inject_command(
                 text=a["text"], intent=a.get("intent", ""),
                 target=a.get("target", ""), value=a.get("value", ""),
                 source=a.get("source", "mcp")).to_dict()}),
        tool("autoclip_live_status", "Live streaming status per platform.",
             {"type": "object", "properties": {}},
             lambda a: rt.live_status()),
        tool("autoclip_live_start", "Start streaming to a platform ('all' = every target).",
             {"type": "object",
              "properties": {"name": {"type": "string"}}, "required": ["name"]},
             lambda a: (rt.live_start_all() if a["name"].lower() in ("all", "*", "everywhere")
                        else [rt.live_start(a["name"])])),
        tool("autoclip_live_stop", "Stop streaming to a platform ('all' = every target).",
             {"type": "object",
              "properties": {"name": {"type": "string"}}, "required": ["name"]},
             lambda a: (rt.live_stop_all() if a["name"].lower() in ("all", "*", "everywhere")
                        else [rt.live_stop(a["name"])])),
        tool("autoclip_obs_status", "OBS scenes, sources, and armed voice intents.",
             {"type": "object", "properties": {}},
             lambda a: rt.obs_status()),
        tool("autoclip_obs_command",
             "Drive OBS. intents: scene, show, hide, toggle, set, play, mute, "
             "unmute, volume, record, unrecord, vcam, unvcam, broadcast, "
             "unbroadcast, replay, clip, transition.",
             {"type": "object",
              "properties": {
                  "intent": {"type": "string"},
                  "target": {"type": "string",
                             "description": "scene/source name as spoken"},
                  "value": {"type": "string",
                            "description": "for set (text), volume (number)"},
              },
              "required": ["intent"]},
             lambda a: rt.obs_action(a["intent"], a.get("target", ""),
                                     a.get("value", ""))),
        tool("autoclip_privacy_status", "Face blur state: on/off, drivers, faces seen.",
             {"type": "object", "properties": {}},
             lambda a: rt.privacy_status()),
        tool("autoclip_privacy_set", "Turn face blurring on, off, or toggle it.",
             {"type": "object",
              "properties": {"on": {"type": "boolean"},
                             "toggle": {"type": "boolean"}}},
             lambda a: (rt.privacy_toggle() if (a.get("toggle") or a.get("on") is None)
                        else rt.privacy_set(bool(a["on"])))),
    ]

    def send(obj: dict) -> None:
        data = json.dumps(obj)
        sys.stdout.write(f"Content-Length: {len(data.encode())}\r\n\r\n{data}")
        sys.stdout.flush()

    def read() -> Optional[dict]:
        headers: Dict[str, str] = {}
        while True:
            line = sys.stdin.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                break
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        length = int(headers.get("content-length", "0"))
        if not length:
            return None
        body = sys.stdin.read(length)
        try:
            return json.loads(body)
        except Exception:
            return None

    while True:
        msg = read()
        if msg is None:
            break
        mid = msg.get("id")
        method = msg.get("method")
        params = msg.get("params") or {}
        try:
            if method == "initialize":
                send({"jsonrpc": "2.0", "id": mid, "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "autoclip", "version": "0.1.0"}}})
            elif method == "tools/list":
                send({"jsonrpc": "2.0", "id": mid,
                      "result": {"tools": [{k: v for k, v in t.items()} for t in tools]}})
            elif method == "tools/call":
                name = params.get("name")
                args = params.get("arguments") or {}
                handler = methods.get(f"tools/call::{name}")
                if handler is None:
                    send({"jsonrpc": "2.0", "id": mid, "error":
                          {"code": -32601, "message": f"unknown tool {name}"}})
                else:
                    out = handler(args)
                    send({"jsonrpc": "2.0", "id": mid,
                          "result": {"content": [{"type": "text", "text": _j(out)}]}})
            elif method in ("notifications/initialized", "initialized"):
                continue
            elif mid is None:
                continue
            else:
                send({"jsonrpc": "2.0", "id": mid,
                      "error": {"code": -32601, "message": f"unsupported method {method}"}})
        except Exception as exc:  # noqa: BLE001
            send({"jsonrpc": "2.0", "id": mid,
                  "error": {"code": -32000, "message": str(exc)}})


# --------------------------------------------------------------------------- handlers
def _propose(rt: Pipeline, args: dict) -> dict:
    from .agents import build_agent
    from .buffer import Window

    if args.get("window_path"):
        win = Window(path=Path(args["window_path"]), start_wall=0.0,
                     duration=duration_of(args["window_path"]), source="external")
    else:
        win = rt.capture_window()
    analysis = rt.analyze(win)
    transcript = rt.transcribe(win)
    ctx = rt.context(win, analysis, transcript)
    agent = rt.agent
    if args.get("agent"):
        acfg = dict(rt.cfg.get("agent", {}))
        acfg["name"] = args["agent"]
        agent = build_agent(acfg)
    decisions = agent.propose(ctx) or []
    return {"window": win.to_dict(), "agent": getattr(agent, "name", "?"),
            "decisions": [d.to_dict() for d in decisions]}


def _render(rt: Pipeline, args: dict) -> dict:
    from .agents import ClipDecision
    from .clips import render_clip

    decision = ClipDecision(start=float(args["start"]), end=float(args["end"]),
                            title=args.get("title", ""), caption=args.get("caption", ""),
                            platforms=args.get("platforms", []))
    clip = render_clip(Path(args["window_path"]), decision, rt.cfg.get("render", {}),
                       out_dir=rt.clips_dir)
    return clip.to_dict()


def _publish(rt: Pipeline, args: dict) -> dict:
    from .agents import ClipDecision
    from .clips import Clip
    from .publishers import publish_all

    decision = ClipDecision(start=0.0, end=0.0, title=args.get("title", ""),
                            caption=args.get("caption", ""),
                            platforms=args.get("platforms", []))
    clip = Clip(path=Path(args["clip_path"]), start=0.0, end=0.0, duration=0.0,
                decision=decision)
    pub_cfg = dict(rt.cfg.get("publish", {}))
    if args.get("live"):
        pub_cfg["mode"] = "live"
    results = publish_all(clip, args.get("platforms") or pub_cfg.get("platforms", ["local"]),
                          pub_cfg, rt.workdir)
    return {"results": [r.to_dict() for r in results]}


def main() -> None:
    parser = argparse.ArgumentParser(description="autoclip MCP server (stdio)")
    parser.add_argument("--config", default="autoclip.yaml")
    parser.add_argument("--list-tools", action="store_true",
                        help="print tool metadata and exit")
    args = parser.parse_args()
    if args.list_tools:
        print(_j(build_tools(args.config)))
        return
    run_stdio(args.config)


if __name__ == "__main__":
    main()
