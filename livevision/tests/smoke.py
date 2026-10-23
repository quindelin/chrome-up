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
import time
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

        # companion app's one-poll health: answers even with nothing running
        r = client.get("/api/autoclip/stack")
        assert r.status_code == 200, r.text
        st = r.json()
        assert st["ingest"]["live"] is False and st["program"]["live"] is False, st
        assert "pending" in st["autoclip"] and "disk_free" in st["host"], st
        assert all("key" not in t for t in st["restream"]["targets"]), st

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

    # ---------------------------------------------------------- visibility allowlist
    # "show lingualens" is OBS's; "show the compass" stays with the HUD
    fake4 = FakeOBS()
    fake4.responses["GetInputList"]["inputs"].append(
        {"inputName": "LinguaLens", "inputKind": "browser_source"})
    vis = OBSController(fake4, {"enabled": True, "intents": ["show", "hide", "toggle"],
                                "visibility_sources": ["LinguaLens"],
                                "aliases": {"lingua lens": "LinguaLens"}})
    assert vis.show("lingua lens").ok
    assert fake4.sent("SetSceneItemEnabled")[-1]["sceneItemEnabled"] is True
    refused = vis.hide("compass")
    assert not refused.ok and "not voice-controllable" in refused.message
    assert not vis.toggle("compass").ok
    assert len(fake4.sent("SetSceneItemEnabled")) == 1


def t_voice_once_and_rumble():
    """A command stays inside the sliding window for ~5 cycles: it must fire
    once. Two commands with the same verb keep their own spoken times."""
    from autoclip.buffer import Window
    from autoclip.transcript import Transcript, Word
    from autoclip.voice import RegexParser

    words = [Word(1.0, 1.4, "show"), Word(1.4, 2.0, "lingualens."),
             Word(40.0, 40.4, "show"), Word(40.4, 41.0, "map.")]
    tr = Transcript(words=words, text="show lingualens. show map.")
    evs = RegexParser().parse(tr)
    assert [round(e.window_t) for e in evs] == [1, 40], [e.window_t for e in evs]

    p = _bare_pipeline()
    try:
        w1 = Window(path=Path("a.mkv"), start_wall=1000.0, duration=300.0, source="t")
        first = p._emit_voice_commands(w1, tr)
        assert len(first) == 2
        # next cycle: window slid 60 s, same words now 60 s earlier in it
        tr2 = Transcript(words=[Word(w.t0 - 60, w.t1 - 60, w.text) for w in words[:2]]
                         + [Word(200.0, 200.4, "hide"), Word(200.4, 201.0, "lingualens.")],
                         text="show lingualens. hide lingualens.")
        w2 = Window(path=Path("b.mkv"), start_wall=1060.0, duration=300.0, source="t")
        again = p._emit_voice_commands(w2, tr2)
        assert [e["intent"] for e in again] == ["hide"], again
    finally:
        p.shutdown()

    # typed/hotkey commands go through the same grammar as speech
    p3 = _bare_pipeline()
    try:
        ev = p3.inject_command("show lingua lens")
        assert (ev.intent, ev.target) == ("show", "lingua lens"), ev
        assert p3.inject_command("hello there").intent == "manual"
    finally:
        p3.shutdown()

    rx = RegexParser()
    one = lambda text: rx.parse(Transcript(words=[Word(0, 1, text.split()[0])], text=text))[0]
    assert (one("start rumble.").intent, one("start rumble.").target) == ("stream", "rumble")
    assert one("go live on rumble.").target == "rumble"


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


def t_head_pose():
    """Glasses orientation -> avatar head: relative to the first sample (DAT
    does not document the quaternion's axes), each axis lands on its own."""
    import math
    from server.headpose import HeadPose, _qmul

    def q(axis, deg):
        h = math.radians(deg) / 2
        return (math.cos(h),) + tuple(math.sin(h) if a == axis else 0.0 for a in "xyz")

    still = {"recenter_s": 0, "pitch_level_s": 0, "roll_level_s": 0}
    hp = HeadPose(still)
    base = q("x", 15)                        # already tilted when data starts = "ahead"
    assert hp.ingest({"q": list(base)})
    for axis, name in (("y", "yaw"), ("x", "pitch"), ("z", "roll")):
        hp.ingest({"q": list(_qmul(base, q(axis, 30)))})
        snap = hp.snapshot()
        assert abs(snap[name] - 30) < 0.5, (name, snap)
        assert all(abs(snap[o]) < 0.5 for o in ("yaw", "pitch", "roll") if o != name), snap
    assert hp.snapshot()["fresh"] is True
    assert hp.ingest({"yaw": 5, "pitch": -2, "roll": 1}) and hp.snapshot()["yaw"] == 5
    assert not hp.ingest({"nothing": 1})
    flip = HeadPose({**still, "invert": {"yaw": True}})
    flip.ingest({"q": [1, 0, 0, 0]}); flip.ingest({"q": list(q("y", 20))})
    assert abs(flip.snapshot()["yaw"] + 20) < 0.5

    # data started while looking up 30 deg (reference) and you then look ahead:
    # pitch reads -30 at first, then levels out instead of staring down for good
    import server.headpose as hpmod
    clock = [1000.0]
    real = hpmod.time.time
    hpmod.time.time = lambda: clock[0]
    try:
        lv = HeadPose({"recenter_s": 0, "pitch_level_s": 30})
        lv.ingest({"q": list(q("x", 30))})
        clock[0] += 0.1; lv.ingest({"q": [1, 0, 0, 0]})
        assert abs(lv.snapshot()["pitch"] + 30) < 1, lv.snapshot()
        for _ in range(1200):                # 2 min at 10 Hz
            clock[0] += 0.1; lv.ingest({"q": [1, 0, 0, 0]})
        assert abs(lv.snapshot()["pitch"]) < 1.5, lv.snapshot()
        clock[0] += 0.1; lv.ingest({"q": list(q("x", -20))})   # a real nod still shows
        assert abs(abs(lv.snapshot()["pitch"]) - 20) < 2, lv.snapshot()
    finally:
        hpmod.time.time = real


def t_nav_stream_safe():
    """The stream's copy of the route keeps the compass marker and nothing
    that names a place."""
    from server.navigation import stream_safe
    full = {"active": True, "source": "apple", "status": "geocode failed (12 Elm St)",
            "objective": {"name": "Ferry Building", "bearing": 81.0, "distance": 120.0,
                          "step": "Turn left onto Market St", "icon": "left", "mode": "apple",
                          "maneuver": "left"},
            "destination": {"name": "Ferry Building", "distance": 1400, "eta": 1080},
            "route_distance": 1400, "route_duration": 1080}
    safe = stream_safe(full)
    text = str(safe)
    for leak in ("Ferry", "Market", "Elm", "1400", "1080"):
        assert leak not in text, (leak, safe)
    assert safe["objective"]["bearing"] == 81.0 and safe["objective"]["distance"] == 120.0
    assert safe["active"] and "destination" not in safe and "status" not in safe
    assert stream_safe({"active": False, "status": "waiting for GPS"})["status"] == "waiting for GPS"


def t_imu_gait():
    """Pocket phone: standing still is idle, a walk's ~1.9 steps/s bounce is
    walking, a hard ~2.8/s run is running, upright (gravity on y) or flat (z)."""
    import math, random, time as _t
    from server.imu import IMUHub

    def feed(hz, amp, axis="y", secs=4.0):
        hub = IMUHub({"window_s": 4.0, "stale_s": 2.0})
        now = _t.time()
        rnd = random.Random(1)
        n = int(secs * 25)
        for i in range(n):
            t = now - secs + i / 25
            bounce = amp * math.sin(2 * math.pi * hz * (i / 25)) + rnd.gauss(0, 0.15)
            # gravity and the (vertical) bounce on whichever axis is up
            a = {"ax": rnd.gauss(0, 0.1), "ay": rnd.gauss(0, 0.1), "az": rnd.gauss(0, 0.1)}
            a["a" + axis] += 9.81 + bounce
            hub.ingest({"t": t * 1000, **a, "gx": 0, "gy": 0, "gz": 0})
        return hub.compute()

    assert feed(0, 0)["activity"] == "idle"
    w = feed(1.9, 2.0)
    assert w["activity"] == "walking" and 1.6 < w["cadence"] < 2.2, w
    assert feed(1.9, 2.0, axis="z")["activity"] == "walking"
    r = feed(2.8, 7.0)
    assert r["activity"] == "running", r
    assert feed(1.9, 0.3)["activity"] == "idle"          # fidgeting, not a gait


def t_locomotion_gate():
    """Walking / running from the head-worn camera: not while sitting, not
    while the head turns, and only after it has held for hold_s."""
    from server.activity import LocomotionGate
    g = LocomotionGate({"hold_s": 2.0, "release_s": 1.0, "head_turn_dps": 45})
    still = {"yaw": 0, "pitch": 0, "fresh": True}
    assert g.update(0.0, "walking", from_camera=True, head=still) == "idle"
    assert g.update(1.0, "walking", from_camera=True, head=still) == "idle"   # not yet
    assert g.update(2.1, "walking", from_camera=True, head=still) == "walking"
    assert g.update(2.5, "idle", from_camera=True, head=still) == "walking"   # release
    assert g.update(3.6, "idle", from_camera=True, head=still) == "idle"
    # sitting: the camera's "running" is your head, never a gait
    for t in (10, 11, 12, 13, 14):
        assert g.update(t, "running", from_camera=True, sitting=True, head=still) == "idle"
    # a fast head turn (90 deg in 0.5 s) blanks camera gaits for a moment
    g2 = LocomotionGate({"hold_s": 0.5})
    g2.update(0.0, "idle", from_camera=True, head={"yaw": 0, "pitch": 0, "fresh": True})
    for i in range(1, 6):
        t = i * 0.1
        assert g2.update(t, "running", from_camera=True,
                         head={"yaw": 18 * i, "pitch": 0, "fresh": True}) == "idle", t
    assert g2.head_speed > 45
    # the IMU feels footfalls: sitting / head turns don't veto it
    g3 = LocomotionGate({"hold_s": 0.5})
    g3.update(0.0, "running", from_camera=False, sitting=True)
    assert g3.update(0.6, "running", from_camera=False, sitting=True) == "running"
    # the head camera's boxing / lifting is dropped (it can't see your arms);
    # opted back in, boxing needs no hold
    assert LocomotionGate().update(0.0, "boxing", from_camera=True) == "idle"
    assert LocomotionGate({"camera_arm_labels": True}).update(0.0, "boxing", from_camera=True) == "boxing"


def t_arms():
    """Wrist orientation -> where the arm points: gravity makes up/down exact,
    the arms-down hold finds the forearm axis, the T-pose sets outward, and a
    pelvis turn doesn't swing the arms."""
    import math, tempfile as _tf
    from server.arms import Arms, rotate, conj

    def q_axis(axis, deg):
        h = math.radians(deg) / 2
        n = math.sqrt(sum(c * c for c in axis))
        return (math.cos(h),) + tuple(math.sin(h) * c / n for c in axis)

    def qmul(a, b):
        aw, ax, ay, az = a; bw, bx, by, bz = b
        return (aw*bw - ax*bx - ay*by - az*bz, aw*bx + ax*bw + ay*bz - az*by,
                aw*by - ax*bz + ay*bw + az*bx, aw*bz + ax*by - ay*bx + az*bw)

    def q_pointing(axis_dev, world_dir):
        """device->world rotation taking device axis_dev onto world_dir"""
        a = axis_dev; b = world_dir
        cx, cy, cz = a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]
        d = sum(x*y for x, y in zip(a, b))
        if d < -0.9999:
            return q_axis((0, 0, 1) if abs(a[2]) < 0.9 else (1, 0, 0), 180)
        w = 1 + d; n = math.sqrt(w*w + cx*cx + cy*cy + cz*cz)
        return (w/n, cx/n, cy/n, cz/n)

    def grav(q):            # device-frame gravity for a device->world q
        return list(rotate(conj(q), (0, 0, -9.8)))

    with _tf.TemporaryDirectory() as td:
        arms = Arms({"calibration_path": f"{td}/cal.json", "smooth": False})
        # world: +x = body's left at calibration, +y = back... (arbitrary yaw);
        # the Watch's forearm axis is +x
        out_left = (1.0, 0.0, 0.0)
        down = q_pointing((1, 0, 0), (0, 0, -1))
        assert arms.ingest_wrist("left", down, "watch", grav(down))
        snap = arms.snapshot()["left"]
        assert snap["fresh"] and snap["elev"] < -85, snap          # hanging, uncalibrated
        up = q_pointing((1, 0, 0), (0, 0, 1))
        arms.ingest_wrist("left", up, "watch", grav(up))
        assert arms.snapshot()["left"]["dir"][1] > 0.95                 # hand overhead
        # a world->device sender is detected from its gravity and flipped
        arms2 = Arms({"calibration_path": f"{td}/cal2.json", "smooth": False})
        assert arms2.ingest_wrist("left", conj(up), "watch", grav(up))
        assert arms2.snapshot()["left"]["dir"][1] > 0.95

        # calibrate: down, then T-pose (left forearm along world +x = outward)
        arms.ingest_wrist("left", down, "watch", grav(down)); arms.calibrate("down")
        tp = q_pointing((1, 0, 0), out_left)
        arms.ingest_wrist("left", tp, "watch", grav(tp))
        tilt = q_axis((1, 0, 0), 70)                     # a pocket phone is never flat:
        arms.ingest_pelvis(tilt, grav(tilt))              # its gravity settles the convention
        arms.ingest_pelvis(q_axis((0, 0, 1), 0), [0, 0, -9.8])
        assert arms.calibrate("tpose")["ok"]
        d = arms.snapshot()["left"]["dir"]
        assert d[0] < -0.95 and arms.snapshot()["left"]["calibrated"], d    # out to the left
        # reach forward: from outward-left, forward is clockwise from above
        fwd = q_pointing((1, 0, 0), (0, -1, 0))
        arms.ingest_wrist("left", fwd, "watch", grav(fwd))
        d = arms.snapshot()["left"]["dir"]
        assert d[2] > 0.95, d
        # turn the whole body 90 deg left (CCW): pelvis and arm both turn,
        # the arm still reads forward
        turn = q_axis((0, 0, 1), 90)
        arms.ingest_pelvis(turn, [0, 0, -9.8])
        fwd2 = qmul(turn, fwd)
        arms.ingest_wrist("left", fwd2, "watch", grav(fwd2))
        d = arms.snapshot()["left"]["dir"]
        assert d[2] > 0.95, d
        # the Neural Band: unknown axis until an arms-down hold
        band_axis = (0.0, 1.0, 0.0)
        bdown = q_pointing(band_axis, (0, 0, -1))
        arms.ingest_wrist("right", bdown, "neural_band")
        assert arms.snapshot()["right"].get("needs") == "calibration"
        arms.calibrate("down")
        bup = q_pointing(band_axis, (0, 0, 1))
        arms.ingest_wrist("right", bup, "neural_band")
        assert arms.snapshot()["right"]["dir"][1] > 0.95
        # calibration survives a restart (that second arms-down hold redid the
        # left arm too: a new axis waits for a new T-pose)
        again = Arms({"calibration_path": f"{td}/cal.json"})._cal
        assert again["right"]["axis"] and again["left"]["out_yaw"] is None


def t_arm_filter():
    """The 1-euro filter: a still arm's sensor noise shrinks a lot, a real
    swing still gets through within a few samples."""
    import random
    from server.arms import OneEuro
    f, rnd = OneEuro(), random.Random(3)
    out = []
    for i in range(60):                                   # 6 s at 10 Hz, arm still
        out.append(f((rnd.gauss(0, 0.05), -1.0, rnd.gauss(0, 0.05)), i * 0.1))
    raw_sd, fil_sd = 0.05, (sum(o[0] ** 2 for o in out[20:]) / 40) ** 0.5
    assert fil_sd < raw_sd * 0.6, (fil_sd, raw_sd)
    for i in range(60, 66):                               # swing the arm up
        v = f((0.0, 1.0, 0.0), i * 0.1)
    assert v[1] > 0.8, v


def t_body_gestures():
    """Neural Band gestures reach the avatar once each, with an id; junk is
    refused; they drop out after GESTURE_SHOW_S."""
    import time as _t
    import server.body as bodymod
    b = bodymod.Body()
    assert b.ingest({"gesture": {"kind": "wave", "side": "right"}})
    assert not b.ingest({"gesture": {"kind": "dab"}})
    assert b.ingest({"gesture": {"kind": "point"}})
    gs = b.snapshot()["gestures"]
    assert [g["kind"] for g in gs] == ["wave", "point"] and gs[0]["id"] < gs[1]["id"], gs
    assert gs[1]["side"] == "right"
    real = _t.time
    try:
        bodymod.time.time = lambda: real() + bodymod.GESTURE_SHOW_S + 0.1
        assert b.snapshot()["gestures"] == []
    finally:
        bodymod.time.time = real


def t_body_tracking():
    """Posture from the phone in a front pocket (thigh angle, with hysteresis),
    hands from the glasses camera going stale on their own, heart rate range."""
    import time as _t
    from server.body import Body
    b = Body({"hand_stale_s": 0.2})
    assert b.snapshot()["posture"] == "unknown"                     # nothing yet
    b.ingest({"gravity": [0.0, -1.0, 0.05]}); assert b.snapshot()["posture"] == "standing"
    b.ingest({"gravity": [0.0, -0.1, -0.99]}); assert b.snapshot()["posture"] == "sitting"
    b.ingest({"gravity": [0.0, -0.39, -0.92]})                       # ~67 deg: in the gap
    assert b.snapshot()["posture"] == "sitting", "hysteresis should hold the last answer"
    b.ingest({"gravity": [0.0, -0.69, -0.72]})                       # ~46 deg: measured standing
    assert b.snapshot()["posture"] == "standing", "a pocket-tilted phone standing up"
    b.ingest({"posture": "standing"}); assert b.snapshot()["posture"] == "standing"
    assert b.ingest({"hands": {"right": {"x": 0.2, "y": -0.3, "z": 0.4}}})
    snap = b.snapshot()["hands"]
    assert snap["right"]["fresh"] and snap["right"]["z"] == 0.4 and not snap["left"]["fresh"]
    _t.sleep(0.25)
    assert not b.snapshot()["hands"]["right"]["fresh"], "a hand out of view must go stale"
    assert not b.ingest({"hands": {"right": {"x": "?"}}})
    b.ingest({"heart_rate": 400}); assert b.snapshot()["heart_rate"] is None
    b.ingest({"heart_rate": 92}); assert b.snapshot()["heart_rate"] == 92
    b.ingest({"wrists": {"left": {"q": [1, 0, 0, 0], "source": "watch"}}})
    assert b.snapshot()["wrists"]["left"]["source"] == "watch"


def t_body_punches():
    """Punch events: each gets an id once, Watch + band on one wrist count once,
    junk is refused, and they drop out of the payload after PUNCH_SHOW_S."""
    from server import body as bodymod
    b = bodymod.Body()
    assert not b.snapshot()["punching"] and b.snapshot()["punches"] == []
    assert b.ingest({"punch": {"side": "right", "kind": "hook", "strength": 0.9, "source": "watch"}})
    assert b.ingest({"punch": {"side": "right", "kind": "straight", "strength": 1.4, "source": "neural_band"}})
    ps = b.snapshot()["punches"]
    assert len(ps) == 1 and ps[0]["kind"] == "hook" and ps[0]["strength"] == 1.0, ps
    assert b.ingest({"punches": [{"side": "left", "kind": "jab?"}]})
    ps = b.snapshot()["punches"]
    assert [p["id"] for p in ps] == [1, 2] and ps[1]["kind"] == "straight" and ps[1]["strength"] == 0.7
    assert not b.ingest({"punch": {"side": "middle"}}) and not b.ingest({"punch": "left"})
    assert b.snapshot()["punching"] and b.punching()
    for p in b._punches:
        p["ts"] -= bodymod.PUNCH_SHOW_S + 0.1
    snap = b.snapshot()
    assert snap["punches"] == [] and snap["punching"], "guard stays up a little longer"


def t_phone_route():
    """Apple Maps turn-by-turn from the companion: fresh = source of truth
    (marker on the next maneuver, the phone's along-route distance), stale or
    {"active": false} = back to the server's own objective."""
    from server import navigation as navmod
    nav = navmod.Navigation({"enabled": True, "provider": "manual",
                             "origin": {"lat": 37.7749, "lon": -122.4194},
                             "destination": {"lat": 37.80, "lon": -122.41}})
    assert nav.tick()["objective"]["mode"] == "straight"
    route = {"active": True, "instruction": "Turn left onto Market St", "step_distance": 120,
             "maneuver": {"lat": 37.7749, "lon": -122.4180, "bearing": 90, "type": "left"},
             "next_instruction": "Turn right onto 3rd St", "remaining_m": 1400, "eta_s": 1080,
             "destination": {"name": "Ferry Building", "lat": 37.7955, "lon": -122.3937},
             "transport": "walking"}
    assert nav.set_phone_route(route)
    st = nav.tick()
    obj = st["objective"]
    assert st["active"] and st["source"] == "apple" and obj["mode"] == "apple"
    assert obj["step"] == "Turn left onto Market St" and obj["distance"] == 120
    assert 85 < obj["bearing"] < 95, obj            # re-aimed at the maneuver, due east
    assert obj["maneuver"] == "left"
    assert st["destination"] == {"name": "Ferry Building", "distance": 1400, "eta": 1080}
    assert not nav.set_phone_route({"active": True, "maneuver": {}}), "no target, no route"
    nav.phone_route_ts -= 60                         # phone went quiet
    assert nav.tick().get("source") != "apple"
    nav.set_phone_route(route)
    nav.set_phone_route({"active": False, "arrived": True, "remaining_m": 4,
                         "destination": {"name": "Ferry Building"}})
    st = nav.tick()
    assert st["arrived"] and not st["active"]
    nav.set_phone_route({"active": False})
    assert nav.tick().get("source") != "apple"


def t_heartbeat_config():
    """The HUD heartbeat's on/off flag reaches the overlay via /api/config
    (on by default, off when config.yaml says so)."""
    import asyncio
    import json as _json
    from types import SimpleNamespace
    import server.main as hud
    from server.config import load_config as load_hud_config
    cfg = load_hud_config(ROOT / "config.yaml")
    assert cfg["heartbeat"]["enabled"] is True
    old = hud.RT
    try:
        for given, want in (({}, True), ({"enabled": False}, False)):
            hud.RT = SimpleNamespace(cfg={**cfg, "heartbeat": given},
                                     vtube=SimpleNamespace(status=lambda: {}))
            out = _json.loads(asyncio.run(hud.api_config()).body)["heartbeat"]
            assert out["enabled"] is want and out["high_bpm"] == 150, out
    finally:
        hud.RT = old

def t_stream_title():
    """Title on twitch/youtube/kick with HTTP mocked; x/rumble say unsupported;
    missing creds are ok=false, never an exception; tokens never in results."""
    from autoclip import stream_title as st
    calls = []

    def fake(method, url, *, headers=None, json_body=None, form=None, timeout=10.0):
        calls.append((method, url, headers or {}, json_body, form))
        if url == st.TWITCH_TOKEN:
            return 200, {"access_token": "tw_new", "refresh_token": "tw_r2", "expires_in": 3600}
        if url.startswith(st.TWITCH_API + "/users"):
            return 200, {"data": [{"id": "4242"}]}
        if url.startswith(st.TWITCH_API + "/channels"):
            return (204, None) if headers["Authorization"] == "Bearer tw_new" else (401, {"message": "bad"})
        if url == st.GOOGLE_TOKEN:
            return 200, {"access_token": "yt_tok", "expires_in": 3599}
        if "liveBroadcasts?part=snippet&broadcastStatus=active" in url:
            return 200, {"items": []}
        if "broadcastStatus=upcoming" in url:
            return 200, {"items": [{"id": "b1", "snippet": {
                "title": "old", "description": "desc", "scheduledStartTime": "2026-10-20T10:00:00Z"}}]}
        if method == "PUT" and "liveBroadcasts" in url:
            return 200, {"id": "b1"}
        if url == st.KICK_API + "/channels":
            return 204, None
        raise AssertionError(f"unexpected call {method} {url}")

    real = st._http
    st._http = fake
    try:
        with tempfile.TemporaryDirectory() as td:
            cfg = {"retry_delays": [],
                   "twitch": {"client_id": "cid", "client_secret": "csec",
                              "refresh_token": "tw_r1", "user_token": "stale"},
                   "youtube": {"client_id": "g", "client_secret": "gs", "refresh_token": "yr"},
                   "kick": {"client_id": "", "client_secret": "", "refresh_token": "",
                            "user_token": "kick_tok"}}
            events = []
            t = st.StreamTitle(cfg, Path(td), on_change=events.append)
            assert all(p["configured"] for p in t.status()["platforms"] if p["supported"])
            out = t.set("  Walking   Shibuya at night ")
            by = {r["platform"]: r for r in out["results"]}
            assert out["title"] == "Walking Shibuya at night", out
            assert set(by) == {"twitch", "youtube", "kick", "x", "rumble"}, by
            assert by["twitch"]["ok"] and by["youtube"]["ok"] and by["kick"]["ok"], by
            assert not by["x"]["ok"] and "not supported" in by["x"]["message"]
            assert not by["rumble"]["ok"] and "not supported" in by["rumble"]["message"]
            # twitch: stale token got 401 -> refreshed -> retried; id looked up
            patch = [c for c in calls if c[0] == "PATCH" and "helix/channels" in c[1]]
            assert patch[-1][1].endswith("broadcaster_id=4242") and patch[-1][3] == {"title": out["title"]}
            assert patch[-1][2]["Client-Id"] == "cid"
            # youtube: upcoming broadcast, snippet carried over, title swapped
            put = next(c for c in calls if c[0] == "PUT")
            assert put[3] == {"id": "b1", "snippet": {"title": out["title"], "description": "desc",
                              "scheduledStartTime": "2026-10-20T10:00:00Z"}}, put
            kick = next(c for c in calls if c[1] == st.KICK_API + "/channels")
            assert kick[3] == {"stream_title": out["title"]} and kick[2]["Authorization"] == "Bearer kick_tok"
            # rotated refresh token persisted privately; nothing secret in answers
            saved = json.loads((Path(td) / "title_tokens.json").read_text())
            assert saved["twitch"]["refresh_token"] == "tw_r2", saved
            assert ((Path(td) / "title_tokens.json").stat().st_mode & 0o077) == 0
            blob = json.dumps([out, t.status(), events[0]])
            for secret in ("tw_new", "tw_r1", "tw_r2", "csec", "yt_tok", "yr", "gs", "kick_tok", "stale"):
                assert secret not in blob, secret
            # remembered across restarts, re-applied to one platform
            t2 = st.StreamTitle(cfg, Path(td))
            assert t2.status()["title"] == out["title"]
            n = len(calls)
            assert t2.apply("kick")["ok"] and len(calls) == n + 1
            # subset + long title cut for youtube
            r = t2.set("x" * 120, ["yt"])["results"]
            assert len(r) == 1 and r[0]["ok"] and "cut to 100" in r[0]["message"], r
            assert next(c for c in reversed(calls) if c[0] == "PUT")[3]["snippet"]["title"] == "x" * 100

        # nothing configured: ok=false per platform with a reason, no calls made
        with tempfile.TemporaryDirectory() as td:
            n = len(calls)
            t = st.StreamTitle({}, Path(td), platforms=["twitch", "youtube", "kick", "custom"])
            out = t.set("hello")
            assert out["ok"] is False and len(calls) == n, out
            assert all(not r["ok"] and r["message"] for r in out["results"]), out
            assert t.set("   ")["ok"] is False
            # a network failure is an answer too
            st._http = lambda *a, **k: (_ for _ in ()).throw(OSError("dns"))
            t = st.StreamTitle({"kick": {"user_token": "k"}}, Path(td), platforms=["kick"])
            r = t.set("hi")["results"][0]
            assert r["ok"] is False and "unreachable" in r["message"], r
    finally:
        st._http = real

    # REST: advertised, answers with no creds, the restream start hook is wired
    from autoclip.api import create_app
    from fastapi.testclient import TestClient
    p = _bare_pipeline()
    with TestClient(create_app(pipeline=p)) as client:
        sch = client.get("/api/autoclip/schema").json()
        assert {"live_title", "live_title_set"} <= {op["name"] for op in sch["operations"]}
        assert "stream_title" in sch["event_types"]
        r = client.post("/api/autoclip/live/title", json={"title": "Hi", "platforms": ["x"]})
        assert r.status_code == 200 and r.json()["results"][0]["ok"] is False, r.text
        g = client.get("/api/autoclip/live/title").json()
        assert g["title"] == "Hi" and {q["name"] for q in g["platforms"]} >= {"twitch", "rumble"}, g
        assert any(e["type"] == "stream_title" for e in
                   client.get("/api/autoclip/events/history").json()["events"])
    from autoclip.livestream import LiveStreamManager
    with tempfile.TemporaryDirectory() as td:
        mgr = LiveStreamManager({"targets": [{"name": "kick", "url": "rtmp://x", "key": "k"}]}, Path(td))
        mgr._spawn_locked = lambda t: None
        mgr._stop.set()
        started = []
        mgr.on_start = started.append
        mgr.start("kick")
        mgr.start("nope")
        assert started == ["kick"], started


def t_clip_posting():
    """Queue in dry_run, edits, async per-platform posting, retry, device
    shares, and the REST surface the phone uses (docs/CLIP_POSTING.md)."""
    import threading
    from types import SimpleNamespace

    from autoclip import pipeline as pl
    from autoclip import posting
    from autoclip.agents import ClipDecision
    from autoclip.buffer import Window
    from autoclip.clips import Clip
    from autoclip.publishers import PublishResult

    p = _bare_pipeline()
    try:
        assert p.cfg["publish"]["mode"] == "dry_run" and p.cfg["publish"]["queue"] == "always"
        # one cycle with everything but the queueing stubbed out
        win = Window(path=p.windows_dir / "w.mkv", start_wall=1000.0, duration=300.0, source="t")
        p.capture_window = lambda: win
        p.analyze = lambda w, with_frames=True: SimpleNamespace(to_dict=lambda: {}, moments=[])
        p.transcribe = lambda w: SimpleNamespace(note="", slice=lambda a, b: None)
        p.context = lambda *a: None
        p._emit_transcript_chunks = lambda *a: None
        p._emit_voice_commands = lambda *a: []
        p.agent = SimpleNamespace(name="t", propose=lambda ctx: [ClipDecision(
            start=10, end=35, score=0.9, title="Big jump", caption="send it",
            hashtags=["skate"], platforms=["youtube", "instagram"])])

        def fake_render(path, decision, cfg, out_dir, transcript=None, name=None, privacy=None):
            mp4, jpg = Path(out_dir) / f"{name}.mp4", Path(out_dir) / f"{name}.jpg"
            mp4.write_bytes(b"\x00" * 64)
            jpg.write_bytes(b"\xff")
            return Clip(path=mp4, start=decision.start, end=decision.end, duration=25.0,
                        decision=decision, thumb=jpg)

        real_render, pl.render_clip = pl.render_clip, fake_render
        try:
            res = p.run_cycle()
        finally:
            pl.render_clip = real_render
        pend = p.pending()
        assert len(pend) == 1, (pend, res.notes)          # queued although dry_run
        rec = pend[0]
        cid = rec["id"]
        assert rec["status"] == "ready" and rec["edits"]["title"] == "Big jump"
        assert rec["video_url"] == f"outbox/{cid}.mp4" and rec["thumb_url"] == f"outbox/{cid}.jpg"
        assert (p.workdir / "outbox" / f"{cid}.mp4").exists()   # preview is playable

        # edits
        rec = p.poster.edit(cid, caption="  new caption ", hashtags=["#a", "b", ""],
                            youtube_privacy="unlisted")
        assert rec["edits"]["caption"] == "new caption" and rec["edits"]["hashtags"] == ["a", "b"]
        try:
            p.poster.edit(cid, youtube_privacy="secret")
            raise AssertionError("bad privacy accepted")
        except ValueError:
            pass

        # posting is async: youtube blocks until released, instagram fails once
        gate, seen, ig_fail = threading.Event(), [], [True]

        def fake_publish(clip, platform, cfg, workdir):
            seen.append((platform, clip.decision.caption, list(clip.decision.hashtags),
                         (cfg.get("youtube") or {}).get("privacy"),
                         (cfg.get("server") or {}).get("public_base_url", None) is not None))
            if platform == "youtube":
                gate.wait(5)
                return PublishResult(platform="youtube", ok=True, url="https://youtube.com/shorts/v1",
                                     media_id="v1", message="uploaded")
            if ig_fail[0]:
                ig_fail[0] = False
                return PublishResult(platform="instagram", ok=False, message="container error")
            return PublishResult(platform="instagram", ok=True, url="https://instagram.com/reel/1")

        real_pub, posting.publish_one = posting.publish_one, fake_publish
        try:
            from fastapi.testclient import TestClient
            from autoclip.api import create_app
            client = TestClient(create_app(pipeline=p))

            plats = client.get("/api/autoclip/platforms").json()
            assert plats["mode"] == "dry_run" and plats["youtube_privacy"] == "public"
            by = {x["name"]: x for x in plats["platforms"]}
            assert by["youtube"]["path"] == "server" and by["tiktok"]["path"] == "device"
            assert by["x"]["limits"]["caption"] == 280
            if not by["youtube"]["configured"]:
                assert "YOUTUBE_REFRESH_TOKEN" in by["youtube"]["reason"], by["youtube"]

            r = client.post(f"/api/autoclip/clips/{cid}/post", json={"title": "Bigger jump"})
            assert r.status_code == 202, r.text
            assert r.json()["status"] == "posting", r.json()     # answered before youtube finished
            for _ in range(100):
                if client.get(f"/api/autoclip/clips/{cid}").json()["posts"]["instagram"]["state"] == "failed":
                    break
                time.sleep(0.02)
            gate.set()
            for _ in range(100):
                rec = client.get(f"/api/autoclip/clips/{cid}").json()
                if rec["status"] != "posting":
                    break
                time.sleep(0.02)
            assert rec["status"] == "partial", rec
            assert rec["posts"]["youtube"]["state"] == "posted"
            assert rec["posts"]["youtube"]["url"].endswith("/v1")
            assert rec["posts"]["instagram"]["message"] == "container error"
            assert rec["edits"]["title"] == "Bigger jump"
            assert seen[0][1] == "new caption" and seen[0][2] == ["a", "b"]
            assert {s[3] for s in seen} == {"unlisted"} and all(s[4] for s in seen)

            # retry posts only what failed
            gate.clear()
            gate.set()
            r = client.post(f"/api/autoclip/clips/{cid}/post", json={})
            assert r.status_code == 202
            for _ in range(100):
                rec = client.get(f"/api/autoclip/clips/{cid}").json()
                if rec["status"] != "posting":
                    break
                time.sleep(0.02)
            assert [s[0] for s in seen].count("youtube") == 1, seen
            assert rec["status"] == "done", rec

            # done records leave the queue for the posted list
            assert client.get("/api/autoclip/pending").json()["pending"] == []
            assert client.get("/api/autoclip/posted").json()["posted"][0]["id"] == cid

            # device platforms are the phone's: refused here, reported back
            assert client.post(f"/api/autoclip/clips/{cid}/post",
                               json={"platforms": ["tiktok"]}).status_code == 422
            r = client.post(f"/api/autoclip/clips/{cid}/shared", json={"platform": "tiktok"})
            assert r.json()["posts"]["tiktok"]["state"] == "shared", r.json()
            assert client.post(f"/api/autoclip/clips/{cid}/shared",
                               json={"platform": "youtube"}).status_code == 422
            assert client.get("/api/autoclip/clips/nope").status_code == 404

            # clip_status events reach the bus
            evs = [e for e in p.events.history(200) if e.type == "clip_status"]
            assert {e.extra["platform"] for e in evs} >= {"youtube", "instagram", "tiktok"}
        finally:
            posting.publish_one = real_pub

        # dry_run really is dry: the real publishers only touch the outbox
        p.state["pending"].append(posting.new_record(
            "d_0", "d", Clip(path=p.clips_dir / f"{cid}.mp4", start=0, end=25, duration=25,
                             decision=ClipDecision(start=0, end=25, title="t")), ["youtube"]))
        results = p.approve("d_0")
        assert results and results[0]["dry_run"] and results[0]["ok"], results
        assert p.poster.get("d_0")["posts"]["youtube"]["state"] == "dry_run"

        # a restart fails posts that were mid-upload instead of spinning forever
        p.state["pending"].append({"id": "x_0", "clip": {"path": "x.mp4"},
                                   "posts": {"youtube": {"state": "uploading"}}})
        again = posting.ClipPoster(p.cfg, p.workdir, p.state, p._state_lock, p._save_state)
        assert again.get("x_0")["posts"]["youtube"]["state"] == "failed"
        assert again.reject("x_0") and not again.reject("x_0")

        # YouTube: Shorts tag, public by default, configured from the refresh token
        from autoclip.publishers.youtube import YouTubePublisher, video_body
        clip = Clip(path=Path("c.mp4"), start=0, end=1, duration=1,
                    decision=ClipDecision(start=0, end=1, title="T", caption="C", hashtags=["#ski"]))
        body = video_body(clip, {"youtube": {}})
        assert body["status"]["privacyStatus"] == "public"
        assert body["snippet"]["description"].endswith("#ski #Shorts") and body["snippet"]["tags"] == ["ski"]
        yt = {"youtube": {"client_id": "i", "client_secret": "s", "refresh_token": "r",
                          "credentials": str(p.workdir / "none.json")}}
        assert YouTubePublisher().enabled(yt) and YouTubePublisher().missing(yt) == ""
        assert "YOUTUBE_REFRESH_TOKEN" in YouTubePublisher().missing({"youtube": {"client_id": "i"}})
    finally:
        p.shutdown()


# --------------------------------------------------------------------------- hud_stack
def t_hud_stack_graph():
    """The HUD layout builds one 1080x1920 graph from the configured boxes, and
    only applies to program-shaped (landscape) input."""
    from autoclip.clips import build_video_filter, hud_stack_graph, resolve_layout
    hud = load_config(ROOT / "autoclip.yaml")["render"]["hud_stack"]
    graph, band = hud_stack_graph(hud, 1080, 1920)
    assert graph.startswith("scale=1920:1080,"), graph
    assert "split=6" in graph and graph.endswith("vstack=inputs=2,setsar=1"), graph
    for box in ("compass", "camera", "avatar", "heartbeat", "magicka"):
        x, y, w, h = hud[box]
        assert f"crop={w}:{h}:{x}:{y}" in graph or box == "camera", (box, graph)
    # camera + band add up to the full height; the compass is in the band
    cam_h = int(graph.split("[hmid]")[0].rsplit("scale=", 1)[1].split(":")[1])
    assert cam_h + band == 1920, (cam_h, band)
    assert "[hbg][hkp]overlay" in graph and "[hb3][hav]overlay" in graph, \
        "compass, vitals and avatar sit on the band backdrop"
    assert band == hud["bottom_height"], band
    # the band backdrop is the camera blurred (matching OBS's side bars), with
    # the crops feathered into it; black keeps the old plain band
    cx, cy, cw, ch = hud["camera"]
    assert hud["band_background"] == "blur"
    assert f"[hb]crop={cw}:{ch}:{cx}:{cy}," in graph and "gblur=" in graph, graph
    assert graph.count("alphamerge") == 4, graph
    black, band2 = hud_stack_graph(dict(hud, band_background="black"), 1080, 1920)
    assert band2 == band and "gblur" not in black and "alphamerge" not in black
    assert "drawbox=t=fill:color=black[hbg]" in black, black
    assert "color=" not in black.split("drawbox")[0], "graph stays single-input"

    assert resolve_layout("hud_stack", 1920, 1080, hud) == "hud_stack"
    assert resolve_layout("hud_stack", 1280, 720, hud) == "hud_stack"   # CPU-path program
    assert resolve_layout("hud_stack", 720, 1280, hud) == "crop"        # raw glasses feed
    assert resolve_layout("crop", 1920, 1080, hud) == "crop"

    pre, post = build_video_filter("9:16", "hud_stack", 1080, 1920, 0.5, None,
                                   fps=30, hud=hud)
    assert pre == [graph, "fps=30"] and post == [], (pre, post)

    vps = load_config(ROOT / "autoclip.yaml")
    import yaml
    over = yaml.safe_load((ROOT / "deploy/obs-vps/autoclip.vps.yaml").read_text())
    assert over["render"]["layout"] == "hud_stack", over["render"]
    assert over["source"]["rtmp"]["stream_key"] == "program", over["source"]
    assert over["source"]["rtmp"]["fallback_key"] == "${STREAM_KEY}"
    assert vps["render"]["layout"] == "crop", "laptop default stays crop"


def t_rtmp_program_fallback():
    """The VPS source prefers live/program, drops to the raw feed while OBS
    isn't publishing, tags chunks per feed and never leaks either key."""
    from autoclip.buffer import Segment
    from autoclip.ingest import RTMPSource, build_source
    with tempfile.TemporaryDirectory() as td:
        src = build_source({"mode": "rtmp", "workdir": td, "rtmp": {
            "url": "rtmp://127.0.0.1:1935/live", "stream_key": "program",
            "fallback_key": "rawsecret42", "mediamtx_api": "http://127.0.0.1:1",
            "dir": td}})
        assert isinstance(src, RTMPSource) and src.api
        ready = {"program": True, "raw": True}
        src.path_ready = lambda feed: ready[feed]
        assert src._pick_feed() == "program"
        ready["program"] = False
        assert src._pick_feed() == "raw"           # OBS down
        ready.update(program=True, raw=False)
        assert src._pick_feed() == "raw"           # program frozen: glasses gone
        src.feed = "raw"
        assert src._url_for("raw").endswith("/rawsecret42")
        assert src._segment_pattern().startswith("raw_")
        st = src.status()
        assert st["feed"] == "raw" and "rawsecret42" not in str(st), st

        # no API: a pull that died flips to the other feed
        src2 = RTMPSource("rtmp://h/live", Path(td), stream_key="program",
                          fallback_key="k")
        assert src2.path_ready("program") is None
        src2._proc = type("Dead", (), {"poll": lambda self: 1})()
        src2.feed = "program"
        assert src2._pick_feed() == "raw"

        # unreachable API counts as "not publishing"
        src3 = RTMPSource("rtmp://h/live", Path(td), stream_key="program",
                          fallback_key="k", mediamtx_api="http://127.0.0.1:1")
        assert src3.path_ready("program") is False

        # chunks are tagged by the feed in their filename
        for name in ("program_20261020_120000.ts", "raw_20261020_120030.ts"):
            seg = Segment(path=Path(td) / name, start_wall=0, duration=1, source="watch_dir")
            src4 = RTMPSource("rtmp://h/live", Path(td), stream_key="program",
                              fallback_key="k")
            src4._proc = type("Live", (), {"poll": lambda self: None})()
            src4._checked = time.time()
            import autoclip.ingest as ing
            orig = ing.WatchDirSource.poll
            ing.WatchDirSource.poll = lambda self, _s=seg: [_s]
            try:
                got = src4.poll()
            finally:
                ing.WatchDirSource.poll = orig
            assert got[0].source == name.split("_")[0], got[0]


def t_obs_blur_background():
    """The OBS seed fills the side bars with a blurred copy of the glasses
    camera (a nested scene reusing the Glasses source, stock filters only),
    and start.sh adds it to a scene seeded before it existed."""
    import json, shutil, subprocess
    obs = ROOT / "deploy/obs-vps/obs"
    seed = json.loads((obs / "seed/IRL.json").read_text())
    src = {x["name"]: x for x in seed["sources"]}
    cam, blur = src["Glasses"], src["Glasses Blur"]
    assert blur["id"] == "scene" and cam["id"] == "ffmpeg_source"
    (inner,) = blur["settings"]["items"]
    assert inner["source_uuid"] == cam["uuid"], "reuses the camera: one RTMP decode"
    assert inner["bounds_type"] == 3 and inner["bounds"] == {"x": 1920.0, "y": 1080.0}  # cover
    ids = [f["id"] for f in blur["filters"]]
    assert ids == ["scale_filter", "scale_filter", "color_filter_v2"], ids
    assert blur["filters"][0]["settings"]["sampling"] == "area"
    items = src["IRL"]["settings"]["items"]
    assert [i["name"] for i in items][:3] == ["Glasses Blur", "Glasses", "Skyrim HUD"], \
        "blur is the bottom layer, under the sharp camera and the HUD"
    assert items[0]["source_uuid"] == blur["uuid"] and items[0]["bounds_type"] == 1
    assert len({i["id"] for i in items}) == len(items)
    assert src["IRL"]["settings"]["id_counter"] >= max(i["id"] for i in items)
    assert "jq" in (obs / "Dockerfile").read_text()

    # migration: start.sh's jq blocks (blur, then rtmp -> rtsp input) turn the
    # pre-blur seed into the new one
    start = (obs / "start.sh").read_text()
    block = start[start.index("SCENE="):start.index("# The stream output always follows")]
    old = subprocess.run(["git", "show", "a91aeba:livevision/deploy/obs-vps/obs/seed/IRL.json"],
                         cwd=ROOT, capture_output=True, text=True)
    if not shutil.which("jq") or old.returncode != 0:
        print("       (migration skipped: no jq or no git history)")
        return
    with tempfile.TemporaryDirectory() as td:
        scene = Path(td) / "IRL.json"
        scene.write_text(old.stdout)
        script = block.replace("/opt/obs-seed/IRL.json", str(obs / "seed/IRL.json")) \
                      .replace('"$CFG/basic/scenes/IRL.json"', f'"{scene}"')
        for _ in range(2):   # idempotent
            subprocess.run(["bash", "-c", script], check=True)
        got = json.loads(scene.read_text())
        norm = lambda d: json.dumps(dict(d, sources=sorted(d["sources"], key=lambda x: x["name"])),
                                    sort_keys=True)
        assert norm(got) == norm(seed), "migrated scene matches the seed"
        # a scene without a Glasses source is left alone (never emptied)
        scene.write_text(json.dumps({"sources": [], "scene_order": []}))
        subprocess.run(["bash", "-c", script], check=True)
        assert json.loads(scene.read_text()) == {"sources": [], "scene_order": []}


def _ffmpeg_ok() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def t_hud_stack_render():
    """A synthetic 1920x1080 program renders to a 1080x1920 hud_stack clip with
    burned captions; a portrait (raw feed) input falls back to crop; a window
    after a feed switch only holds the newest feed."""
    if not _ffmpeg_ok():
        print("       (skipped: no ffmpeg)")
        return
    from autoclip.buffer import RollingWindow, Segment
    from autoclip.clips import render_clip
    from autoclip.util import probe, run
    cfg = load_config(ROOT / "autoclip.yaml")
    rcfg = dict(cfg["render"], layout="hud_stack")
    tr = Transcript(words=[Word(i * 0.4, i * 0.4 + 0.35, w) for i, w in
                           enumerate("we found the dragon".split())], engine="fake")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        prog, raw = td / "program.mp4", td / "raw.mp4"
        for path, size in ((prog, "1920x1080"), (raw, "720x1280")):
            run(["ffmpeg", "-y", "-v", "error",
                 "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30",
                 "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                 "-t", "3", "-c:v", "libx264", "-preset", "ultrafast",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)],
                timeout=120)
        clip = render_clip(prog, ClipDecision(start=0.0, end=2.0, score=1.0, title="t"),
                           rcfg, td / "out", transcript=tr, name="hud")
        info = probe(clip.path)
        assert (info["width"], info["height"]) == (1080, 1920), info
        assert clip.captions_burned or any("libass" in n or "Pillow" in n
                                           for n in clip.notes), clip.notes
        if clip.ass:   # captions sit above the vitals + avatar band
            band = cfg["render"]["hud_stack"]["bottom_height"]
            style = next(l for l in clip.ass.read_text().splitlines()
                         if l.startswith("Style:"))
            assert style.split(",")[-2] == str(band + 40), style
        assert not any("not the program" in n for n in clip.notes), clip.notes
        # the band behind the HUD is blurred camera, not black
        band = cfg["render"]["hud_stack"]["bottom_height"]
        y_band = run(["ffmpeg", "-v", "error", "-i", str(clip.path), "-frames:v", "1",
                      "-vf", f"crop=1080:{band}:0:{1920 - band},scale=1:1,format=gray",
                      "-f", "rawvideo", "-"], timeout=60).stdout
        assert y_band and y_band[0] > 30, y_band

        fb = render_clip(raw, ClipDecision(start=0.0, end=2.0, score=1.0, title="t"),
                         rcfg, td / "out", name="raw")
        info = probe(fb.path)
        assert (info["width"], info["height"]) == (1080, 1920), info
        assert any("rendered with layout crop" in n for n in fb.notes), fb.notes

        # program -> raw switch mid-buffer: the window is the raw run only
        win = RollingWindow(300, td / "buf")
        win.add(Segment(path=prog, start_wall=1000, duration=3, source="program"))
        win.add(Segment(path=raw, start_wall=1003, duration=3, source="raw"))
        win.add(Segment(path=td / "gone.ts", start_wall=1006, duration=3, source="raw"))
        w = win.materialize(out_dir=td / "win")
        assert w.path == raw and [s.source for s in w.segments] == ["raw"], w.to_dict()


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
        ("live stream manager", t_live_manager), ("stream title", t_stream_title), ("command dispatcher", t_dispatcher),
        ("obs voice patterns", t_obs_voice_patterns),
        ("obs controller", t_obs_controller),
        ("obs dispatcher routing", t_dispatcher_obs),
        ("privacy blur", t_privacy),
        ("privacy voice grammar", t_privacy_voice),
        ("privacy dispatcher routing", t_privacy_dispatcher),
        ("dedupe across windows", t_dedupe_across_windows),
        ("head pose", t_head_pose),
        ("nav on stream: no place names", t_nav_stream_safe),
        ("imu gait (pocket phone)", t_imu_gait),
        ("locomotion gate", t_locomotion_gate),
        ("arm directions", t_arms),
        ("arm smoothing (1-euro)", t_arm_filter),
        ("band gestures", t_body_gestures),
        ("body tracking", t_body_tracking),
        ("hud heartbeat config", t_heartbeat_config),
        ("body punches", t_body_punches),
        ("apple maps phone route", t_phone_route),
        ("retention keeps disk bounded", t_retention_keeps_disk_bounded),
        ("captions one file per clip", t_captions_one_file_per_clip),
        ("voice fires once + rumble", t_voice_once_and_rumble),
        ("clip posting", t_clip_posting),
        ("hud_stack filter graph", t_hud_stack_graph),
        ("OBS blurred side bars", t_obs_blur_background),
        ("rtmp program/raw fallback", t_rtmp_program_fallback),
        ("hud_stack render 1080x1920", t_hud_stack_render),
    ]:
        check(name, fn)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    for name, exc in FAIL:
        print(f"  - {name}: {exc}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
