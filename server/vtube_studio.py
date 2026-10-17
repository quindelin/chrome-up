"""VTube Studio Plugin API client (background thread, sync-callable).

VTube Studio (https://denchisoft.com/) is a popular Live2D / 3D VTuber
app for Windows + macOS. Its Plugin API is a WebSocket served on
`ws://localhost:8001` by default. We use it to trigger model hotkeys and
switch expressions whenever the HUD fires a shout, detects a skill, or
changes focus — so a real licensed model (Kirito / Eren / your own art)
loaded in VTube Studio reacts in sync with the mic audio you routed to
it via a virtual audio device (BlackHole on macOS, voiceMeeter /
ASIO Link on Windows).

We do NOT ship any copyrighted model. The model is yours to provide
through VTube Studio's model store, a free CC0 base, or your own art.

API basics (https://github.com/DenchiSoft/VTubeStudio):

  request  = {"apiName":"VTubeStudioPublicAPI",
              "apiVersion":"1.0",
              "requestID":"<uuid>",
              "messageType":"HotkeyTriggerRequest"|"...",
              "data":{...}}
  response = { ..., "returnedError":bool, "messageCode":int,
              "messageString":"...", "data":{...} }

Auth flow:
  1. Open Settings -> Plugins -> "Start API Server" in VTube Studio.
  2. First connect with no token -> API returns `RequiresAuth`.
  3. We send `AuthenticationTokenRequest`; VTube Studio shows a
     6-digit code dialog and the user types it.
  4. The token is cached at `~/.cache/hudstream/vts_token.json` so we
     don't re-prompt on every launch.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import queue
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Optional

try:
    import websockets
    from websockets.exceptions import ConnectionClosed
    _HAS_WS = True
except Exception:  # pragma: no cover
    _HAS_WS = False


log = logging.getLogger("hudstream.vtube")

CACHE_DIR = Path.home() / ".cache" / "hudstream"
TOKEN_PATH = CACHE_DIR / "vts_token.json"


class VTubeStudio:
    def __init__(self, cfg: Optional[dict] = None):
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", False))
        self.host = str(cfg.get("host", "127.0.0.1"))
        self.port = int(cfg.get("port", 8001))
        self.token = self._load_token() or str(cfg.get("token", "") or "")
        self.uri = f"ws://{self.host}:{self.port}"
        self.hotkeys: Dict[str, str] = dict(cfg.get("hotkeys") or {})
        self.expressions: Dict[str, str] = dict(cfg.get("expressions") or {})
        self.reconnect_s = float(cfg.get("reconnect_s", 5.0))
        self.timeout_s = float(cfg.get("timeout_s", 4.0))
        self.cooldown_s = float(cfg.get("hotkey_cooldown_s", 0.6))
        # shared state
        self._connected = False
        self._last_event_at = 0.0
        self._last_error = ""
        self._last_sent: Dict[str, float] = {}
        # thread + queue
        self._q: "queue.Queue[dict]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------ token
    def _load_token(self) -> str:
        try:
            return json.loads(TOKEN_PATH.read_text()).get("token", "")
        except Exception:
            return ""

    def _save_token(self, token: str) -> None:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            TOKEN_PATH.write_text(json.dumps({"token": token}))
        except Exception as e:
            log.warning("could not save VTS token: %s", e)

    # ------------------------------------------------------------------ public
    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "host": self.host,
            "port": self.port,
            "uri": self.uri,
            "connected": self._connected,
            "has_token": bool(self.token),
            "hotkeys": list(self.hotkeys.keys()),
            "expressions": list(self.expressions.keys()),
            "last_event_age": (round(time.time() - self._last_event_at, 1)
                               if self._last_event_at else None),
            "last_error": self._last_error,
        }

    def start(self) -> None:
        if not self.enabled or not _HAS_WS:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                         name="vts-client")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        try:
            self._q.put_nowait({"type": "_shutdown"})
        except Exception:
            pass

    def trigger(self, action: str) -> bool:
        """Trigger a hotkey or expression by config name. Throttled per action."""
        if not self.enabled:
            return False
        now = time.time()
        if now - self._last_sent.get(action, 0.0) < self.cooldown_s:
            return False
        self._last_sent[action] = now
        if not self._connected:
            return False
        if action in self.hotkeys:
            self._q.put({"type": "hotkey", "id": self.hotkeys[action]})
            return True
        if action in self.expressions:
            self._q.put({"type": "expression", "file": self.expressions[action],
                         "active": True})
            return True
        return False

    def load_model_by_id(self, model_id: str) -> None:
        self._q.put({"type": "load_model", "id": model_id})

    # ------------------------------------------------------------------ thread
    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._main())
        finally:
            try:
                loop.close()
            except Exception:
                pass

    async def _main(self) -> None:
        while not self._stop.is_set():
            try:
                async with websockets.connect(self.uri,
                                              open_timeout=self.timeout_s,
                                              max_size=2 ** 20) as ws:
                    self._last_error = ""
                    await self._authenticate(ws)
                    self._connected = True
                    log.info("VTube Studio connected @ %s", self.uri)
                    await self._pump(ws)
            except Exception as e:
                self._connected = False
                self._last_error = str(e)[:200]
            for _ in range(int(self.reconnect_s * 10)):
                if self._stop.is_set():
                    return
                await asyncio.sleep(0.1)

    async def _authenticate(self, ws) -> None:
        try:
            resp = await self._send_raw(ws, "APIStateRequest", {})
        except Exception:
            return
        if not resp or resp.get("data", {}).get("authenticationRequired"):
            try:
                r = await self._send_raw(ws, "AuthenticationTokenRequest",
                                          {"pluginName": "HUDstream",
                                           "pluginDeveloper": "hudstream",
                                           "pluginIcon": ""})
                token = (r or {}).get("data", {}).get("authenticationToken", "")
                if token:
                    self.token = token
                    self._save_token(token)
                    log.info("VTube Studio auth token acquired")
            except Exception as e:
                self._last_error = f"auth: {e}"[:200]
        # Verify with the (possibly new) token
        try:
            await self._send_raw(ws, "APIStateRequest", {})
        except Exception:
            pass

    async def _pump(self, ws) -> None:
        loop = asyncio.get_event_loop()
        while not self._stop.is_set():
            try:
                item = await loop.run_in_executor(None, self._q.get, True, 0.5)
            except Exception:
                continue
            if item.get("type") == "_shutdown":
                return
            try:
                await self._dispatch(ws, item)
            except Exception as e:
                self._last_error = f"dispatch: {e}"[:200]
                return

    async def _dispatch(self, ws, payload: dict) -> None:
        mtype = payload.get("type")
        if mtype == "hotkey":
            await self._send_raw(ws, "HotkeyTriggerRequest",
                                  {"hotkeyID": payload.get("id", "")})
        elif mtype == "expression":
            await self._send_raw(ws, "ExpressionActivationRequest",
                                  {"expressionFile": payload.get("file", ""),
                                   "active": bool(payload.get("active", True))})
        elif mtype == "load_model":
            await self._send_raw(ws, "ModelLoadRequest",
                                  {"modelID": payload.get("id", "")})
        self._last_event_at = time.time()

    async def _send_raw(self, ws, mtype: str, data: dict) -> dict:
        req = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": f"hudstream-{uuid.uuid4()}",
            "messageType": mtype,
            "data": data,
        }
        if self.token and mtype != "AuthenticationTokenRequest":
            req["data"] = {**data, "authenticationToken": self.token}
        await ws.send(json.dumps(req))
        raw = await asyncio.wait_for(ws.recv(), timeout=self.timeout_s)
        return json.loads(raw)
