"""obs-websocket v5 client (no hard dependency: degrades to 'unavailable').

Used for three things:
  1. SaveReplayBuffer  -> instantly get the last N seconds as one file (OBS-native)
  2. GetStreamStatus / GetRecordStatus -> know whether OBS is actually producing content
  3. Scene + scene-switch events -> cheap, high-signal context for the agent

Requires `pip install websocket-client` and OBS -> Tools -> obs-websocket Settings
(enable WebSocket server). If either is missing, every call returns None/False and
the pipeline falls back to watch_dir / stream_url.
"""
from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
from typing import Any, Dict, List, Optional

try:
    import websocket  # websocket-client
except Exception:  # pragma: no cover - optional dependency
    websocket = None


class OBSError(RuntimeError):
    pass


class OBSClient:
    """Thread-safe, on-demand obs-websocket v5 request/response client."""

    OP_HELLO = 0
    OP_IDENTIFY = 1
    OP_IDENTIFIED = 2
    OP_REQUEST = 6
    OP_REQUEST_RESPONSE = 7

    def __init__(self, cfg: dict):
        self.enabled = bool(cfg.get("enabled", True)) and websocket is not None
        self.host = cfg.get("host", "127.0.0.1")
        self.port = int(cfg.get("port", 4455))
        self.password = cfg.get("password") or ""
        self.timeout = float(cfg.get("timeout", 4.0))
        self.auto_start_replay = bool(cfg.get("auto_start_replay_buffer", True))

        self._ws = None
        self._lock = threading.RLock()
        self._rpc_version = 1
        self._counter = 0
        self._last_error: Optional[str] = None
        self._identified = False
        self._broken_until = 0.0

    # ------------------------------------------------------------------ lifecycle
    @property
    def available(self) -> bool:
        return self.enabled and self._identified

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def _url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    def connect(self, force: bool = False) -> bool:
        if not self.enabled:
            self._last_error = "obs disabled or websocket-client not installed"
            return False
        with self._lock:
            if self._identified and not force:
                return True
            if time.time() < self._broken_until and not force:
                return False
            try:
                self._ws = websocket.create_connection(self._url(), timeout=self.timeout)
                hello = json.loads(self._ws.recv())
                if hello.get("op") != self.OP_HELLO:
                    raise OBSError(f"unexpected hello: {hello.get('op')}")
                d = hello.get("d", {}) or {}
                self._rpc_version = min(int(d.get("rpcVersion", 1)), 1)

                identify: Dict[str, Any] = {
                    "op": self.OP_IDENTIFY,
                    "d": {"rpcVersion": self._rpc_version, "eventSubscriptions": 0},
                }
                auth = d.get("authentication")
                if auth:
                    if not self.password:
                        raise OBSError("OBS requires a websocket password; set obs.password")
                    identify["d"]["authentication"] = self._auth_secret(
                        self.password, auth["salt"], auth["challenge"]
                    )
                self._ws.send(json.dumps(identify))

                while True:
                    msg = json.loads(self._ws.recv())
                    if msg.get("op") == self.OP_IDENTIFIED:
                        self._identified = True
                        self._last_error = None
                        return True
                    if msg.get("op") == 9:  # RequestResponse to Identify = auth failure
                        raise OBSError(msg.get("d", {}).get("requestStatus", {}).get("comment",
                                                                                     "auth failed"))
            except Exception as exc:  # noqa: BLE001
                self._last_error = str(exc)
                self._identified = False
                self._broken_until = time.time() + 5.0
                try:
                    if self._ws:
                        self._ws.close()
                except Exception:
                    pass
                self._ws = None
                return False

    @staticmethod
    def _auth_secret(password: str, salt: str, challenge: str) -> str:
        def sha256_b64(raw: str) -> str:
            return base64.b64encode(hashlib.sha256(raw.encode("utf-8")).digest()).decode()

        return sha256_b64(sha256_b64(password + salt) + challenge)

    def close(self) -> None:
        with self._lock:
            self._identified = False
            try:
                if self._ws:
                    self._ws.close()
            except Exception:
                pass
            self._ws = None

    def request(self, request_type: str, data: dict | None = None,
                retry: bool = True) -> Optional[dict]:
        """Send a request, return its responseData ({} on success) or None on failure."""
        if not self.connect():
            return None
        with self._lock:
            try:
                self._counter += 1
                rid = f"ac{self._counter}"
                self._ws.send(json.dumps({
                    "op": self.OP_REQUEST,
                    "d": {"requestType": request_type, "requestId": rid,
                          "requestData": data or {}},
                }))
                deadline = time.time() + max(2.0, self.timeout)
                while time.time() < deadline:
                    msg = json.loads(self._ws.recv())
                    if msg.get("op") != self.OP_REQUEST_RESPONSE:
                        continue
                    dd = msg.get("d", {}) or {}
                    if dd.get("requestId") != rid:
                        continue
                    status = dd.get("requestStatus", {}) or {}
                    if not status.get("result"):
                        self._last_error = status.get("comment", f"{request_type} failed")
                        return None
                    return dd.get("responseData") or {}
            except Exception as exc:  # noqa: BLE001
                self._last_error = str(exc)
                self.close()
                if retry:
                    return self.request(request_type, data, retry=False)
        return None

    # ------------------------------------------------------------------ capability probes
    def get_version(self) -> Optional[dict]:
        return self.request("GetVersion")

    def get_stream_status(self) -> Optional[dict]:
        """{'outputActive': bool, 'outputReconnecting':..., 'outputDuration': ms, ...}"""
        return self.request("GetStreamStatus")

    def get_record_status(self) -> Optional[dict]:
        return self.request("GetRecordStatus")

    def get_replay_buffer_status(self) -> Optional[dict]:
        return self.request("GetReplayBufferStatus")

    def get_current_scene(self) -> Optional[str]:
        d = self.request("GetCurrentProgramScene")
        return (d or {}).get("currentProgramSceneName")

    # ------------------------------------------------------------------ scenes
    def get_scene_list(self) -> dict:
        """{'currentProgramSceneName': str, 'scenes': [{'sceneName', 'sceneIndex'}]}"""
        return self.request("GetSceneList") or {}

    def scene_names(self) -> List[str]:
        d = self.get_scene_list()
        return [str(s.get("sceneName")) for s in (d.get("scenes") or [])
                if s.get("sceneName")]

    def set_current_scene(self, name: str) -> bool:
        return self.request("SetCurrentProgramScene", {"sceneName": name}) is not None

    def get_scene_item_list(self, scene: str) -> List[dict]:
        d = self.request("GetSceneItemList", {"sceneName": scene})
        return list((d or {}).get("sceneItems") or [])

    def get_scene_item_id(self, scene: str, source_name: str) -> Optional[int]:
        d = self.request("GetSceneItemId",
                         {"sceneName": scene, "sourceName": source_name})
        v = (d or {}).get("sceneItemId")
        return int(v) if v is not None else None

    def set_scene_item_enabled(self, scene: str, item_id: int,
                               enabled: bool) -> bool:
        return self.request("SetSceneItemEnabled", {
            "sceneName": scene, "sceneItemId": int(item_id),
            "sceneItemEnabled": bool(enabled)}) is not None

    # ------------------------------------------------------------------ inputs
    def get_input_list(self) -> List[dict]:
        """[{'inputName', 'inputKind', 'inputKindCaps'}] — kinds tell us what
        an input can do (text vs media vs browser vs audio)."""
        return list((self.request("GetInputList") or {}).get("inputs") or [])

    def get_input_kind(self, name: str) -> Optional[str]:
        d = self.request("GetInputSettings", {"inputName": name})
        return (d or {}).get("inputKind")

    def set_input_settings(self, name: str, settings: dict,
                           overlay: bool = True) -> bool:
        return self.request("SetInputSettings",
                            {"inputName": name, "inputSettings": settings,
                             "overlay": bool(overlay)}) is not None

    def set_text(self, name: str, text: str) -> bool:
        """Set a Text (GDI+/FreeType) source's content."""
        return self.set_input_settings(name, {"text": text})

    def get_input_mute(self, name: str) -> Optional[bool]:
        d = self.request("GetInputMute", {"inputName": name})
        v = (d or {}).get("inputMuted")
        return bool(v) if v is not None else None

    def set_input_mute(self, name: str, muted: bool) -> bool:
        return self.request("SetInputMute",
                            {"inputName": name, "inputMuted": bool(muted)}) is not None

    def get_input_volume(self, name: str) -> Optional[float]:
        """Returns 0..1 multiplier (OBS also reports dB; mul is easier to use)."""
        d = self.request("GetInputVolume", {"inputName": name})
        v = (d or {}).get("inputVolumeMul")
        return float(v) if v is not None else None

    def set_input_volume(self, name: str, mul: float) -> bool:
        return self.request("SetInputVolume",
                            {"inputName": name, "inputVolumeMul": float(mul)}) is not None

    def trigger_media_action(self, name: str, action: str = "restart") -> bool:
        """Restart / pause / play a Media Source or VLC source."""
        actions = {
            "play": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PLAY",
            "pause": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PAUSE",
            "stop": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP",
            "restart": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART",
            "next": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_NEXT",
            "previous": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_PREVIOUS",
        }
        key = actions.get(action.lower(), actions["restart"])
        return self.request("TriggerMediaInputAction",
                            {"inputName": name, "mediaAction": key}) is not None

    def refresh_browser_source(self, name: str) -> bool:
        return self.request("PressInputPropertiesButton", {
            "inputName": name, "propertyName": "refreshnocache"}) is not None

    # ------------------------------------------------------------------ outputs
    def start_record(self) -> bool:
        return self.request("StartRecord") is not None

    def stop_record(self) -> bool:
        return self.request("StopRecord") is not None

    def toggle_record(self) -> Optional[bool]:
        d = self.request("ToggleRecord")
        return (d or {}).get("outputActive")

    def start_stream(self) -> bool:
        return self.request("StartStream") is not None

    def stop_stream(self) -> bool:
        return self.request("StopStream") is not None

    def toggle_stream(self) -> Optional[bool]:
        d = self.request("ToggleStream")
        return (d or {}).get("outputActive")

    def start_virtualcam(self) -> bool:
        return self.request("StartVirtualCam") is not None

    def stop_virtualcam(self) -> bool:
        return self.request("StopVirtualCam") is not None

    def get_virtualcam_status(self) -> Optional[bool]:
        d = self.request("GetVirtualCamStatus")
        v = (d or {}).get("outputActive")
        return bool(v) if v is not None else None

    # ------------------------------------------------------------------ transitions
    def get_current_transition(self) -> Optional[str]:
        d = self.request("GetCurrentSceneTransition")
        return (d or {}).get("transitionName")

    def set_current_transition(self, name: str) -> bool:
        return self.request("SetCurrentSceneTransition",
                            {"transitionName": name}) is not None

    def trigger_transition(self) -> bool:
        """Studio-mode only: cut/fade to preview. No-op without studio mode."""
        return self.request("TriggerStudioModeTransition") is not None

    def is_streaming(self) -> bool:
        st = self.get_stream_status() or {}
        return bool(st.get("outputActive"))

    def is_recording(self) -> bool:
        st = self.get_record_status() or {}
        return bool(st.get("outputActive"))

    # ------------------------------------------------------------------ replay buffer
    def ensure_replay_buffer(self) -> bool:
        """Start the replay buffer if OBS is idle and auto_start is enabled."""
        if not self.auto_start_replay:
            return False
        st = self.get_replay_buffer_status()
        if st is None:
            return False
        if st.get("outputActive"):
            return True
        return self.request("StartReplayBuffer") is not None

    def save_replay_buffer(self) -> bool:
        return self.request("SaveReplayBuffer") is not None

    def trigger_replay(self) -> bool:
        """Ensure the buffer is running, then save it. Returns True if a save was issued."""
        if not self.connect():
            return False
        self.ensure_replay_buffer()
        return self.save_replay_buffer()


def describe(cfg: dict) -> dict:
    """Diagnostics blob used by /api/autoclip/status and the MCP `status` tool."""
    client = OBSClient(cfg)
    ok = client.connect()
    info = {
        "enabled": client.enabled,
        "connected": ok,
        "url": client._url(),
        "error": client.last_error,
    }
    if ok:
        info["version"] = (client.get_version() or {}).get("obsVersion")
        info["streaming"] = client.is_streaming()
        info["recording"] = client.is_recording()
        info["replay_active"] = bool((client.get_replay_buffer_status() or {}).get("outputActive"))
        info["scene"] = client.get_current_scene()
        info["scenes"] = client.scene_names()
        try:
            info["virtualcam"] = client.get_virtualcam_status()
        except Exception:
            info["virtualcam"] = None
    client.close()
    return info
