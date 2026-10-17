"""Compass / heading hub.

Every transport writes into the same hub, so you can mix them:

  phone  - the paired phone opens /phone and streams DeviceOrientation heading
           over websockets (the practical route for Meta Ray-Ban Display today)
  udp    - HyperIMU / Sensor Stream IMU+ / any app pushing JSON or CSV
  ble    - BLE IMU beacon speaking Nordic UART (needs `pip install bleak`)
  serial - USB/serial IMU pushing JSON or CSV lines (needs `pip install pyserial`)
  sim    - slow drift, useful for layout work without hardware
"""
from __future__ import annotations

import json
import re
import socket
import threading
import time

from .state import HeadingSnapshot

HEADING_KEYS = ("heading", "azimuth", "yaw", "compass", "bearing", "angle", "orientation")
FRESH_S = 5.0


def _shortest_delta(a: float, b: float) -> float:
    """Signed delta from a to b on a 360 degree circle."""
    return (b - a + 180.0) % 360.0 - 180.0


class HeadingHub:
    def __init__(self, cfg: dict):
        self.mode = str(cfg.get("mode", "auto")).lower()
        self.port = int(cfg.get("udp_port", 5555))
        self.udp_format = str(cfg.get("udp_format", "auto")).lower()
        self.udp_index = int(cfg.get("udp_heading_index", 0))
        self.offset = float(cfg.get("offset", 0.0))
        self.smoothing = float(cfg.get("smoothing", 0.15))
        self.ble_cfg = cfg.get("ble") or {}
        self.serial_cfg = cfg.get("serial") or {}

        self._lock = threading.Lock()
        self._values = {"phone": None, "udp": None, "ble": None, "serial": None}
        self._times = {"phone": 0.0, "udp": 0.0, "ble": 0.0, "serial": 0.0}
        self._accuracy = 0.0
        self._sim_deg = 0.0
        self._cur = 0.0
        self._running = False
        self._sock = None
        self._threads = []
        self.ble_status = "off"
        self.serial_status = "off"

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> None:
        self._running = True
        if self.mode in ("udp", "auto"):
            self._spawn(self._udp_loop, "heading-udp")
        if self.serial_cfg.get("enabled") and self.serial_cfg.get("port"):
            self._spawn(self._serial_loop, "heading-serial")

    def _spawn(self, fn, name: str) -> None:
        th = threading.Thread(target=fn, name=name, daemon=True)
        th.start()
        self._threads.append(th)

    async def start_ble(self) -> None:
        """BLE notify loop (async, driven by the server's event loop)."""
        if not self.ble_cfg.get("enabled"):
            return
        try:
            from bleak import BleakClient, BleakScanner
        except Exception as exc:
            self.ble_status = f"unavailable ({exc})"
            print(f"[heading] ble disabled: {exc}  (pip install bleak)")
            return

        def handler(_sender, data: bytes):
            deg = self._parse(data.decode("utf-8", "ignore"))
            if deg is not None:
                self._set("ble", deg)

        while self._running:
            try:
                address = self.ble_cfg.get("address")
                if not address:
                    self.ble_status = "scanning…"
                    hint = (self.ble_cfg.get("name_hint") or "").lower()
                    devices = await BleakScanner.discover(timeout=6.0)
                    for d in devices:
                        if hint and hint in (d.name or "").lower():
                            address = d.address
                            break
                    if not address and devices:
                        address = devices[0].address
                if not address:
                    self.ble_status = "no device found"
                    await _async_sleep(5)
                    continue

                self.ble_status = f"connecting {address}"
                async with BleakClient(address) as client:
                    self.ble_status = f"connected {address}"
                    await client.start_notify(self.ble_cfg.get("char_uuid"), handler)
                    while self._running and client.is_connected:
                        await _async_sleep(1.0)
                    self.ble_status = "disconnected"
            except Exception as exc:
                self.ble_status = f"error ({exc})"
                await _async_sleep(5.0)

    def stop(self) -> None:
        self._running = False
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ inputs
    def set_phone(self, deg: float, accuracy: float = 0.0) -> None:
        self._accuracy = float(accuracy or 0.0)
        self._set("phone", deg)

    def _set(self, name: str, deg: float) -> None:
        with self._lock:
            self._values[name] = float(deg) % 360.0
            self._times[name] = time.time()

    # ------------------------------------------------------------------ udp
    def _udp_loop(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(("0.0.0.0", self.port))
            self._sock.settimeout(0.5)
            print(f"[heading] listening for UDP sensor packets on :{self.port}")
        except Exception as exc:
            print(f"[heading] udp unavailable ({exc})")
            return
        while self._running:
            try:
                data, _addr = self._sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            deg = self._parse(data.decode("utf-8", "ignore"))
            if deg is not None:
                self._set("udp", deg)

    # ------------------------------------------------------------------ serial
    def _serial_loop(self):
        try:
            import serial  # type: ignore
        except Exception as exc:
            self.serial_status = f"unavailable ({exc})"
            print(f"[heading] serial disabled: {exc}  (pip install pyserial)")
            return
        port = self.serial_cfg.get("port")
        while self._running:
            try:
                with serial.Serial(port, int(self.serial_cfg.get("baud", 115200)),
                                   timeout=1) as ser:
                    self.serial_status = f"connected {port}"
                    while self._running:
                        line = ser.readline()
                        if not line:
                            continue
                        deg = self._parse(line.decode("utf-8", "ignore"))
                        if deg is not None:
                            self._set("serial", deg)
            except Exception as exc:
                self.serial_status = f"error ({exc})"
                time.sleep(3.0)

    # ------------------------------------------------------------------ parsing
    def _parse(self, text: str):
        text = text.strip()
        if not text:
            return None
        if self.udp_format in ("auto", "json") and text.startswith("{"):
            try:
                data = json.loads(text)
            except Exception:
                data = None
            if isinstance(data, dict):
                for key in HEADING_KEYS:
                    if key in data:
                        try:
                            return float(data[key])
                        except (TypeError, ValueError):
                            return None
                if isinstance(data.get("values"), list):
                    nums = [v for v in data["values"] if isinstance(v, (int, float))]
                    if len(nums) > self.udp_index:
                        return float(nums[self.udp_index])
            return None
        nums = []
        for part in re.split(r"[,;\t ]+", text):
            try:
                nums.append(float(part))
            except ValueError:
                continue
        if len(nums) > self.udp_index:
            return nums[self.udp_index]
        return None

    # ------------------------------------------------------------------ tick
    def tick(self, dt: float) -> HeadingSnapshot:
        now = time.time()
        with self._lock:
            if self.mode in ("phone", "udp", "ble", "serial"):
                raw = self._values.get(self.mode)
                source = self.mode if raw is not None else "sim"
            else:  # auto -> newest live source
                raw, source = None, "sim"
                best = 0.0
                for name in ("phone", "udp", "ble", "serial"):
                    if self._values[name] is not None and self._times[name] > best:
                        best, raw, source = self._times[name], self._values[name], name
                if raw is None or now - best > FRESH_S:
                    raw, source = None, "sim"
            if raw is None:
                self._sim_deg = (self._sim_deg + dt * 9.0) % 360.0
                raw = self._sim_deg
            acc = self._accuracy if source == "phone" else 0.0
            raw = float(raw)

        target = (raw + self.offset) % 360.0
        self._cur = (self._cur + _shortest_delta(self._cur, target) *
                     max(0.02, min(1.0, self.smoothing))) % 360.0
        return HeadingSnapshot(deg=round(self._cur, 1), source=source,
                               accuracy=round(acc, 1), raw=round(raw, 1))

    def status(self) -> dict:
        now = time.time()
        with self._lock:
            live = {
                name: round(now - self._times[name], 1)
                for name, t in self._times.items() if self._values[name] is not None
            }
        return {"mode": self.mode, "live": live, "ble": self.ble_status,
                "serial": self.serial_status}


async def _async_sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
