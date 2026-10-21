"""HUDstream server: mic + camera + compass + gestures -> OBS browser source."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from typing import Set

import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .attributes import AttributeClassifier
from .audio import AudioAnalyzer
from .config import load_config
from .desktop import DesktopActivity
from .devices.meta_glass import lan_ip
from .discovery import Discovery
from .focus import FocusRecognizer
from .gestures import GestureBus
from .imu import IMUHub
from .headpose import HeadPose
from .body import Body
from .activity import LocomotionGate
from .navigation import Navigation, parse_coords, stream_safe
from .progress import load as progress_load, save as progress_save
from .sensors import HeadingHub
from .shouts import Shouts
from .skills import SKILL_NAMES, SkillEngine
from .state import World
from .video import VideoAnalyzer
from .vtube_studio import VTubeStudio

ROOT = Path(__file__).resolve().parents[1]
OVERLAY_DIR = ROOT / "overlay"
WEB_DIR = ROOT / "web"


class Runtime:
    def __init__(self, cfg: dict, optin_attributes: bool = False):
        self.cfg = cfg
        self.world = World(started=time.time())
        self.audio = AudioAnalyzer(cfg.get("audio", {}))
        self.video = VideoAnalyzer(cfg.get("video", {}))
        self.heading = HeadingHub(cfg.get("heading", {}))
        self.engine = SkillEngine(cfg.get("skills", {}))
        self.nav = Navigation(cfg.get("navigation", {}))
        self.nav_details = bool((cfg.get("navigation") or {}).get("stream_details", False))
        self.gestures = GestureBus(cfg.get("gestures", {}))
        self.attributes = AttributeClassifier(cfg.get("attributes", {}), optin_attributes)
        self.desktop = DesktopActivity(cfg.get("desktop", {}))
        self.shouts = Shouts(cfg.get("shouts", {}))
        self.discovery = Discovery(cfg.get("discovery", {}))
        self.focus = FocusRecognizer(cfg.get("focus", {}))
        self.imu = IMUHub(cfg.get("imu", {}))
        self.head = HeadPose(cfg.get("head", {}))
        self.body = Body(cfg.get("body", {}))
        self.gait = LocomotionGate(cfg.get("activity", {}))
        self.vtube = VTubeStudio(cfg.get("vtube_studio", {}))
        self.vtube.start()
        self._skill_prev = {k: False for k in SKILL_NAMES}
        self._last_focus = {"kind": "other", "confidence": 0.0,
                             "source": "init", "features": {}, "stats": {}}
        self.progress_cfg = cfg.get("progress", {}) or {}
        self.clients: Set[WebSocket] = set()
        self.phone_clients: Set[WebSocket] = set()
        self.gesture_clients: Set[WebSocket] = set()
        self.sources = {"audio": "sim", "video": "sim", "heading": "sim"}
        self.nav_state = {"active": False}
        self._last_save = 0.0

    def start(self) -> None:
        self.sources["audio"] = self.audio.start()
        self.sources["video"] = self.video.start()
        self.heading.start()
        self.sources["heading"] = self.cfg.get("heading", {}).get("mode", "auto")
        if self.progress_cfg.get("enabled"):
            loaded = progress_load(self.progress_cfg.get("path", "data/progress.json"))
            if loaded:
                self.engine.load_state(loaded)
                print(f"[hudstream] loaded progress from {self.progress_cfg.get('path')}")
        print(f"[hudstream] sources: {self.sources}")

    def stop(self) -> None:
        self.audio.stop()
        self.video.stop()
        self.heading.stop()
        self._save_progress(force=True)

    def focus_result(self) -> dict:
        return self._last_focus

    def _dispatch_vtube(self, events: list) -> None:
        """Edge-detect skill activations + fire VTube Studio triggers for
        shouts, skill level-ups and focus transitions. Idempotent and
        throttled by the VTS client."""
        skills = self.world.skills
        if skills:
            prev = self._skill_prev
            for key, rec in skills.items():
                cur = bool(rec.get("active"))
                if cur and not prev.get(key, False):
                    self.vtube.trigger(key)
                prev[key] = cur
        cur_focus = self.world.vision.focus
        if cur_focus and cur_focus != getattr(self, "_prev_focus", ""):
            self.vtube.trigger(cur_focus)
            self._prev_focus = cur_focus
        for ev in events:
            if ev.get("type") == "shout":
                word = (ev.get("text") or ev.get("shout") or "").lower()
                if "fus" in word: self.vtube.trigger("shout_fus")
                elif "yol" in word: self.vtube.trigger("shout_yol")
                elif "wuld" in word: self.vtube.trigger("shout_wuld")
                else: self.vtube.trigger("shout_generic")
            elif ev.get("type") == "skill_level":
                self.vtube.trigger("level_up")
            elif ev.get("type") == "level":
                self.vtube.trigger("level_up")

    def _save_progress(self, force: bool = False) -> None:
        if not self.progress_cfg.get("enabled"):
            return
        if not force and (time.time() - self._last_save
                          < float(self.progress_cfg.get("autosave_s", 30))):
            return
        if progress_save(self.progress_cfg.get("path", "data/progress.json"),
                         self.engine.export()):
            self._last_save = time.time()

    # ------------------------------------------------------------------ inputs
    def handle_phone(self, text: str) -> None:
        try:
            data = json.loads(text)
        except Exception:
            return
        if not isinstance(data, dict):
            return

        # heading
        got_heading = False
        for key in ("heading", "azimuth", "compass", "bearing"):
            if key in data:
                try:
                    self.heading.set_phone(float(data[key]), data.get("accuracy", 0.0))
                    got_heading = True
                except (TypeError, ValueError):
                    pass
                break
        if not got_heading and "alpha" in data:      # Android absolute orientation
            try:
                self.heading.set_phone((360.0 - float(data["alpha"])) % 360.0,
                                       data.get("accuracy", 0.0))
            except (TypeError, ValueError):
                pass

        # GPS for navigation
        lat, lon = data.get("lat"), data.get("lon")
        if lat is None:
            lat, lon = data.get("latitude"), data.get("longitude")
        if lat is not None and lon is not None:
            try:
                self.nav.set_position(float(lat), float(lon))
            except (TypeError, ValueError):
                pass

        # Apple Maps turn-by-turn from the companion (MKDirections on the phone)
        if isinstance(data.get("route"), dict):
            self.nav.set_phone_route(data["route"])

        # glasses battery (DAT DeviceState), flat or nested under "glasses"
        g = data.get("glasses") if isinstance(data.get("glasses"), dict) else data
        if "glasses_battery" in data or (g is not data and "battery" in g):
            self.set_glasses(g.get("battery", data.get("glasses_battery")),
                             g.get("charging", data.get("glasses_charging")))

        # gestures (if the bridge app forwards them)
        if data.get("gesture"):
            self.handle_gesture(str(data["gesture"]), "phone")

        # head orientation (glasses Motion quaternion, or yaw/pitch/roll)
        if isinstance(data.get("head"), dict):
            self.head.ingest(data["head"], source="phone-ws")
        # body: posture, hands, wrists (watch / Neural Band), heart rate
        if isinstance(data.get("body"), dict):
            self.body.ingest(data["body"], source="phone-ws")

        # IMU sample (devicemotion) — single or batch
        imu = data.get("imu")
        if isinstance(imu, dict):
            self.imu.ingest(imu, source="phone-ws")
        elif isinstance(imu, list):
            self.imu.ingest_batch(imu, source="phone-ws")

    def set_glasses(self, battery, charging=None) -> dict:
        """Glasses battery for the HUD's magicka bar. `charging` takes a bool
        or DAT's ChargingState name (CHARGING / NOT_CHARGING / UNKNOWN)."""
        g = self.world.glasses
        try:
            g["battery"] = max(0, min(100, int(round(float(battery)))))
        except (TypeError, ValueError):
            g["battery"] = None
        if isinstance(charging, str):
            charging = {"charging": True, "not_charging": False}.get(charging.lower())
        g["charging"] = charging if isinstance(charging, bool) else None
        g["ts"] = time.time()
        return dict(g)

    def handle_gesture(self, gesture: str, source: str = "api") -> dict:
        event = self.gestures.handle(gesture, source)
        if event:
            self.world.events.append(event)
        return event or {"ok": False, "reason": "ignored"}

    # ------------------------------------------------------------------ broadcast
    def build_payload(self, events: list) -> dict:
        w = self.world
        return {
            "t": time.time(),
            "audio": {
                "level": round(w.audio.level, 3),
                "speaking": w.audio.speaking,
                "talk_ratio": round(w.audio.talk_ratio, 2),
                "bands": [round(b, 3) for b in w.audio.bands],
                "viseme": w.audio.viseme,
                "openness": round(w.audio.openness, 3),
                "width": round(w.audio.width, 3),
                "source": w.audio.source,
            },
            "vision": {
                "motion": round(w.vision.motion, 3),
                "people": w.vision.people,
                "faces": w.vision.faces,
                "running": w.vision.running,
                "moving": w.vision.moving,
                "brightness": round(w.vision.brightness, 3),
                "fps": w.vision.fps,
                "source": str(w.vision.source),
                "activity": w.vision.activity,
                "cadence": w.vision.cadence,
                "attributes": w.vision.attributes,
                "text_rows": w.vision.text_rows,
                "focus": w.vision.focus,
            },
            "imu": w.imu,
            "head": self.head.snapshot(),
            "body": self.body.snapshot(),
            "focus": RT.focus_result(),
            "heading": {
                "deg": w.heading.deg,
                "raw": w.heading.raw,
                "source": w.heading.source,
                "accuracy": w.heading.accuracy,
            },
            "vitals": {
                "health": round(w.vitals.health, 1),
                "magicka": round(w.vitals.magicka, 1),
                "stamina": round(w.vitals.stamina, 1),
            },
            "glasses": {
                "battery": w.glasses["battery"],
                "charging": w.glasses["charging"],
                # DAT stops updating when the glasses disconnect: say so
                "fresh": time.time() - float(w.glasses["ts"]) < 120,
            },
            "skills": self.engine.to_dict(),
            "player_level": self.engine.player_level,
            "level_progress": round(self.engine.level_progress(), 3),
            # what the stream shows (and anyone with the overlay URL can read):
            # no street names, steps or destination. navigation.stream_details
            # puts them back
            "nav": self.nav_state if self.nav_details else stream_safe(self.nav_state),
            "ui": self.gestures.ui(),
            "attributes": self.attributes.snapshot(),
            "desktop": {
                "app": w.desktop.app,
                "title": w.desktop.title,
                "kind": w.desktop.kind,
                "source": w.desktop.source,
            },
            "shout": w.shout,
            "discovery": {"status": self.discovery.status, "count": len(self.discovery._seen)},
            "events": events,
        }

    async def loop(self, interval: float) -> None:
        last = time.time()
        last_nav = 0.0
        while True:
            await asyncio.sleep(interval)
            now = time.time()
            dt = max(0.0, min(0.5, now - last))
            last = now

            self.world.audio = self.audio.tick(dt)
            self.world.desktop = self.desktop.tick(dt)
            self.shouts.update(dt, self.world.audio, self.world)
            self.world.shout = self.shouts.state()

            vision = self.video.tick(dt)
            frame, rects = self.video.faces_for_attributes()
            counts = self.attributes.update(frame, rects)
            focus_info = self.focus.classify(frame, vision.motion)
            self._last_focus = focus_info

            # IMU augments the activity label (treadmill, stationary, shadowboxing)
            imu_info = self.imu.compute()
            self.world.imu = imu_info
            cam_act = vision.activity or "idle"
            imu_act = imu_info.get("activity", "idle") if imu_info.get("fresh") else "idle"
            from_camera = True
            if imu_info.get("fresh"):
                # the phone in a pocket feels footfalls: with fresh data it
                # decides the gait outright, and "idle" means no walking even
                # when the head-worn camera sees motion (boxing / lifting from
                # the camera still count: the pocket can't see your arms)
                from_camera = False
                # the pocket feels footfalls, not arms: its "boxing" is noise
                if imu_act not in ("idle", "boxing"):
                    activity, cadence = imu_act, imu_info.get("cadence", 0.0) or 0.0
                else:
                    activity, cadence = "idle", 0.0
            else:
                activity, cadence = cam_act, vision.cadence
            # the camera is on your head: head turns and sitting aren't a gait,
            # and a gait has to hold a moment before the avatar starts one
            body_snap = self.body.snapshot()
            activity = self.gait.update(now, activity, from_camera=from_camera,
                                        sitting=body_snap.get("posture") == "sitting",
                                        head=self.head.snapshot())
            running = activity == "running"
            moving = activity in ("walking", "running", "boxing", "lifting")
            self.world.vision = replace(vision, attributes=counts, focus=focus_info["kind"],
                                        activity=activity, cadence=cadence,
                                        running=running, moving=moving)
            self.world.heading = self.heading.tick(dt)
            self.engine.update(dt, self.world)

            if now - last_nav > 1.0:
                last_nav = now
                state = self.nav.tick()
                if state.get("arrived") and self.nav_state.get("active"):
                    self.world.events.append({
                        "type": "arrival",
                        "text": f"You have arrived at {state['objective']['name']}",
                    })
                self.nav_state = state
                self.discovery.tick(self.nav.pos, self.world)

            self._save_progress()
            events = self.world.drain_events()
            self._dispatch_vtube(events)
            payload = self.build_payload(events)
            dead = []
            for ws in list(self.clients):
                try:
                    await ws.send_text(json.dumps(payload))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.clients.discard(ws)


RT: Runtime | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    assert RT is not None
    RT.start()
    if (RT.cfg.get("heading", {}).get("ble") or {}).get("enabled"):
        asyncio.create_task(RT.heading.start_ble())
    task = asyncio.create_task(RT.loop(1.0 / float(RT.cfg["server"].get("tick_hz", 20))))
    try:
        yield
    finally:
        task.cancel()
        RT.stop()


app = FastAPI(title="HUDstream", lifespan=lifespan)


@app.middleware("http")
async def overlay_revalidate(request: Request, call_next):
    """OBS's browser source keeps a disk cache across restarts and happily
    serves last deploy's ES modules; make it revalidate (ETags keep it cheap)."""
    response = await call_next(request)
    if request.url.path.startswith("/overlay/"):
        response.headers["Cache-Control"] = "no-cache"
    return response
app.mount("/overlay", StaticFiles(directory=str(OVERLAY_DIR)), name="overlay")
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="web")


@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "dashboard.html")


@app.get("/phone")
async def phone():
    return FileResponse(WEB_DIR / "phone.html")


@app.get("/api/config")
async def api_config():
    assert RT is not None
    cfg = RT.cfg
    return JSONResponse({
        "markers": cfg.get("markers", []),
        "tick_hz": cfg["server"].get("tick_hz", 20),
        "bars": cfg["audio"].get("bars", 12),
        "skills": cfg["skills"].get("rules", {}),
        "gestures": cfg["gestures"].get("mapping", {}),
        "avatar": {
            "theme": cfg.get("avatar", {}).get("theme", "default"),
            "themes": cfg.get("avatar", {}).get("themes",
                ["default", "dark_swordsman", "green_scout",
                 "silver_knight", "blonde_prince", "hacker"]),
            "engine": cfg.get("avatar", {}).get("engine", "procedural"),
            "model": cfg.get("avatar", {}).get("model", ""),
            "layout": cfg.get("avatar", {}).get("layout", "full"),
            "render_scale": cfg.get("avatar", {}).get("render_scale", 0.75),
            "mirror": cfg.get("avatar", {}).get("mirror", True),
            "sync_delay_ms": cfg.get("avatar", {}).get("sync_delay_ms", 0),
            "vtube_studio": RT.vtube.status(),
        },
        "overlay": {
            "vicinity_ad": cfg.get("overlay", {}).get("vicinity_ad", True),
        },
        "heartbeat": {
            "enabled": bool(cfg.get("heartbeat", {}).get("enabled", True)),
            "high_bpm": cfg.get("heartbeat", {}).get("high_bpm", 150),
        },
    })


@app.get("/api/status")
async def api_status():
    assert RT is not None
    return JSONResponse({
        "sources": RT.sources,
        "heading": RT.heading.status(),
        "uptime": round(time.time() - RT.world.started, 1),
        "clients": len(RT.clients),
        "phones": len(RT.phone_clients),
        "skills": RT.engine.to_dict(),
        "player_level": RT.engine.player_level,
        "vitals": {
            "health": round(RT.world.vitals.health, 1),
            "magicka": round(RT.world.vitals.magicka, 1),
            "stamina": round(RT.world.vitals.stamina, 1),
        },
        "nav": RT.nav_state if RT.nav_details else stream_safe(RT.nav_state),   # public, like the stream
        "ui": RT.gestures.ui(),
        "attributes": RT.attributes.snapshot(),
        "desktop": {"app": RT.world.desktop.app, "kind": RT.world.desktop.kind,
                    "source": RT.world.desktop.source, "title": RT.world.desktop.title},
        "focus": RT.focus_result(),
        "imu": RT.world.imu,
        "avatar": {
            "theme": RT.cfg.get("avatar", {}).get("theme", "default"),
            "engine": RT.cfg.get("avatar", {}).get("engine", "procedural"),
            "vtube_studio": RT.vtube.status(),
        },
        "shout": RT.world.shout,
        "discovery": {"status": RT.discovery.status,
                       "count": len(RT.discovery._seen)},
    })


# ---------------------------------------------------------------- desktop / shouts
@app.post("/api/desktop")
async def api_desktop(request: Request):
    """Manually report the frontmost app + title (Hammerspoon, AutoHotkey, etc).
    Informational only — the camera-based focus recognizer drives the
    Intelligence / Enchanting skills, not this endpoint."""
    assert RT is not None
    body = await request.json()
    RT.desktop.set(str(body.get("app", "")), str(body.get("title", "")))
    return JSONResponse({"ok": True,
                          "kind": RT.desktop.state.kind,
                          "app": RT.desktop.state.app})


@app.post("/api/focus")
async def api_focus(request: Request):
    """Force-set the focus kind (testing). The camera recognizer will take
    over again on the next frame."""
    assert RT is not None
    body = await request.json()
    kind = str(body.get("kind", "")).lower()
    if kind not in ("reading", "coding", "other"):
        return JSONResponse({"ok": False, "error": "kind must be reading|coding|other"})
    RT.focus._ema_kind = kind
    RT.focus._ema_conf = 1.0
    return JSONResponse({"ok": True, "kind": kind})


@app.get("/api/vtube")
async def api_vtube_status():
    """VTube Studio connection status + the action map the HUD will fire."""
    assert RT is not None
    return JSONResponse(RT.vtube.status())


@app.post("/api/vtube")
async def api_vtube_trigger(request: Request):
    """Manually fire a VTube Studio action (e.g. 'shout_fus')."""
    assert RT is not None
    body = await request.json()
    action = str(body.get("action", "")).strip()
    if not action:
        return JSONResponse({"ok": False, "error": "action required"})
    fired = RT.vtube.trigger(action)
    return JSONResponse({"ok": fired, "action": action,
                         "status": RT.vtube.status()})


@app.post("/api/avatar")
async def api_avatar(request: Request):
    """Switch the overlay's procedural avatar theme at runtime."""
    assert RT is not None
    body = await request.json()
    theme = str(body.get("theme", "")).strip()
    valid = RT.cfg.get("avatar", {}).get("themes",
            ["default", "dark_swordsman", "green_scout",
             "silver_knight", "blonde_prince", "hacker"])
    if theme not in valid:
        return JSONResponse({"ok": False, "error": f"unknown theme; valid: {valid}"})
    RT.cfg.setdefault("avatar", {})["theme"] = theme
    return JSONResponse({"ok": True, "theme": theme, "themes": valid})


@app.post("/api/shout")
async def api_shout(request: Request):
    """Force a shout (e.g. for tests)."""
    assert RT is not None
    body = await request.json()
    if str(body.get("word")):
        RT.world.events.append({"type": "shout", "text": body["word"], "shout": body["word"]})
        return JSONResponse({"ok": True, "shout": body["word"]})
    return JSONResponse({"ok": False})


@app.get("/api/progress")
async def api_progress():
    assert RT is not None
    return JSONResponse(RT.engine.export())


# ---------------------------------------------------------------- navigation
@app.get("/api/navigation")
async def api_navigation():
    assert RT is not None
    return JSONResponse(RT.nav_state)


@app.post("/api/destination")
async def api_destination(request: Request):
    """Set the objective from coords, a place name, or any maps share link."""
    assert RT is not None
    body = await request.json()
    if body.get("clear"):
        RT.nav.clear()
        return JSONResponse({"ok": True, "nav": {"active": False}})
    link = body.get("link")
    if link:
        coords = parse_coords(str(link))
        if coords:
            return JSONResponse({"ok": True, "lat": coords[0], "lon": coords[1],
                                 "set": RT.nav.set_destination(*coords,
                                                                name=body.get("name"))})
        return JSONResponse({"ok": False, "error": "no coordinates in link"})
    ok = RT.nav.set_destination(body.get("lat"), body.get("lon"),
                                body.get("query"), body.get("name"))
    return JSONResponse({"ok": bool(ok), "nav": _nav_public(RT.nav.tick())})


@app.post("/api/route")
async def api_route(request: Request):
    """Paste directions from Meta Maps / Google Maps / Apple Maps:
    {"destination": {"lat","lon","name"}, "steps": [{"lat","lon","instruction","distance"}]}

    Or {"route": {...}}: the companion's Apple Maps progress message, as it
    arrives on /ws/phone (for testing the overlay without a phone).
    """
    assert RT is not None
    body = await request.json()
    if isinstance(body.get("route"), dict):
        ok = RT.nav.set_phone_route(body["route"])
        return JSONResponse({"ok": ok, "nav": _nav_public(RT.nav.tick())})
    RT.nav.set_route(body.get("destination"), body.get("steps"))
    return JSONResponse({"ok": True, "nav": _nav_public(RT.nav.tick())})


# ------------------------------------------------------------------ gestures
@app.post("/api/gesture")
async def api_gesture(request: Request):
    assert RT is not None
    body = await request.json()
    return JSONResponse(RT.handle_gesture(str(body.get("gesture", "")), "api"))


@app.websocket("/ws/gesture")
async def ws_gesture(ws: WebSocket):
    assert RT is not None
    await ws.accept()
    RT.gesture_clients.add(ws)
    try:
        while True:
            text = await ws.receive_text()
            try:
                data = json.loads(text)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("gesture"):
                RT.handle_gesture(str(data["gesture"]), "ws")
    except Exception:
        pass
    finally:
        RT.gesture_clients.discard(ws)


# ------------------------------------------------------------------ streams
@app.websocket("/ws")
async def ws_overlay(ws: WebSocket):
    assert RT is not None
    await ws.accept()
    RT.clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except Exception:
        pass
    finally:
        RT.clients.discard(ws)


@app.websocket("/ws/phone")
async def ws_phone(ws: WebSocket):
    assert RT is not None
    await ws.accept()
    RT.phone_clients.add(ws)
    try:
        while True:
            RT.handle_phone(await ws.receive_text())
    except Exception:
        pass
    finally:
        RT.phone_clients.discard(ws)


# ------------------------------------------------------------------ glasses
@app.post("/api/glasses")
async def api_glasses(request: Request):
    """Glasses battery from the phone app (DAT DeviceState). The phone page's
    WebSocket takes the same thing as {"glasses": {"battery", "charging"}}.

    Body: {"battery": 72, "charging": false}
    """
    assert RT is not None
    body = await request.json()
    return JSONResponse({"ok": True, "glasses": RT.set_glasses(body.get("battery"), body.get("charging"))})


# ------------------------------------------------------------------ head pose
@app.post("/api/head")
async def api_head(request: Request):
    """Head orientation for the avatar (testing, or a client without the WS).

    Body: {"q": [w,x,y,z]} | {"yaw":..,"pitch":..,"roll":..}, optional "recenter".
    """
    assert RT is not None
    ok = RT.head.ingest(await request.json(), source="http")
    return JSONResponse({"ok": ok, "head": RT.head.snapshot()})


def _nav_public(state):
    """These answers go through the same public host as the overlay."""
    return state if RT.nav_details else stream_safe(state)


@app.post("/api/body")
async def api_body(request: Request):
    """Body tracking for the avatar (see server/body.py for the fields)."""
    assert RT is not None
    ok = RT.body.ingest(await request.json(), source="http")
    return JSONResponse({"ok": ok, "body": RT.body.snapshot()})


# ------------------------------------------------------------------ IMU
@app.post("/api/imu")
async def api_imu(request: Request):
    """Batch-post `devicemotion` samples (testing or non-WS clients).

    Body: {"samples":[{ax,ay,az,gx,gy,gz,t}, ...], "reset": false}
    """
    assert RT is not None
    body = await request.json()
    if body.get("reset"):
        RT.imu._buf.clear()
        RT.imu._last_seen = 0.0
        RT.imu._source = "none"
    n = RT.imu.ingest_batch(body.get("samples", []), source="http")
    snap = RT.imu.to_snapshot()
    return JSONResponse({"ok": True, "ingested": n, "imu": snap})


@app.websocket("/ws/imu")
async def ws_imu(ws: WebSocket):
    assert RT is not None
    await ws.accept()
    try:
        while True:
            text = await ws.receive_text()
            try:
                data = json.loads(text)
            except Exception:
                continue
            if isinstance(data, list):
                RT.imu.ingest_batch(data, source="imu-ws")
            elif isinstance(data, dict) and data.get("samples"):
                RT.imu.ingest_batch(data["samples"], source="imu-ws")
            elif isinstance(data, dict):
                RT.imu.ingest(data, source="imu-ws")
    except Exception:
        pass


def main():
    global RT
    parser = argparse.ArgumentParser(description="HUDstream server")
    parser.add_argument("--config", default=str(ROOT / "config.yaml"))
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-audio", action="store_true", help="force simulated audio")
    parser.add_argument("--no-video", action="store_true", help="force simulated vision")
    parser.add_argument("--sim", action="store_true", help="simulate everything")
    parser.add_argument("--optin-attributes", action="store_true",
                        help="REQUIRED to run face-attribute inference (off by default)")
    parser.add_argument("--ssl-cert", default=None, help="enable HTTPS (iPhone sensors)")
    parser.add_argument("--ssl-key", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.host:
        cfg["server"]["host"] = args.host
    if args.port:
        cfg["server"]["port"] = args.port
    if args.no_audio or args.sim:
        cfg["audio"]["enabled"] = False
    if args.no_video or args.sim:
        cfg["video"]["enabled"] = False
    if args.sim:
        cfg["heading"]["mode"] = "sim"

    optin = args.optin_attributes or os.getenv("HUDSTREAM_OPTIN_ATTRIBUTES") == "1"
    RT = Runtime(cfg, optin_attributes=optin)
    rizz = cfg.get("skills", {}).get("rizz") or {}
    if str(rizz.get("mode", "conversation")).lower() == "gender" and not RT.attributes.enabled:
        print("[hudstream] WARNING: skills.rizz.mode is 'gender' but face attributes are "
              "disabled -> rizz will never fire. Set attributes.enabled + --optin-attributes, "
              "or use mode: conversation")
    host = cfg["server"]["host"]
    port = int(cfg["server"]["port"])
    print(f"[hudstream] overlay -> http://127.0.0.1:{port}/overlay/index.html")
    print(f"[hudstream] phone bridge -> http://{lan_ip()}:{port}/phone")
    uvicorn.run(app, host=host, port=port, log_level="info",
                ssl_certfile=args.ssl_cert, ssl_keyfile=args.ssl_key)


if __name__ == "__main__":
    main()
