"""Meta Ray-Ban Display bridge helpers.

Until Meta's Wearables Device Access Toolkit exposes a live POV stream and raw
IMU, the practical route is through the paired phone:

  * POV video   -> phone camera app publishing RTSP, set as `video.source`
  * heading     -> /phone page (DeviceOrientation) -> WebSocket to this box
  * mic         -> the glasses' own mic, or the phone, set as `audio.device`
"""
from __future__ import annotations

import socket


def lan_ip() -> str:
    """Best-effort LAN address, used to print the phone bridge URL."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        sock.close()
