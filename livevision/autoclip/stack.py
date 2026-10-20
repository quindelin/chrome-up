"""One-call health of the whole streaming box, for the iOS companion app.

GET /api/autoclip/stack answers "am I live?" without the phone having to know
MediaMTX, OBS or the host: the glasses ingest and OBS's program output (from
MediaMTX's local API), the restream targets, the host's load/memory/disk, and
autoclip's own queue. Every probe degrades to `{"ok": false, "error": ...}`;
the endpoint never fails because one part is down.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from .util import expand_env

# last (bytesReceived, time) per path, so a poll can report a bitrate
_last_bytes: Dict[str, tuple] = {}


def _mediamtx_paths(api: str, timeout: float = 2.0) -> Dict[str, dict]:
    with urllib.request.urlopen(f"{api.rstrip('/')}/v3/paths/list", timeout=timeout) as r:
        data = json.load(r)
    return {p.get("name", ""): p for p in data.get("items", [])}


def _path_status(label: str, path: Optional[dict]) -> Dict[str, Any]:
    if not path or not path.get("ready"):
        _last_bytes.pop(label, None)
        return {"live": False}
    now, got = time.time(), int(path.get("bytesReceived") or 0)
    kbps = None
    prev = _last_bytes.get(label)
    if prev and now > prev[1] and got >= prev[0]:
        kbps = round((got - prev[0]) * 8 / 1000 / (now - prev[1]))
    _last_bytes[label] = (got, now)
    since = path.get("readyTime")
    return {"live": True, "since": since, "bitrate_kbps": kbps,
            "tracks": path.get("tracks") or [], "readers": len(path.get("readers") or [])}


def _host(workdir: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {"cpus": os.cpu_count()}
    try:
        out["load"] = [round(x, 2) for x in os.getloadavg()]
    except OSError:
        pass
    try:      # host network + shared kernel: these are the VM's numbers
        mem = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            mem[k] = int(v.split()[0]) * 1024
        out["mem_total"] = mem.get("MemTotal")
        out["mem_available"] = mem.get("MemAvailable")
        out["uptime_seconds"] = round(float(Path("/proc/uptime").read_text().split()[0]))
    except Exception:  # noqa: BLE001 - not Linux (dev laptop)
        pass
    du = shutil.disk_usage(workdir)
    out["disk_total"], out["disk_free"] = du.total, du.free
    return out


def stack_status(cfg: Dict[str, Any], rt) -> Dict[str, Any]:
    scfg = cfg.get("stack", {}) or {}
    out: Dict[str, Any] = {"ts": round(time.time(), 3)}

    api = str(scfg.get("mediamtx_api") or "")
    ingest_path = expand_env(str(scfg.get("ingest_path") or ""))
    program_path = expand_env(str(scfg.get("program_path") or ""))
    if api:
        try:
            paths = _mediamtx_paths(api)
            out["ingest"] = {"ok": True, **_path_status("ingest", paths.get(ingest_path))}
            out["program"] = {"ok": True, **_path_status("program", paths.get(program_path))}
        except Exception as exc:  # noqa: BLE001
            err = {"ok": False, "live": False, "error": f"mediamtx: {exc}"}
            out["ingest"], out["program"] = dict(err), dict(err)
    else:
        out["ingest"] = out["program"] = {"ok": False, "live": False,
                                          "error": "stack.mediamtx_api not set"}

    live = rt.live_status()
    out["restream"] = {
        "enabled": bool(live.get("enabled", True)),
        "active_count": live.get("active_count", 0),
        # never the keys or URLs: only what the phone needs to show and toggle
        "targets": [{k: t.get(k) for k in ("name", "enabled", "key_set", "active",
                                          "uptime_seconds", "last_error")}
                    for t in live.get("targets", [])],
    }

    cycles = rt.state.get("cycles", [])
    last = cycles[-1] if cycles else {}
    out["autoclip"] = {
        "publish_mode": cfg.get("publish", {}).get("mode"),
        "pending": len(rt.pending()),
        "cycles": len(cycles),
        "clips": sum(len(c.get("clips", [])) for c in cycles),
        "last_cycle_ts": last.get("ts"),
        "last_note": (last.get("notes") or [""])[-1],
    }
    try:
        out["host"] = _host(Path(rt.workdir))
    except Exception as exc:  # noqa: BLE001
        out["host"] = {"error": str(exc)}
    return out
