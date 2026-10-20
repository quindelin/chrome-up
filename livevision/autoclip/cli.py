"""Command line. Everything the REST API and MCP server can do, in one binary.

  python -m autoclip status
  python -m autoclip run                 # one cycle
  python -m autoclip loop                # keep watching, clip, publish
  python -m autoclip propose --agent llm
  python -m autoclip render --window var/autoclip/windows/window_1.mkv --start 42 --end 73
  python -m autoclip serve               # REST + OpenAPI on :8899
  python -m autoclip serve --loop        # both, one process (the VPS runs this)
  python -m autoclip mcp                 # MCP stdio server for agents

Live multi-streaming (see docs/LIVE_STREAMING.md):
  python -m autoclip live                # per-platform status
  python -m autoclip live start twitch
  python -m autoclip live stop youtube
  python -m autoclip live start-all | stop-all

OBS voice control (see docs/OBS_VOICE_CONTROL.md):
  python -m autoclip obs                    # scenes, sources, armed intents
  python -m autoclip obs scene map
  python -m autoclip obs mute mic
  python -m autoclip obs volume 50
  python -m autoclip obs record | unrecord | broadcast

Stream title (see docs/STREAM_TITLE.md):
  python -m autoclip title                  # last title + per-platform results
  python -m autoclip title "Walking Shibuya at night"
  python -m autoclip title-auth twitch      # laptop: OAuth once, prints .env lines

Privacy blur (see docs/PRIVACY_BLUR.md):
  python -m autoclip privacy                # on/off, drivers, faces seen
  python -m autoclip privacy on | off | toggle
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .pipeline import build_pipeline


def _print(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="autoclip", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="autoclip.yaml")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="source / buffer / agent diagnostics")
    sub.add_parser("window", help="materialize the past N minutes into one file")
    p_run = sub.add_parser("run", help="one full cycle")
    p_run.add_argument("--agent", default=None)
    p_run.add_argument("--no-publish", action="store_true")
    p_run.add_argument("--no-frames", action="store_true")
    p_loop = sub.add_parser("loop", help="run cycles forever")
    p_loop.add_argument("--cycles", type=int, default=None)
    p_loop.add_argument("--every", type=float, default=None)
    p_prop = sub.add_parser("propose", help="agent clip decisions for the current window")
    p_prop.add_argument("--agent", default=None)
    sub.add_parser("analyze", help="signals + transcript for the current window")
    p_rend = sub.add_parser("render", help="cut + caption one clip")
    p_rend.add_argument("--window", required=True)
    p_rend.add_argument("--start", type=float, required=True)
    p_rend.add_argument("--end", type=float, required=True)
    p_rend.add_argument("--title", default="")
    p_rend.add_argument("--caption", default="")
    p_rend.add_argument("--platforms", default="")
    p_pub = sub.add_parser("publish", help="push a rendered clip to platforms")
    p_pub.add_argument("--clip", required=True)
    p_pub.add_argument("--platforms", default="")
    p_pub.add_argument("--live", action="store_true")
    sub.add_parser("pending", help="clips awaiting approval")
    p_app = sub.add_parser("approve", help="publish a pending clip")
    p_app.add_argument("id")
    p_app.add_argument("--platforms", default="")
    p_rej = sub.add_parser("reject", help="drop a pending clip")
    p_rej.add_argument("id")
    sub.add_parser("clips", help="list produced clips")
    p_serve = sub.add_parser("serve", help="REST + OpenAPI server")
    p_serve.add_argument("--host", default=None)
    p_serve.add_argument("--port", type=int, default=None)
    p_serve.add_argument("--loop", action="store_true", help="also run the cycle loop in-process")
    p_serve.add_argument("--every", type=float, default=None)
    p_mcp = sub.add_parser("mcp", help="MCP stdio server")
    p_mcp.add_argument("--list-tools", action="store_true")
    p_live = sub.add_parser("live", help="multi-stream control")
    p_live.add_argument("action", nargs="?", default="status",
                        choices=["status", "start", "stop", "start-all", "stop-all"])
    p_live.add_argument("name", nargs="?", default="all")
    p_obs = sub.add_parser("obs", help="OBS voice-control surface")
    p_obs.add_argument("intent", nargs="?", default="")
    p_obs.add_argument("target", nargs="?", default="")
    p_obs.add_argument("value", nargs="?", default="")
    p_tit = sub.add_parser("title", help="live stream title (see docs/STREAM_TITLE.md)")
    p_tit.add_argument("title", nargs="?", default="")
    p_tit.add_argument("--platforms", nargs="*", default=None)
    p_ta = sub.add_parser("title-auth", help="OAuth once for the title API, print .env lines")
    p_ta.add_argument("platform", choices=["twitch", "youtube", "kick"])
    p_ta.add_argument("--client-id", required=True)
    p_ta.add_argument("--client-secret", required=True)
    p_ta.add_argument("--port", type=int, default=8765)
    p_pri = sub.add_parser("privacy", help="face blur switch (see docs/PRIVACY_BLUR.md)")
    p_pri.add_argument("action", nargs="?", default="status",
                       choices=["status", "on", "off", "toggle"])
    sub.add_parser("doctor", help="check ffmpeg, OBS, deps, platforms")

    args = parser.parse_args(argv)
    cfg = load_config(args.config)

    if args.cmd == "mcp":
        from .mcp_server import build_tools, run_stdio
        if args.list_tools:
            _print(build_tools(args.config))
            return 0
        run_stdio(args.config)
        return 0

    if args.cmd == "serve":
        from .api import serve
        serve(args.config, host=args.host, port=args.port, loop=args.loop, every=args.every)
        return 0

    if args.cmd == "doctor":
        return _doctor(cfg)

    if args.cmd == "title-auth":
        from .stream_title import oauth_login
        tok = oauth_login(args.platform, args.client_id, args.client_secret, args.port)
        up = args.platform.upper()
        print(f"# into the VM's .env, from deploy/obs-vps (each prompts, hidden):\n"
              f"#   ./gcp.sh env {up}_CLIENT_ID\n#   ./gcp.sh env {up}_CLIENT_SECRET\n"
              f"#   ./gcp.sh env {up}_REFRESH_TOKEN\n"
              f"{up}_CLIENT_ID={args.client_id}\n{up}_CLIENT_SECRET={args.client_secret}\n"
              f"{up}_REFRESH_TOKEN={tok['refresh_token']}")
        return 0

    rt = build_pipeline(args.config)

    if args.cmd == "status":
        _print({"workdir": str(rt.workdir), "source": rt.source.status(),
                "window": rt.refresh(), "agent": getattr(rt.agent, "name", "?"),
                "publish_mode": cfg.get("publish", {}).get("mode"),
                "pending": len(rt.pending())})
    elif args.cmd == "window":
        win = rt.capture_window()
        _print(win.to_dict())
    elif args.cmd == "analyze":
        win = rt.capture_window()
        analysis = rt.analyze(win)
        tr = rt.transcribe(win)
        _print({"window": win.to_dict(), "analysis": analysis.to_dict(),
                "transcript": tr.to_dict()})
    elif args.cmd == "propose":
        win = rt.capture_window()
        analysis = rt.analyze(win)
        tr = rt.transcribe(win)
        ctx = rt.context(win, analysis, tr)
        if args.agent:
            from .agents import build_agent
            acfg = dict(cfg.get("agent", {}))
            acfg["name"] = args.agent
            agent = build_agent(acfg)
        else:
            agent = rt.agent
        _print({"window": win.to_dict(), "agent": getattr(agent, "name", "?"),
                "decisions": [d.to_dict() for d in (agent.propose(ctx) or [])]})
    elif args.cmd == "run":
        result = rt.run_cycle(with_frames=not args.no_frames,
                              publish=not args.no_publish, agent_name=args.agent)
        _print(result.to_dict())
    elif args.cmd == "loop":
        rt.loop(seconds=args.every, max_cycles=args.cycles)
    elif args.cmd == "render":
        from .agents import ClipDecision
        from .clips import render_clip
        decision = ClipDecision(start=args.start, end=args.end, title=args.title,
                                caption=args.caption,
                                platforms=[p for p in args.platforms.split(",") if p])
        clip = render_clip(Path(args.window), decision, cfg.get("render", {}),
                           out_dir=rt.clips_dir)
        _print(clip.to_dict())
    elif args.cmd == "publish":
        from .agents import ClipDecision
        from .clips import Clip
        from .publishers import publish_all

        platforms = [p for p in args.platforms.split(",") if p]
        pub_cfg = dict(cfg.get("publish", {}))
        if args.live:
            pub_cfg["mode"] = "live"
        clip = Clip(path=Path(args.clip), start=0.0, end=0.0,
                    duration=0.0, decision=ClipDecision(start=0.0, end=0.0))
        results = publish_all(clip, platforms or pub_cfg.get("platforms", ["local"]),
                              pub_cfg, rt.workdir)
        _print({"results": [r.to_dict() for r in results]})
    elif args.cmd == "pending":
        _print({"pending": rt.pending()})
    elif args.cmd == "approve":
        _print({"results": rt.approve(args.id,
                                      [p for p in args.platforms.split(",") if p] or None)})
    elif args.cmd == "reject":
        _print({"rejected": rt.reject(args.id)})
    elif args.cmd == "clips":
        _print({"clips": [c for cyc in rt.state.get("cycles", [])
                          for c in cyc.get("clips", [])]})
    elif args.cmd == "live":
        if args.action == "status":
            _print(rt.live_status())
        elif args.action == "start":
            _print(rt.live_start(args.name)
                   if args.name != "all" else {"results": rt.live_start_all()})
        elif args.action == "stop":
            _print(rt.live_stop(args.name)
                   if args.name != "all" else {"results": rt.live_stop_all()})
        elif args.action == "start-all":
            _print({"results": rt.live_start_all()})
        elif args.action == "stop-all":
            _print({"results": rt.live_stop_all()})
    elif args.cmd == "obs":
        if not args.intent:
            _print(rt.obs_status())
        else:
            _print(rt.obs_action(args.intent, args.target, args.value))
    elif args.cmd == "title":
        _print(rt.title_set(args.title, args.platforms) if args.title else rt.title_status())
    elif args.cmd == "privacy":
        if args.action == "status":
            _print(rt.privacy_status())
        elif args.action == "toggle":
            _print(rt.privacy_toggle())
        else:
            _print(rt.privacy_set(args.action == "on"))
    else:  # pragma: no cover
        parser.print_help()
    return 0


def _doctor(cfg: dict) -> int:
    import shutil

    from . import caption_images
    from .obs import describe
    from .publishers import available_platforms
    from .transcript import ffmpeg_has_ass

    report = {
        "ffmpeg": shutil.which("ffmpeg") or "MISSING (brew install ffmpeg)",
        "ffprobe": shutil.which("ffprobe") or "MISSING",
        "ffmpeg libass": ("yes — captions burn via subtitles filter"
                          if ffmpeg_has_ass() else
                          "no — captions burn via Pillow PNG overlay"),
        "Pillow": "installed" if caption_images.available() else
                  "not installed (needed for PNG captions)",
        "obs": describe(cfg.get("obs", {})),
        "obs_voice": {
            "enabled": bool((cfg.get("obs", {}).get("voice") or {}).get("enabled", False)),
            "intents": (cfg.get("obs", {}).get("voice") or {}).get("intents", []),
            "allow_dangerous": bool((cfg.get("obs", {}).get("voice") or {})
                                    .get("allow_dangerous", False)),
        },
        "privacy": {
            "enabled": bool((cfg.get("privacy", {}) or {}).get("enabled", False)),
            "mode": (cfg.get("privacy", {}) or {}).get("mode", "clip"),
            "detector": (cfg.get("privacy", {}) or {}).get("detector", "haar"),
            "opencv": "installed" if _has("cv2") else
                      "not installed (needed for face detection)",
        },
        "platforms_available": available_platforms(),
        "live_streams": {
            "enabled": bool(cfg.get("live_streams", {}).get("enabled", False)),
            "targets_configured": len(cfg.get("live_streams", {}).get("targets", []) or []),
            "targets_with_keys": sum(
                1 for t in (cfg.get("live_streams", {}).get("targets") or [])
                if t.get("key")),
        },
        "publish_mode": cfg.get("publish", {}).get("mode"),
        "window_seconds": cfg.get("window", {}).get("seconds"),
        "workdir": cfg["workdir"],
    }
    try:
        import numpy  # noqa: F401
        report["numpy"] = numpy.__version__
    except Exception:
        report["numpy"] = "MISSING"
    for mod, label in (("faster_whisper", "faster-whisper"),
                       ("websocket", "obs websocket-client"),
                       ("mcp", "mcp sdk"),
                       ("requests_oauthlib", "X publisher"),
                       ("googleapiclient", "YouTube publisher"),
                       ("boto3", "S3 hosting")):
        try:
            __import__(mod)
            report[label] = "installed"
        except Exception:
            report[label] = "not installed (optional)"
    _print(report)
    return 0


def _has(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    sys.exit(main())
