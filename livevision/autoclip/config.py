"""Config loading for autoclip, with deep-merged defaults.

Nothing here is required to be set for the pipeline to run: every external
service degrades to a no-op / dry-run when credentials are missing.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict

import yaml

from .util import expand_env

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKDIR = ROOT / "var" / "autoclip"

DEFAULTS: Dict[str, Any] = {
    "workdir": str(DEFAULT_WORKDIR),

    # ---------------------------------------------------------------- source
    # How we obtain the rolling stream.
    #   replay_buffer -> ask OBS for its replay buffer (cheapest, OBS-native)
    #   watch_dir     -> tail OBS's recording/split directory
    #   stream_url    -> ffmpeg pulls SRT/RTMP/HLS from OBS and segments locally
    #   file          -> a single local video file (offline / testing)
    "source": {
        "mode": "auto",             # auto = replay_buffer if OBS reachable, else watch_dir, else file
        "stream_url": "",           # e.g. srt://127.0.0.1:9000?mode=listener  or rtmp://127.0.0.1/live/key
        "watch_dir": "~/Movies/OBS",
        "watch_glob": "*.{mp4,mkv,mov,ts,flv}",
        "file": "",
        "segment_seconds": 10,
    },

    # ---------------------------------------------------------------- OBS
    "obs": {
        "enabled": True,
        "host": "127.0.0.1",
        "port": 4455,
        "password": "",             # obs-websocket v5 password (leave empty if auth is off)
        "timeout": 4.0,
        "auto_start_replay_buffer": True,
        "replay_dir": "",           # fallback if obs-websocket can't report the saved path
        # Voice -> OBS. Off by default: nothing touches OBS until you opt in.
        # See docs/OBS_VOICE_CONTROL.md.
        "voice": {
            "enabled": False,
            "scene": "",            # pin source ops to one scene ("" = current)
            "scenes": [],           # allowlist of voice-switchable scenes ("" = all)
            "allow_dangerous": False,   # gate unbroadcast / unrecord / unvcam
            "aliases": {},          # spoken name -> OBS source name
            "scene_aliases": {},    # spoken name -> OBS scene name
            "default_audio": "",    # for bare "mute" / "volume 50" ("" = autodetect)
            "intents": ["scene", "mute", "unmute", "volume", "record",
                        "unrecord", "vcam", "unvcam", "broadcast",
                        "unbroadcast", "replay", "clip"],
            "match_cutoff": 0.6,    # fuzzy-match threshold for source/scene names
            "cache_seconds": 5.0,   # how long scene/source lists are cached
        },
    },

    # ---------------------------------------------------------------- window
    "window": {
        "seconds": 300,             # the "past five minutes" we always keep
        "stride_seconds": 60,       # how far the analysis window advances each cycle
        "cycle_seconds": 60,        # how often the pipeline runs automatically
        "min_ready_seconds": 45,    # don't analyze until we have this much material
        "overlap_seconds": 30,      # keep this much overlap with the previous window
    },

    # ---------------------------------------------------------------- retention
    # The VPS disk is small; without this every cycle leaves a 5-minute window
    # file behind and the disk fills in a couple of hours of streaming.
    "retention": {
        "keep_windows": 2,          # materialized windows kept (latest N)
        "clip_hours": 72,           # rendered clips older than this are deleted
        "max_clips_gb": 4.0,        # ...and the oldest go first above this size
        "cycles": 50,               # cycle records kept in state.json
        "dedupe_overlap": 0.5,      # a candidate overlapping a recent clip by
                                    # this fraction of its length is a repeat
    },

    # ---------------------------------------------------------------- analysis
    "analysis": {
        "frame_fps": 1.0,           # frames per second sampled from the window
        "audio_hz": 16000,
        "motion_threshold": 0.06,
        "scene_cut_threshold": 0.35,
        "silence_db": -45.0,
        "transcribe": True,
        "transcribe_model": "base",
        "transcribe_max_seconds": 300,
    },

    # ---------------------------------------------------------------- agent
    # "any agent can plug in": pick one by name, or point at a remote endpoint.
    "agent": {
        "name": "heuristic",        # heuristic | llm | remote | <registered name>
        "auto_approve_score": 0.62, # decisions at/above this score get rendered+published
        "max_clips_per_window": 3,
        # Short-form reach is driven by completion rate + replays, so clips are
        # held inside a tight band: 10s floor, ~25s ideal, 30s hard ceiling.
        "min_clip_seconds": 10,
        "target_clip_seconds": 25,
        "max_clip_seconds": 30,
        "llm": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key_env": "OPENAI_API_KEY",
            "send_frames": True,
            "max_frames": 12,
            "temperature": 0.2,
        },
        "remote": {
            "url": "",              # POST AgentContext JSON here, expect {"clips": [...]}
            "headers": {},
            "timeout": 120,
        },
    },

    # ---------------------------------------------------------------- live stream
    # Live multi-streaming: re-broadcast the POV stream to N platforms at once.
    # Start/stop per platform via voice command ("go live on twitch",
    # "stop youtube") or the REST API. See docs/LIVE_STREAMING.md.
    "live_streams": {
        "enabled": False,          # off by default: no ffmpeg spawned at boot
        "source": "",              # local RTMP to pull from (MediaMTX / OBS)
        "max_restarts": 5,
        "restart_backoff_seconds": 5,
        "targets": [],             # [{name, url, key, enabled}]
    },

    # ---------------------------------------------------------------- title
    # Live stream title on twitch / youtube / kick (x and rumble have no API).
    # Credentials come from .env; see docs/STREAM_TITLE.md.
    "stream_title": {
        "retry_delays": [30, 90],   # re-apply after a restream starts
        "twitch": {}, "youtube": {}, "kick": {},
    },

    # ---------------------------------------------------------------- privacy
    # Face blur for bystanders. One switch ("blur faces" / "unblur"), two
    # drivers: blur faces in rendered clips, and/or blur them on the live OBS
    # program output. See docs/PRIVACY_BLUR.md.
    "privacy": {
        "enabled": False,           # master switch: nothing runs unless true
        "default_on": True,         # state at boot (voice can flip it either way)
        "mode": "clip",             # clip | obs | both
        "detector": "auto",         # auto | yunet (DNN, best) | haar (cv2 4.x only)
        "yunet_model": "",          # "" = <workdir>/models/face_detection_yunet_2023mar.onnx
        "auto_download_model": True,    # fetch the YuNet ONNX once, when missing
        "score_threshold": 0.6,
        "strength": 20,             # blur radius in pixels (scaled to the box)
        "padding": 0.25,            # grow each box by this fraction (hair/chin)
        "max_faces": 4,             # tracked faces at once
        "min_face_px": 24,          # ignore anything smaller
        "sample_fps": 2.0,          # clip scan rate
        "scan_width": 640,          # clip scan resolution
        "hold_seconds": 0.8,        # keep a patch alive after a missed frame
        "persist": True,            # remember on/off in workdir/privacy.json
        "obs": {                    # live driver (mode: obs|both)
            "scene": "",            # "" = current program scene
            "source": "",           # "" = autodetect the video source
            "patch_scene": "PrivacyBlur",
            "update_hz": 3.0,
            "screenshot_width": 640,
            "blur_type": "box",     # box | gaussian | bilateral
            "blur_size": 25,
        },
    },

    # ---------------------------------------------------------------- voice
    # Voice command detection: turn a transcript into structured events the
    # HUD / stream-element agent can react to. See docs/VOICE_COMMANDS.md.
    "voice": {
        "name": "regex",           # regex | llm | off
        "min_confidence": 0.5,
        "llm": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key_env": "OPENAI_API_KEY",
            "timeout": 30,
        },
    },

    # ---------------------------------------------------------------- render
    "render": {
        "aspect": "9:16",           # 9:16 | 1:1 | 16:9 | source
        "layout": "crop",           # crop | blur  (blur = blurred padded background)
        "crop_x": 0.5,             # 0..1 horizontal focus when cropping to vertical
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "video_bitrate": "8M",
        "audio_bitrate": "160k",
        "loudnorm": True,
        "captions": True,
        # Live (animated) subtitles burned into the clip.
        #   karaoke : line stays up, active word fills in colour as it's spoken
        #   pop     : one event per word, active word highlights + pops (CapCut style)
        #   line    : static, no animation
        "caption_style": {
            "mode": "karaoke",
            # auto   -> libass `subtitles` filter when available, else PNG overlay
            # ass    -> force the subtitles filter (fails if ffmpeg lacks libass)
            # images -> force the pre-rendered PNG overlay (needs Pillow)
            "burn": "auto",
            "caption_fps": 12,        # PNG overlay frame rate (images mode)
            "stroke": 5,              # outline width (images mode)
            "font": "Arial",
            "size": 64,
            "primary": "&H0000FFFF",      # active / sung colour  (ASS &HAABBGGRR)
            "secondary": "&H00FFFFFF",    # not-yet-sung colour
            "outline": "&H00000000",
            "back": "&H80000000",
            "active_inline": "&H00FFFF&",   # per-word colour in `pop` mode (BGR)
            "inactive_inline": "&HFFFFFF&",
            "pop_scale": 118,
            "pop_ms": 90,
            "fade_ms": 90,
            "margin_v": 260,
            "max_words": 3,
            "max_chars": 28,
        },
        "watermark": "",
    },

    # ---------------------------------------------------------------- publish
    "publish": {
        "mode": "dry_run",          # dry_run | live  (per-platform override below)
        "platforms": ["youtube", "instagram"],
        "default_title": "Clip from the last 5 minutes",
        "default_tags": [],
        "require_approval": True,   # clips sit in the approval queue until approved
        "queue": "always",          # always: queue in dry_run too | live_only
        "youtube": {
            "privacy": "public",
            "category": "22",
            "client_id": "",
            "client_secret": "",
            "refresh_token": "",
            "client_secrets": "",
            "credentials": "var/autoclip/youtube_creds.json",
            "made_for_kids": False,
        },
        "instagram": {
            "graph_version": "v23.0",
            "ig_user_id": "",
            "access_token_env": "INSTAGRAM_ACCESS_TOKEN",
            "share_to_feed": True,
            # Instagram needs a *public* URL for the video.
            #   static -> served by this app at <hosting.public_base_url>/outbox/<file>
            #   s3     -> uploaded to S3/R2 first
            "hosting": "static",
            "hosting_s3": {"bucket": "", "prefix": "autoclip/", "endpoint": "",
                           "region": "auto", "public_base_url": ""},
            "poll_seconds": 5,
            "poll_timeout": 300,
        },
        "x": {
            "consumer_key_env": "X_CONSUMER_KEY",
            "consumer_secret_env": "X_CONSUMER_SECRET",
            "access_token_env": "X_ACCESS_TOKEN",
            "access_token_secret_env": "X_ACCESS_TOKEN_SECRET",
            "max_seconds": 140,
        },
    },

    # ---------------------------------------------------------------- stack
    # GET /api/autoclip/stack (the iOS companion app): which MediaMTX paths
    # are the glasses ingest and OBS's program. "" = not on a MediaMTX box.
    "stack": {
        "mediamtx_api": "",         # e.g. http://127.0.0.1:9997
        "ingest_path": "",          # e.g. live/${STREAM_KEY}
        "program_path": "",         # e.g. live/program
    },

    # ---------------------------------------------------------------- server
    "server": {
        "enabled": False,
        "host": "0.0.0.0",
        "port": 8899,
        "public_base_url": "",      # needed by Instagram hosting=static
        "api_token": "",            # optional bearer token for the REST API
        "root_path": "",            # path prefix when behind a proxy, e.g. /autoclip
        # The OBS browser overlay is served from another origin (the HUD
        # server), so it needs CORS to poll privacy state and read the SSE
        # stream. Leave api_token empty if you want the overlay badge.
        "cors": True,
        "cors_origins": ["*"],
    },

    "logging": {"level": "INFO"},
}


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path = "autoclip.yaml") -> Dict[str, Any]:
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        p = ROOT / path
    raw: Dict[str, Any] = {}
    if p.exists():
        with p.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    cfg = _merge(DEFAULTS, raw)
    return _expand(cfg)


def _expand(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve ~, env vars, and absolutize the workdir.

    `${VAR}` -> `os.environ['VAR']`
    `${VAR:-default}` -> `os.environ['VAR']` if set, else `default`
    """
    def walk(v: Any) -> Any:
        if isinstance(v, str):
            return expand_env(v)
        if isinstance(v, dict):
            return {k: walk(val) for k, val in v.items()}
        if isinstance(v, list):
            return [walk(x) for x in v]
        return v

    cfg = walk(cfg)
    # AUTOCLIP_SOURCE_MODE=rtmp|watch_dir|... overrides the YAML at runtime
    # (handy for container deploys and the `cloud` run mode).
    import os
    if os.environ.get("AUTOCLIP_SOURCE_MODE"):
        cfg["source"]["mode"] = os.environ["AUTOCLIP_SOURCE_MODE"]
    src = cfg["source"]
    for key in ("watch_dir", "file"):
        if src.get(key):
            src[key] = str(Path(src[key]).expanduser())
    rtmp = (src.get("rtmp") or {})
    if rtmp.get("dir"):
        rtmp["dir"] = str(Path(rtmp["dir"]).expanduser())
    wd = Path(cfg["workdir"]).expanduser()
    if not wd.is_absolute():
        wd = ROOT / wd
    cfg["workdir"] = str(wd)
    for key in ("client_secrets", "credentials"):
        val = cfg["publish"]["youtube"].get(key)
        if val:
            p = Path(val).expanduser()
            cfg["publish"]["youtube"][key] = str(p if p.is_absolute() else ROOT / p)
    return cfg
