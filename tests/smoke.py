"""Dependency-light smoke test for autoclip.  Run:  python tests/smoke.py

Covers everything that does not need ffmpeg: config, decision parsing, the
heuristic agent, moment detection, caption writing, the local publisher, the
REST app, and a real MCP stdio handshake against the server subprocess.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoclip.agents import ClipDecision, HeuristicAgent  # noqa: E402
from autoclip.captions import write_captions  # noqa: E402
from autoclip.clips import _escape_filter_path  # noqa: E402
from autoclip.config import load_config  # noqa: E402
from autoclip.pipeline import build_pipeline  # noqa: E402
from autoclip.publishers import publish_all  # noqa: E402
from autoclip.signals import SecondSignal, find_moments  # noqa: E402
from autoclip.transcript import Transcript, Word  # noqa: E402

PASS, FAIL = [], []


def check(name: str, fn):
    try:
        fn()
        PASS.append(name)
        print(f"  ok   {name}")
    except Exception as exc:  # noqa: BLE001
        FAIL.append((name, exc))
        print(f"  FAIL {name}: {exc}")


# --------------------------------------------------------------------------- 1 config
def t_config():
    cfg = load_config(ROOT / "autoclip.yaml")
    assert cfg["window"]["seconds"] == 300, cfg["window"]
    assert Path(cfg["workdir"]).is_absolute()
    assert "~" not in cfg["source"]["watch_dir"]
    # short-form length band: 10s floor, ~25s ideal, 30s ceiling
    assert cfg["agent"]["min_clip_seconds"] == 10
    assert cfg["agent"]["target_clip_seconds"] == 25
    assert cfg["agent"]["max_clip_seconds"] == 30


def t_length_band():
    """Every clip the pipeline can emit must land inside the 10–30s band."""
    c = {"min_clip_seconds": 10, "target_clip_seconds": 25, "max_clip_seconds": 30,
         "platforms": ["x"]}
    # too long -> clamped to the ceiling
    long = ClipDecision.from_any({"start": 10, "end": 90}, c)
    assert long.duration == 30.0, long.duration
    # too short -> padded to the floor
    short = ClipDecision.from_any({"start": 10, "end": 12}, c)
    assert short.duration == 10.0, short.duration
    # no end given -> defaults to the ideal, not the floor
    open_ended = ClipDecision.from_any({"start": 10}, c)
    assert open_ended.duration == 25.0, open_ended.duration

    # a 60s hot run must be trimmed to the densest 30s, not chopped from the head
    per = [SecondSignal(t=float(i), rms_db=-15.0, speech=True, motion=0.3,
                        brightness=0.5, cut=False) for i in range(120)]
    moments = find_moments(per, min_seconds=10, target_seconds=25, max_seconds=30)
    assert moments, "expected a moment"
    assert moments[0].end - moments[0].start <= 30.5, moments[0]


# --------------------------------------------------------------------------- 2 decisions
def t_decisions():
    c = {"min_clip_seconds": 10, "max_clip_seconds": 60, "platforms": ["x"]}
    d = ClipDecision.from_any({"start": 100, "end": 105, "score": "0.9",
                               "hashtags": "a, b", "platforms": "youtube"}, c)
    assert d is not None and 9.5 <= d.duration <= 10.5, d
    assert d.hashtags == ["a", "b"] and d.platforms == ["youtube"]
    long = ClipDecision.from_any({"start": 0, "end": 600}, c)
    assert long.duration <= 60.5
    assert ClipDecision.from_any({"nope": 1}, c) is None


# --------------------------------------------------------------------------- 3 moments
def t_moments():
    per = []
    for i in range(120):
        hot = 40 <= i < 55
        per.append(SecondSignal(t=float(i), rms_db=-20.0 if hot else -60.0,
                                speech=hot, motion=0.4 if hot else 0.01,
                                brightness=0.5, cut=(i == 40)))
    moments = find_moments(per)
    assert moments, "expected at least one moment"
    top = moments[0]
    assert top.start < 45 < top.end, (top.start, top.end)
    assert 0.0 < top.score <= 1.0


# --------------------------------------------------------------------------- 4 agent
def t_agent():
    from autoclip.signals import Analysis

    per = [SecondSignal(t=float(i), rms_db=-18.0, speech=True, motion=0.3,
                        brightness=0.5, cut=False) for i in range(60)]
    analysis = Analysis(duration=60.0, per_second=per,
                        moments=find_moments(per))
    words = [Word(i * 0.5, i * 0.5 + 0.4, w)
             for i, w in enumerate("this is a genuinely funny moment from the stream".split())]
    tr = Transcript(words=words, text=" ".join(w.text for w in words), engine="fake")
    ctx = type("C", (), {})()  # minimal stand-in
    from autoclip.agents import AgentContext
    ctx = AgentContext(window={"path": "x", "duration": 60.0}, analysis=analysis,
                       transcript=tr, constraints={"max_clips_per_window": 2,
                                                   "platforms": ["youtube"],
                                                   "default_tags": ["clip"]})
    out = HeuristicAgent({}).propose(ctx)
    assert out, "heuristic produced nothing"
    assert out[0].title and out[0].duration > 0


# --------------------------------------------------------------------------- 5 captions
def t_captions():
    from autoclip.transcript import caption_lines

    tr = Transcript(words=[Word(i * 0.5, i * 0.5 + 0.45, w) for i, w in
                           enumerate("hello there friends this is live".split())],
                    text="hello there friends this is live", engine="fake")
    lines = caption_lines(tr, max_words=3, max_chars=28)
    assert lines and lines[0]["words"], "caption lines must carry word timings"

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # karaoke: one event per line, \kf sweep per word
        karaoke = write_captions(lines, td / "k", {"size": 64, "font": "Arial",
                                                   "mode": "karaoke"})
        srt = karaoke["srt"].read_text()
        ass = karaoke["ass"].read_text()
        assert "00:00:00,000 --> 00:00:01,450" in srt, srt
        assert "hello there friends" in srt
        assert "[V4+ Styles]" in ass
        assert "\\kf" in ass, "karaoke mode must emit \\kf sweep tags"
        assert ass.count("Dialogue:") == len(lines), ass

        # pop: one event per word
        pop = write_captions(lines, td / "p", {"size": 64, "font": "Arial", "mode": "pop"})
        pop_ass = pop["ass"].read_text()
        assert pop_ass.count("Dialogue:") >= len(tr.words), pop_ass
        assert "\\fscx" in pop_ass, "pop mode must scale the active word"
        assert "\\c&H00FFFF&" in pop_ass

        # no word timings -> static fallback
        plain = write_captions([{"t0": 0.0, "t1": 1.0, "text": "static"}], td / "s",
                               {"mode": "karaoke"})
        assert "\\kf" not in plain["ass"].read_text()


# --------------------------------------------------------------------------- 6 publisher
def t_publish():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        clip_path = td / "clip.mp4"
        clip_path.write_bytes(b"\x00" * 64)
        from autoclip.agents import ClipDecision as CD
        from autoclip.clips import Clip
        clip = Clip(path=clip_path, start=0, end=10, duration=10,
                    decision=CD(start=0, end=10, title="t"))
        results = publish_all(clip, ["local"], {"mode": "dry_run"}, td)
        assert results and results[0].ok, results
        assert (td / "outbox" / "clip.mp4").exists()
        assert (td / "outbox" / "clip.json").exists()


# --------------------------------------------------------------------------- 7 REST app
def t_rest():
    from autoclip.api import create_app
    app = create_app(config_path=str(ROOT / "autoclip.yaml"))
    paths = {r.path for r in app.routes}
    for needed in ("/api/autoclip/schema", "/api/autoclip/status",
                   "/api/autoclip/run", "/api/autoclip/approve/{item_id}"):
        assert needed in paths, f"missing route {needed}"
    try:
        from fastapi.testclient import TestClient
    except Exception:
        return  # httpx not installed; route presence is enough
    with TestClient(app) as client:
        r = client.get("/api/autoclip/schema")
        assert r.status_code == 200, r.text
        assert r.json()["operations"]
        # the new HUD-facing operations must be advertised
        names = {op["name"] for op in r.json()["operations"]}
        for needed in ("events", "events_history", "command"):
            assert needed in names, f"missing op {needed}"
        r = client.get("/api/autoclip/status")
        assert r.status_code == 200, r.text
        # manual command injection: appears in history within one call
        r = client.post("/api/autoclip/command",
                        json={"text": "show the compass", "intent": "show",
                              "target": "compass"})
        assert r.status_code == 200, r.text
        ev = r.json()["event"]
        assert ev["intent"] == "show" and ev["target"] == "compass"
        r = client.get("/api/autoclip/events/history?type=voice_command&n=10")
        assert r.status_code == 200, r.text
        assert any(e["target"] == "compass" for e in r.json()["events"]), r.json()

        # live multi-stream endpoints exist and degrade cleanly when disabled
        r = client.get("/api/autoclip/live")
        assert r.status_code == 200, r.text
        assert r.json()["enabled"] is False
        for path in ("/api/autoclip/live/start/twitch", "/api/autoclip/live/stop/twitch"):
            r = client.post(path)
            assert r.status_code == 200, (path, r.text)
            assert r.json()["ok"] is False, (path, r.json())
        for path in ("/api/autoclip/live/start_all", "/api/autoclip/live/stop_all"):
            r = client.post(path)
            assert r.status_code == 200, (path, r.text)

        # schema advertises live control + the configured targets
        sch = client.get("/api/autoclip/schema").json()
        assert "live_start_all" in {op["name"] for op in sch["operations"]}
        assert "stream" in sch["voice_intents"] and "unstream" in sch["voice_intents"]
        assert "stream_status" in sch["event_types"]
        assert "twitch" in sch["live_platforms"], sch["live_platforms"]

        # obs voice-control endpoints exist and degrade when disabled
        r = client.get("/api/autoclip/obs")
        assert r.status_code == 200, r.text
        assert r.json()["enabled"] is False
        r = client.post("/api/autoclip/obs/command",
                        json={"intent": "scene", "target": "map"})
        assert r.status_code == 200, r.text
        assert r.json()["ok"] is False, r.json()

        assert "obs_status" in {op["name"] for op in sch["operations"]}
        assert "scene" in sch["voice_intents"]
        assert "obs_status" in sch["event_types"]
        assert "scene" in sch["obs_intents"], sch["obs_intents"]

        # privacy blur: advertised, readable, and refuses while disabled
        assert {"privacy_status", "privacy_set"} <= {op["name"] for op in sch["operations"]}
        assert "blur" in sch["voice_intents"] and "unblur" in sch["voice_intents"]
        assert "privacy_status" in sch["event_types"], sch["event_types"]
        r = client.get("/api/autoclip/privacy")
        assert r.status_code == 200, r.text
        assert r.json()["enabled"] is False
        r = client.post("/api/autoclip/privacy", json={"on": True})
        assert r.status_code == 200 and r.json()["ok"] is False, r.text
        r = client.post("/api/autoclip/privacy", json={"toggle": True})
        assert r.status_code == 200 and r.json()["ok"] is False, r.text


# --------------------------------------------------------------------------- 8 MCP stdio
def _mcp_call(proc: subprocess.Popen, msg: dict) -> dict:
    body = json.dumps(msg).encode()
    proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
    proc.stdin.flush()
    headers = {}
    while True:
        line = proc.stdout.readline().decode().strip()
        if not line:
            break
        k, v = line.split(":", 1)
        headers[k.strip().lower()] = v.strip()
    n = int(headers.get("content-length", 0))
    return json.loads(proc.stdout.read(n))


def t_mcp():
    proc = subprocess.Popen(
        [sys.executable, "-m", "autoclip.mcp_server", "--config", str(ROOT / "autoclip.yaml")],
        cwd=str(ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        init = _mcp_call(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        assert init["result"]["serverInfo"]["name"] == "autoclip", init
        tools = _mcp_call(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [t["name"] for t in tools["result"]["tools"]]
        for needed in ("autoclip_status", "autoclip_propose", "autoclip_run",
                       "autoclip_render", "autoclip_publish", "autoclip_approve",
                       "autoclip_command", "autoclip_events_history",
                       "autoclip_live_status", "autoclip_live_start",
                       "autoclip_live_stop", "autoclip_obs_status",
                       "autoclip_obs_command", "autoclip_privacy_status",
                       "autoclip_privacy_set"):
            assert needed in names, names
        res = _mcp_call(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                               "params": {"name": "autoclip_status", "arguments": {}}})
        payload = json.loads(res["result"]["content"][0]["text"])
        assert "source" in payload and "window" in payload, payload
        # command injection over MCP
        cmd = _mcp_call(proc, {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                               "params": {"name": "autoclip_command", "arguments": {
                                   "text": "set weather to rain", "intent": "set",
                                   "target": "weather", "value": "rain"}}})
        ev = json.loads(cmd["result"]["content"][0]["text"])["event"]
        assert ev["intent"] == "set" and ev["value"] == "rain", ev
    finally:
        proc.terminate()


# --------------------------------------------------------------------------- 9 pipeline
def t_pipeline():
    from autoclip.config import load_config
    from autoclip.pipeline import Pipeline

    p = build_pipeline(str(ROOT / "autoclip.yaml"))
    assert p.source is not None and p.agent is not None
    st = p.refresh()
    assert "covered_seconds" in st
    # a cycle with no footage must degrade, not crash
    res = p.run_cycle(publish=False)
    assert res.id and isinstance(res.notes, list)

    # obs voice control is opt-in: disabled means no controller and no
    # dispatcher thread at all; enabled means both, even with no OBS to reach.
    assert p.obs is None and p.dispatcher is None
    assert p.obs_status()["enabled"] is False
    assert p.obs_action("scene", "map")["ok"] is False
    # privacy blur is opt-in too, and has no OBS driver in clip mode
    assert p.privacy_status()["enabled"] is False
    assert p.privacy_set(True)["ok"] is False
    assert p.privacy.obs is None

    cfg = load_config(str(ROOT / "autoclip.yaml"))
    cfg["workdir"] = str(Path(tempfile.mkdtemp()) / "w")
    cfg["obs"]["voice"]["enabled"] = True
    p2 = Pipeline(cfg)
    try:
        assert p2.obs is not None and p2.dispatcher is not None
        st = p2.obs_status()
        assert st["enabled"] is True and "connected" in st
        # unreachable OBS must refuse, never raise
        assert p2.obs_action("scene", "map")["ok"] is False
        # and the destructive gate holds even when unreachable
        assert "destructive" in p2.obs_action("unbroadcast")["message"]
    finally:
        p2.shutdown()


def t_escape():
    assert _escape_filter_path(Path("/tmp/a'b:c.ass")).count("\\") >= 1


def t_rtmp_source():
    """The cloud source driver builds the right URL, hides the key in status,
    and degrades to a WatchDirSource when ffmpeg isn't running yet."""
    from autoclip.ingest import RTMPSource, build_source
    with tempfile.TemporaryDirectory() as td:
        src = RTMPSource("rtmp://ingest.example.com/live", Path(td),
                          stream_key="secret123", segment_seconds=15)
        assert src.name == "rtmp"
        assert src.url.endswith("/secret123"), src.url
        st = src.status()
        assert st["ingest"] == "rtmp"
        assert "secret123" not in str(st), "status must not leak the stream key"

    # env expansion of ${VAR:-default}
    cfg = {
        "mode": "rtmp",
        "workdir": "/tmp",
        "rtmp": {
            "url": "rtmp://h:1935/live",
            "stream_key": "${MISSING_KEY:-fallback}",
            "dir": "/tmp/incoming",
            "chunk_seconds": 30,
        },
    }
    src = build_source(cfg)
    assert src.url.endswith("/fallback"), src.url

    # env override on source.mode (for container deploys)
    import os
    os.environ["AUTOCLIP_SOURCE_MODE"] = "rtmp"
    try:
        cfg2 = load_config(ROOT / "autoclip.yaml")
        assert cfg2["source"]["mode"] == "rtmp", cfg2["source"]
    finally:
        del os.environ["AUTOCLIP_SOURCE_MODE"]


def t_voice_parser():
    """The voice command parser turns a transcript into the right StreamEvents."""
    from autoclip.voice import RegexParser, build_parser
    p = RegexParser()
    cases = [
        ("show the compass now.",          "show",   "compass",        ""),
        ("hide the health bar",            "hide",   "health bar",     ""),
        ("set weather to snow",            "set",    "weather",        "snow"),
        ("play dragon roar",               "play",   "dragon roar",    ""),
        ("add subtitle: hello friends",    "add",    "subtitle",       "hello friends"),
        ("caption: this is a test",        "add",    "subtitle",       "this is a test"),
        ("toggle night vision",            "toggle", "night vision",   ""),
        ("clip this",                      "clip",   "",               ""),
        ("mark a clip",                    "clip",   "",               ""),
    ]
    for text, intent, target, value in cases:
        tr = Transcript(words=[Word(i * 0.3, i * 0.3 + 0.25, w)
                               for i, w in enumerate(text.split())],
                        text=text, engine="t")
        evs = p.parse(tr)
        assert evs, f"no event for {text!r}"
        d = evs[0].to_dict()
        assert d["intent"] == intent, (text, d)
        assert d["target"] == target, (text, d)
        assert d["value"] == value, (text, d)

    # non-command sentences are ignored
    tr = Transcript(words=[Word(0, 0.3, w)
                           for w in "I think this is really cool".split()],
                    text="I think this is really cool.", engine="t")
    assert p.parse(tr) == [], "non-commands must be skipped"

    # build_parser dispatch
    assert build_parser({"name": "regex"}).name == "regex"
    assert build_parser({"name": "off"}).name == "off"


def t_event_bus():
    """EventBus: in-process pub/sub, JSONL log, history replay on warm start."""
    from autoclip.events import EventBus
    from autoclip.voice import StreamEvent
    import time as _t
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        bus = EventBus(td / "events.jsonl", history=10)
        sub = bus.subscribe()
        ev = StreamEvent(type="voice_command", ts=_t.time(), window_t=0.0,
                         text="show the compass", intent="show", target="compass")
        bus.publish(ev)
        assert sub, "subscriber must receive event"
        assert sub[0].text == "show the compass"
        assert (td / "events.jsonl").exists()

        # warm start: a new bus replays the JSONL
        bus2 = EventBus(td / "events.jsonl", history=10)
        h = bus2.history()
        assert h and h[0].target == "compass"


def t_voice_stream_commands():
    """The voice grammar must turn live-stream phrases into stream/unstream
    intents with the right platform target."""
    from autoclip.voice import RegexParser
    p = RegexParser()
    cases = [
        ("go live on twitch.",            "stream",   "twitch"),
        ("live on youtube",               "stream",   "youtube"),
        ("start streaming on kick",       "stream",   "kick"),
        ("start twitch",                  "stream",   "twitch"),
        ("go live everywhere",            "stream",   "all"),
        ("go live on all platforms",      "stream",   "all"),
        ("stop streaming to youtube",     "unstream", "youtube"),
        ("stop twitch",                   "unstream", "twitch"),
        ("end the youtube stream",        "unstream", "youtube"),
        ("stop all streams",              "unstream", "all"),
    ]
    for text, intent, target in cases:
        tr = Transcript(words=[Word(i * 0.3, i * 0.3 + 0.25, w)
                               for i, w in enumerate(text.split())],
                        text=text, engine="t")
        evs = p.parse(tr)
        assert evs, f"no event for {text!r}"
        d = evs[0].to_dict()
        assert d["intent"] == intent, (text, d)
        assert d["target"] == target, (text, d)

    # HUD-only commands must not be mistaken for stream control
    for text in ("show the compass", "hide health bar", "clip this"):
        tr = Transcript(words=[Word(0, 0.3, w) for w in text.split()],
                        text=text, engine="t")
        evs = p.parse(tr)
        assert evs and evs[0].intent not in ("stream", "unstream"), (text, evs)


def t_obs_voice_patterns():
    """The OBS half of the grammar must not collide with the multi-stream half.

    "start streaming" (bare) is OBS's own output; "start streaming on twitch"
    is a platform. Same for "stop broadcasting" vs "stop twitch".
    """
    from autoclip.voice import RegexParser
    p = RegexParser()
    cases = [
        # --- scene switching
        ("switch to the map scene.",      "scene",       ("map", "")),
        ("go to the ending scene",        "scene",       ("ending", "")),
        ("scene map",                     "scene",       ("map", "")),
        ("cut to the map",                "scene",       ("map", "")),
        # --- audio
        ("mute the mic",                  "mute",        ("mic", "")),
        ("mute.",                         "mute",        ("", "")),
        ("unmute mic",                    "unmute",      ("mic", "")),
        ("volume 50",                     "volume",      ("", "50")),
        ("set volume to 30",              "volume",      ("", "30")),
        ("set mic volume to 80",          "volume",      ("mic", "80")),
        ("turn the volume up",            "volume",      ("", "up")),
        # --- recording / output
        ("start recording",               "record",      ("", "")),
        ("record this",                   "record",      ("", "")),
        ("stop recording",                "unrecord",    ("", "")),
        ("start the virtual camera",      "vcam",        ("", "")),
        ("stop virtual cam",              "unvcam",      ("", "")),
        ("start streaming",               "broadcast",   ("", "")),
        ("start the stream",              "broadcast",   ("", "")),
        ("stop broadcasting",             "unbroadcast", ("", "")),
        ("stop the stream",               "unbroadcast", ("", "")),
        ("save the replay",               "replay",      ("", "")),
        ("replay that",                   "replay",      ("", "")),
        ("set transition to fade",        "transition",  ("fade", "")),
        # --- multi-stream must NOT be stolen by the OBS rules
        ("start streaming on twitch",     "stream",      ("twitch", "")),
        ("stop twitch",                   "unstream",    ("twitch", "")),
        ("go live everywhere",            "stream",      ("all", "")),
        # --- HUD intents still resolve
        ("set weather to snow",           "set",         ("weather", "snow")),
        ("show the compass",              "show",        ("compass", "")),
    ]
    for text, intent, (target, value) in cases:
        tr = Transcript(words=[Word(i * 0.3, i * 0.3 + 0.25, w)
                               for i, w in enumerate(text.split())],
                        text=text, engine="t")
        evs = p.parse(tr)
        assert evs, f"no event for {text!r}"
        d = evs[0].to_dict()
        assert d["intent"] == intent, (text, d)
        assert d["target"] == target, (text, d)
        assert d["value"] == value, (text, d)


def t_obs_controller():
    """OBSController: name resolution + policy gates.

    No real OBS: `OBSClient.request` is stubbed, which is the single seam all
    the higher-level methods go through.
    """
    from autoclip.obs import OBSClient
    from autoclip.obsctl import OBSController, normalize

    assert normalize("Compass Image") == normalize("compass image") == "compassimage"

    class FakeOBS(OBSClient):
        def __init__(self):
            super().__init__({"enabled": True})
            self.calls: List[tuple] = []
            self.responses = {
                "GetSceneList": {
                    "currentProgramSceneName": "Live",
                    "scenes": [{"sceneName": "Live"}, {"sceneName": "MapScene"},
                               {"sceneName": "Ending"}]},
                "GetInputList": {"inputs": [
                    {"inputName": "Mic/Aux", "inputKind": "wasapi_input_capture"},
                    {"inputName": "Compass", "inputKind": "image_source"},
                    {"inputName": "Subtitle", "inputKind": "text_gdiplus_v2"},
                    {"inputName": "DragonRoar", "inputKind": "ffmpeg_source"}]},
                "GetSceneItemId": {"sceneItemId": 7},
                "GetSceneItemList": {"sceneItems": [
                    {"sceneItemId": 7, "sourceName": "Compass",
                     "sceneItemEnabled": False}]},
            }

        def connect(self, force: bool = False) -> bool:
            return True

        def request(self, request_type, data=None, retry=True):
            self.calls.append((request_type, data or {}))
            return self.responses.get(request_type, {})

        def sent(self, name):
            return [d for rt, d in self.calls if rt == name]

    # ---------------------------------------------------------- name resolution
    fake = FakeOBS()
    ctl = OBSController(fake, {"enabled": True,
                               "aliases": {"compass": "Compass"},
                               "scene_aliases": {"map": "MapScene"}})
    assert ctl.resolve_source("compass") == "Compass"          # alias
    assert ctl.resolve_source("subtitle") == "Subtitle"        # exact
    assert ctl.resolve_source("dragon roar") == "DragonRoar"   # normalized exact
    assert ctl.resolve_source("zzzzqqq") is None               # no match
    assert ctl.resolve_scene("map") == "MapScene"              # scene alias
    assert ctl.resolve_scene("ending") == "Ending"
    assert ctl.resolve_scene("nope") is None

    # ---------------------------------------------------------- policy gates
    off = OBSController(FakeOBS(), {"enabled": False})
    assert off.handle("scene", "map").ok is False
    assert "disabled" in off.handle("scene", "map").message

    # destructive action is gated
    safe = OBSController(FakeOBS(), {"enabled": True})
    r = safe.handle("unbroadcast")
    assert r.ok is False and "destructive" in r.message, r
    assert not any(rt == "StopStream" for rt, _ in safe.client.calls), \
        "gated action must never reach OBS"

    bold = OBSController(FakeOBS(), {"enabled": True, "allow_dangerous": True})
    assert bold.handle("unbroadcast").ok is True
    assert bold.client.sent("StopStream")

    # intent not armed
    narrow = OBSController(FakeOBS(), {"enabled": True, "intents": ["scene"]})
    assert narrow.handle("record").ok is False
    assert narrow.handles("record") is False
    assert narrow.handles("scene") is True
    assert narrow.handles("madeupintent") is False

    # ---------------------------------------------------------- scene switching
    fake2 = FakeOBS()
    ctl2 = OBSController(fake2, {"enabled": True,
                                 "scene_aliases": {"map": "MapScene"}})
    r = ctl2.handle("scene", "map")
    assert r.ok is True and r.target == "MapScene", r
    assert fake2.sent("SetCurrentProgramScene") == [{"sceneName": "MapScene"}]

    # scene allowlist blocks anything not listed
    locked = OBSController(FakeOBS(), {"enabled": True, "scenes": ["Live"]})
    r = locked.handle("scene", "ending")
    assert r.ok is False and "not voice-switchable" in r.message, r
    assert not any(rt == "SetCurrentProgramScene"
                   for rt, _ in locked.client.calls)

    # ---------------------------------------------------------- source visibility
    fake3 = FakeOBS()
    ctl3 = OBSController(fake3, {"enabled": True,
                                 "aliases": {"compass": "Compass"},
                                 "intents": ["show", "hide", "toggle", "set"]})
    assert ctl3.handle("show", "compass").ok is True
    assert fake3.sent("SetSceneItemEnabled")[0]["sceneItemEnabled"] is True
    assert ctl3.handle("hide", "compass").ok is True
    assert fake3.sent("SetSceneItemEnabled")[1]["sceneItemEnabled"] is False
    # toggle reads current state first (Compass starts disabled -> becomes shown)
    assert ctl3.handle("toggle", "compass").ok is True
    assert fake3.sent("SetSceneItemEnabled")[2]["sceneItemEnabled"] is True
    # unknown source -> refuses
    before = len(fake3.sent("SetSceneItemEnabled"))
    assert ctl3.handle("show", "zzzzqqq").ok is False
    assert len(fake3.sent("SetSceneItemEnabled")) == before

    # ---------------------------------------------------------- mute / volume
    fake4 = FakeOBS()
    ctl4 = OBSController(fake4, {"enabled": True})
    assert ctl4.handle("mute", "mic").ok is True
    assert fake4.sent("SetInputMute")[0]["inputName"] == "Mic/Aux"
    assert fake4.sent("SetInputMute")[0]["inputMuted"] is True
    assert ctl4.handle("unmute", "mic").ok is True
    assert fake4.sent("SetInputMute")[1]["inputMuted"] is False

    assert ctl4.handle("volume", "", "50").detail["mul"] == 0.5     # 50 -> 50%
    assert ctl4.handle("volume", "", "0.25").detail["mul"] == 0.25  # 0.25 -> 25%
    assert ctl4.handle("volume", "", "150").detail["mul"] == 1.0    # clamped
    assert ctl4.handle("volume", "", "up").ok is True
    assert ctl4.handle("volume", "", "loud").ok is False            # unparseable

    # ---------------------------------------------------------- outputs
    fake5 = FakeOBS()
    ctl5 = OBSController(fake5, {"enabled": True, "allow_dangerous": True})
    assert ctl5.handle("record").ok is True and fake5.sent("StartRecord")
    assert ctl5.handle("unrecord").ok is True and fake5.sent("StopRecord")
    assert ctl5.handle("vcam").ok is True and fake5.sent("StartVirtualCam")
    assert ctl5.handle("replay").ok is True and fake5.sent("SaveReplayBuffer")
    assert ctl5.handle("broadcast").ok is True and fake5.sent("StartStream")
    assert ctl5.handle("clip").ok is True                     # clip -> replay save

    # ---------------------------------------------------------- status
    st = OBSController(FakeOBS(), {"enabled": True}).status()
    assert st["connected"] is True
    assert st["scenes"] == ["Live", "MapScene", "Ending"]
    assert "Mic/Aux" in st["sources"]
    assert "unbroadcast" in st["intents"]
    assert OBSController(FakeOBS(), {"enabled": False}).status()["enabled"] is False


def t_dispatcher_obs():
    """The dispatcher routes OBS intents to the controller and leaves
    HUD-owned intents alone unless the operator opted in."""
    from autoclip.dispatcher import CommandDispatcher
    from autoclip.events import EventBus
    from autoclip.obs import OBSClient
    from autoclip.obsctl import OBSController
    from autoclip.voice import StreamEvent

    class FakeOBS(OBSClient):
        def __init__(self):
            super().__init__({"enabled": True})
            self.calls: List[tuple] = []
        def connect(self, force=False): return True
        def request(self, request_type, data=None, retry=True):
            self.calls.append((request_type, data or {}))
            return {"GetSceneList": {"currentProgramSceneName": "Live", "scenes": []},
                    "GetInputList": {"inputs": []},
                    "GetSceneItemId": {"sceneItemId": 1},
                    "GetSceneItemList": {"sceneItems": []}}.get(request_type, {})

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        bus = EventBus(td / "events.jsonl")
        watcher = bus.subscribe()
        ctl = OBSController(FakeOBS(), {"enabled": True})
        disp = CommandDispatcher(bus, None, ctl)

        # OBS intent -> controller -> obs_status event
        bus.publish(StreamEvent(type="voice_command", intent="scene",
                                target="map", text="switch to the map scene"))
        disp._loop_iteration()
        assert disp.processed == 1
        assert disp.last_action["intent"] == "scene"
        obs_evs = [e for e in watcher if e.type == "obs_status"]
        assert obs_evs and obs_evs[0].target, list(watcher)

        # HUD intent is NOT handled by default (the HUD agent owns it)
        bus.publish(StreamEvent(type="voice_command", intent="show",
                                target="compass", text="show the compass"))
        disp._loop_iteration()
        assert disp.processed == 1, "show must fall through to the HUD agent"

        # ...but is handled once the operator arms it
        bus2 = EventBus(td / "events2.jsonl")
        ctl2 = OBSController(FakeOBS(), {"enabled": True,
                                         "intents": ["show", "hide"]})
        disp2 = CommandDispatcher(bus2, None, ctl2)
        bus2.publish(StreamEvent(type="voice_command", intent="show",
                                 target="compass", text="show the compass"))
        disp2._loop_iteration()
        assert disp2.processed == 1, "armed show intent should reach OBS"

        # an intent OBS can't do at all is ignored
        disp3 = CommandDispatcher(EventBus(td / "events3.jsonl"), None,
                                  OBSController(FakeOBS(), {"enabled": True}))
        disp3.bus.publish(StreamEvent(type="voice_command", intent="clip"))
        disp3._loop_iteration()
        assert disp3.processed == 1, "clip is in the default obs intent set"


def t_live_manager():
    """LiveStreamManager: target loading, alias resolution, start/stop, status.

    Real ffmpeg is never spawned — `_spawn_locked` is stubbed so the test is
    deterministic and safe to run on a laptop.
    """
    from autoclip.livestream import LiveStreamManager, resolve_name
    # alias resolution
    assert resolve_name("Twitch") == "twitch"
    assert resolve_name("twitch.tv") == "twitch"
    assert resolve_name("twitter") == "x"
    assert resolve_name("everywhere") == "all"
    assert resolve_name("*") == "all"
    assert resolve_name("mycustomrelay") == "mycustomrelay"

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cfg = {
            "source": "rtmp://127.0.0.1:1935/live/glasses",
            "max_restarts": 2,
            "restart_backoff_seconds": 0,
            "targets": [
                {"name": "twitch", "url": "rtmp://live.twitch.tv/app",
                 "key": "live_123", "enabled": False},
                {"name": "youtube", "url": "rtmp://a.rtmp.youtube.com/live2",
                 "key": "${MISSING_YT_KEY}", "enabled": False},
            ],
        }
        mgr = LiveStreamManager(cfg, td)
        spawned = []

        def fake_spawn(t):
            spawned.append(t.name)
        mgr._spawn_locked = fake_spawn          # no real ffmpeg
        mgr._stop.set()                          # pause the watchdog

        # a target with no resolved key must refuse to start
        r = mgr.start("youtube")
        assert r["ok"] is False and "stream key" in r["message"], r
        assert r["platform"] == "youtube"

        # a configured target starts
        r = mgr.start("twitch")
        assert r["ok"] is True, r
        assert "twitch" in spawned
        assert mgr.targets["twitch"].enabled is True

        # unknown target
        assert mgr.start("myspace")["ok"] is False

        # status reflects configuration without leaking keys
        st = mgr.status()
        assert st["source"].endswith("/glasses")
        names = {t["name"] for t in st["targets"]}
        assert names == {"twitch", "youtube"}, names
        yt = next(t for t in st["targets"] if t["name"] == "youtube")
        assert yt["key_set"] is False, "empty key must not report as set"
        tw = next(t for t in st["targets"] if t["name"] == "twitch")
        assert tw["key_set"] is True
        assert "live_123" not in str(st), "status must not leak stream keys"

        # stop
        assert mgr.stop("twitch")["ok"] is True
        assert mgr.targets["twitch"].enabled is False
        assert (td / "state.json").exists(), "active set must persist"


def t_dispatcher():
    """The dispatcher routes stream/unstream events to the live manager and
    emits a stream_status event the HUD can render."""
    from autoclip.dispatcher import CommandDispatcher
    from autoclip.events import EventBus
    from autoclip.livestream import LiveStreamManager
    from autoclip.voice import StreamEvent
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        cfg = {"source": "rtmp://127.0.0.1:1935/live/glasses",
               "targets": [{"name": "twitch", "url": "rtmp://live.twitch.tv/app",
                            "key": "k"}]}
        mgr = LiveStreamManager(cfg, td / "live")
        spawned, stopped = [], []
        mgr._spawn_locked = lambda t: spawned.append(t.name)
        mgr._stop.set()

        bus = EventBus(td / "events.jsonl")
        disp = CommandDispatcher(bus, mgr)
        watcher = bus.subscribe()

        # "go live on twitch" -> start
        bus.publish(StreamEvent(type="voice_command", intent="stream",
                                target="twitch", text="go live on twitch"))
        disp._loop_iteration()
        assert spawned == ["twitch"], spawned
        assert disp.last_action["intent"] == "stream"
        assert any(e.type == "stream_status" for e in watcher), list(watcher)

        # "stop twitch" -> stop
        bus.publish(StreamEvent(type="voice_command", intent="unstream",
                                target="twitch", text="stop twitch"))
        disp._loop_iteration()
        assert disp.last_action["intent"] == "unstream"
        assert mgr.targets["twitch"].enabled is False

        # unknown platform -> recorded as unknown, not a crash
        bus.publish(StreamEvent(type="voice_command", intent="stream",
                                target="myspace", text="go live on myspace"))
        disp._loop_iteration()
        assert disp.last_action["result"]["ok"] is False

        # unrelated intents are ignored
        before = disp.processed
        bus.publish(StreamEvent(type="voice_command", intent="show",
                                target="compass", text="show the compass"))
        disp._loop_iteration()
        assert disp.processed == before

        # transcript chunks are not commands
        bus.publish(StreamEvent(type="transcript_chunk", text="hello there"))
        disp._loop_iteration()
        assert disp.processed == before


def t_privacy():
    """Privacy blur: filtergraph builder, tracking, and the on/off switch."""
    from autoclip.privacy import (BlurBox, FaceBox, FaceTracker, PrivacyManager,
                                  is_privacy_target, privacy_chain)

    # ---- filtergraph
    assert privacy_chain([]) == ""
    boxes = [BlurBox(0.0, 2.5, 100, 200, 80, 90), BlurBox(3.0, 6.0, 400, 120, 60, 70)]
    chain = privacy_chain(boxes, strength=20)
    assert chain.startswith("split=3[b][s0][s1]"), chain
    assert "crop=80:90:100:200,boxblur=20:2[p0]" in chain, chain
    assert "overlay=100:200:enable='between(t,0.000,2.500)'" in chain
    # the last overlay is left unlabelled: the caller owns the output label
    assert chain.endswith("enable='between(t,3.000,6.000)'"), chain
    # radius is clamped so boxblur can never exceed the crop
    assert "boxblur=2:2" in privacy_chain([BlurBox(0, 1, 0, 0, 3, 3)], strength=99)

    # ---- tracking collapses jitter into a couple of stable patches
    tr = FaceTracker(max_faces=2, hold_seconds=0.5, smoothing=0.5)
    for i in range(6):
        tr.update(i * 0.5, [FaceBox(100 + i, 50, 60, 60)])
    for i in range(3):
        tr.update(3.0 + i * 0.5, [FaceBox(400, 300, 60, 60)])
    segs = tr.segments(padding=0.0, frame_w=1920, frame_h=1080)
    assert 1 <= len(segs) <= 2, segs
    assert segs[0].w >= 60 and segs[0].h >= 60

    # ---- target words that mean "the privacy blur"
    assert is_privacy_target("face blur") and is_privacy_target("privacy")
    assert is_privacy_target("faces") and not is_privacy_target("compass")

    # ---- state machine
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        # disabled -> refuses, never writes state
        off = PrivacyManager({"privacy": {"enabled": False}}, Path(td) / "a")
        assert off.set(True)["ok"] is False
        assert "disabled" in off.set(True)["message"]
        assert off.status()["enabled"] is False
        assert off.clips_blurred is False

        mgr = PrivacyManager({"privacy": {"enabled": True, "mode": "clip",
                                          "default_on": False}}, Path(td) / "b")
        assert mgr.on is False
        assert mgr.set(True)["on"] is True and mgr.clips_blurred is True
        assert mgr.toggle()["on"] is False
        assert mgr.status()["mode"] == "clip"
        assert mgr.status()["obs_blurred"] is False
        # persisted across a restart
        again = PrivacyManager({"privacy": {"enabled": True, "mode": "clip",
                                            "default_on": True}}, Path(td) / "b")
        assert again.on is False, "persisted state must win over default_on"

        # voice entry points
        assert mgr.handle("blur")["on"] is True
        assert mgr.handle("unblur")["on"] is False
        assert mgr.handle("toggle", "face blur")["on"] is True
        assert mgr.handle("toggle", "compass")["ok"] is False
        assert mgr.wants("blur") and mgr.wants("toggle", "privacy")
        assert not mgr.wants("show")


def t_privacy_voice():
    """"blur faces" / "privacy mode on" must not be read as anything else."""
    from autoclip.voice import RegexParser
    p = RegexParser()
    cases = [
        ("blur faces.",                  "blur",   "faces", ""),
        ("blur the faces",               "blur",   "faces", ""),
        ("blur everyone's faces",        "blur",   "faces", ""),
        ("blur all faces",               "blur",   "faces", ""),
        ("privacy mode on",              "blur",   "faces", ""),
        ("turn privacy on",              "blur",   "faces", ""),
        ("start blurring",               "blur",   "faces", ""),
        ("unblur faces",                 "unblur", "faces", ""),
        ("show faces",                   "unblur", "faces", ""),
        ("stop blurring",                "unblur", "faces", ""),
        ("stop blurring faces",          "unblur", "faces", ""),
        ("privacy off",                  "unblur", "faces", ""),
        ("toggle face blur",             "toggle", "face blur", ""),
        ("toggle privacy",               "toggle", "privacy", ""),
    ]
    for text, intent, target, value in cases:
        tr = Transcript(words=[Word(i * 0.3, i * 0.3 + 0.25, w)
                               for i, w in enumerate(text.split())],
                        text=text, engine="t")
        evs = p.parse(tr)
        assert evs, f"no event for {text!r}"
        d = evs[0].to_dict()
        assert d["intent"] == intent, (text, d)
        assert d["target"] == target, (text, d)
        assert d["value"] == value, (text, d)

    # nothing else got broken by putting the privacy rules first
    for text, intent, target in (("show the compass", "show", "compass"),
                                 ("stop twitch", "unstream", "twitch"),
                                 ("hide health bar", "hide", "health bar"),
                                 ("stop recording", "unrecord", "")):
        tr = Transcript(words=[Word(i * 0.3, i * 0.3 + 0.25, w)
                               for i, w in enumerate(text.split())],
                        text=text, engine="t")
        evs = p.parse(tr)
        assert evs and evs[0].intent == intent, (text, evs)
        assert evs[0].target == target, (text, evs)


def t_privacy_dispatcher():
    """A voice command reaches the privacy manager and shows up on the bus."""
    from autoclip.dispatcher import CommandDispatcher
    from autoclip.events import EventBus
    from autoclip.privacy import PrivacyManager
    from autoclip.voice import StreamEvent
    import tempfile as _tf

    with _tf.TemporaryDirectory() as td:
        td = Path(td)
        bus = EventBus(td / "events.jsonl")
        watcher = bus.subscribe()
        mgr = PrivacyManager({"privacy": {"enabled": True, "mode": "clip",
                                          "default_on": False}}, td / "w", bus=bus)
        disp = CommandDispatcher(bus, None, None, privacy=mgr)

        bus.publish(StreamEvent(type="voice_command", intent="blur",
                                target="faces", text="blur faces"))
        disp._loop_iteration()
        assert mgr.on is True, "voice 'blur faces' must switch it on"
        assert disp.processed == 1
        assert any(e.type == "privacy_status" for e in watcher), list(watcher)

        bus.publish(StreamEvent(type="voice_command", intent="unblur",
                                target="faces", text="unblur faces"))
        disp._loop_iteration()
        assert mgr.on is False

        # "toggle face blur" is privacy's; "toggle compass" is not
        bus.publish(StreamEvent(type="voice_command", intent="toggle",
                                target="face blur", text="toggle face blur"))
        disp._loop_iteration()
        assert mgr.on is True
        before = disp.processed
        bus.publish(StreamEvent(type="voice_command", intent="toggle",
                                target="compass", text="toggle compass"))
        disp._loop_iteration()
        assert disp.processed == before, "HUD toggles must fall through"


def _bare_pipeline():
    from autoclip.config import load_config
    from autoclip.pipeline import Pipeline
    cfg = load_config(str(ROOT / "autoclip.yaml"))
    cfg["workdir"] = str(Path(tempfile.mkdtemp()) / "w")
    return Pipeline(cfg)


def t_dedupe_across_windows():
    """The window slides 60 s per cycle but spans 300 s, so one moment is
    re-proposed for ~5 cycles. It must be clipped once."""
    from autoclip.agents import ClipDecision
    from autoclip.buffer import Window
    p = _bare_pipeline()
    try:
        w1 = Window(path=Path("w1.mkv"), start_wall=1000.0, duration=300.0, source="t")
        # cycle 1 clipped 200-225 s of window 1 (wall 1200-1225)
        p.state["cycles"] = [{"clips": [{"abs_start": 1200.0, "abs_end": 1225.0,
                                         "decision": {"title": "big moment"}}]}]
        w2 = Window(path=Path("w2.mkv"), start_wall=1060.0, duration=300.0, source="t")
        same = ClipDecision(start=140.0, end=165.0, score=0.9)      # wall 1200-1225 again
        new = ClipDecision(start=250.0, end=275.0, score=0.8)       # wall 1310-1335
        kept, dropped = p._drop_repeats(w2, [same, new])
        assert dropped == 1 and kept == [new], (dropped, kept)
        # two picks inside one window may not overlap each other either
        a = ClipDecision(start=10.0, end=35.0, score=0.9)
        b = ClipDecision(start=15.0, end=40.0, score=0.8)
        kept, dropped = p._drop_repeats(w1, [a, b])
        assert kept == [a] and dropped == 1
        # the agent is told where earlier clips sit in the new window
        assert p._recent_spans()[0][:2] == (1200.0, 1225.0)
    finally:
        p.shutdown()


def t_retention_keeps_disk_bounded():
    import os
    import time as _t
    p = _bare_pipeline()
    try:
        p.cfg["retention"] = {"keep_windows": 2, "clip_hours": 1, "max_clips_gb": 100, "cycles": 3}
        for i in range(5):
            w = p.windows_dir / f"window_{i}.mkv"
            w.write_bytes(b"x")
            os.utime(w, (_t.time() + i, _t.time() + i))
        old = _t.time() - 7200
        for stem in ("old_0", "pend_0", "new_0"):
            for ext in (".mp4", ".srt", ".jpg"):
                f = p.clips_dir / f"{stem}{ext}"
                f.write_bytes(b"x")
                if stem != "new_0":
                    os.utime(f, (old, old))
        (p.clips_dir / "old_0_caps").mkdir()
        p.state["pending"] = [{"id": "pend_0", "clip": {"path": str(p.clips_dir / "pend_0.mp4")}}]
        p._cleanup()
        assert sorted(x.name for x in p.windows_dir.iterdir()) == ["window_3.mkv", "window_4.mkv"]
        names = {x.name for x in p.clips_dir.iterdir()}
        assert not any(n.startswith("old_0") for n in names), names     # aged out, caps dir too
        assert {"pend_0.mp4", "pend_0.srt", "pend_0.jpg"} <= names       # awaiting approval: kept
        assert "new_0.mp4" in names
        # state.json keeps only the last N cycles
        from autoclip.pipeline import CycleResult
        for _ in range(6):
            p._record(CycleResult(id="c"))
        assert len(p.state["cycles"]) == 3
    finally:
        p.shutdown()


def t_captions_one_file_per_clip():
    with tempfile.TemporaryDirectory() as td:
        lines = [{"t0": 0.0, "t1": 1.0, "text": "one"}]
        a = write_captions(lines, Path(td), {"mode": "line"}, stem="clipA")
        b = write_captions([{"t0": 0.0, "t1": 1.0, "text": "two"}], Path(td), {"mode": "line"}, stem="clipB")
        assert a["srt"] != b["srt"]
        assert "one" in Path(a["srt"]).read_text() and "two" in Path(b["srt"]).read_text()


def main() -> int:
    print("autoclip smoke test\n")
    for name, fn in [
        ("config", t_config), ("clip length band", t_length_band),
        ("decisions", t_decisions), ("moments", t_moments),
        ("heuristic agent", t_agent), ("captions", t_captions), ("publisher", t_publish),
        ("rest api", t_rest), ("mcp stdio", t_mcp), ("pipeline", t_pipeline),
        ("filter escaping", t_escape), ("rtmp cloud source", t_rtmp_source),
        ("voice parser", t_voice_parser), ("event bus", t_event_bus),
        ("voice stream commands", t_voice_stream_commands),
        ("live stream manager", t_live_manager), ("command dispatcher", t_dispatcher),
        ("obs voice patterns", t_obs_voice_patterns),
        ("obs controller", t_obs_controller),
        ("obs dispatcher routing", t_dispatcher_obs),
        ("privacy blur", t_privacy),
        ("privacy voice grammar", t_privacy_voice),
        ("privacy dispatcher routing", t_privacy_dispatcher),
        ("dedupe across windows", t_dedupe_across_windows),
        ("retention keeps disk bounded", t_retention_keeps_disk_bounded),
        ("captions one file per clip", t_captions_one_file_per_clip),
    ]:
        check(name, fn)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    for name, exc in FAIL:
        print(f"  - {name}: {exc}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
