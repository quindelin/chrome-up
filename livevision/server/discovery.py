"""Discover OSM points of interest around your GPS and fire Skyrim-style
'Discovered: <name>' toasts for new ones.

Public Overpass API, ~1 query per minute, only when you've moved at least
`min_move_m` since the last query. Failures are silent.
"""
from __future__ import annotations

import json
import math
import threading
import time
import urllib.request
from typing import Iterable, Optional, Set, Tuple

from .state import World

UA = {"User-Agent": "HUDstream/0.3 (POV stream overlay)"}
EARTH = 6371008.8


def _moved_enough(a, b, m: float) -> bool:
    if a is None or b is None:
        return True
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH * math.asin(min(1.0, math.sqrt(h))) >= m


class Discovery:
    def __init__(self, cfg: dict):
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.radius_m = float(cfg.get("radius_m", 80))
        self.min_move_m = float(cfg.get("min_move_m", 40))
        self.every_s = float(cfg.get("every_s", 60))
        self.endpoint = str(cfg.get("endpoint", "https://overpass-api.de/api/interpreter"))
        self.status = "idle"
        self._seen: Set[str] = set()
        self._last_query = 0.0
        self._last_pos: Optional[Tuple[float, float]] = None
        self._pending: Iterable[str] = ()
        self._fetching = False
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._seen.clear()

    def tick(self, pos: Optional[Tuple[float, float]], world: World) -> None:
        if not self.enabled or pos is None:
            return
        now = time.time()
        if self._fetching:
            self._drain(world)
            return
        if now - self._last_query < self.every_s and not _moved_enough(self._last_pos, pos, 0):
            return
        if not _moved_enough(self._last_pos, pos, self.min_move_m) and self._last_query:
            return
        self._last_query = now
        self._last_pos = pos
        self._fetching = True
        threading.Thread(target=self._query, args=(pos,), daemon=True).start()

    def _drain(self, world: World) -> None:
        with self._lock:
            if not self._pending:
                return
            for name in list(self._pending):
                if name not in self._seen:
                    self._seen.add(name)
                    world.events.append({
                        "type": "discovery",
                        "text": f"Discovered: {name}",
                        "place": name,
                    })
            self._pending = ()

    def _query(self, pos) -> None:
        try:
            radius = int(max(15, self.radius_m))
            body = (
                f'[out:json][timeout:5];'
                f'(node(around:{radius},{pos[0]},{pos[1]});'
                f'way(around:{radius},{pos[0]},{pos[1]}););'
                f'out tags 30;'
            )
            req = urllib.request.Request(self.endpoint, data=body.encode("utf-8"),
                                         headers={**UA, "Content-Type": "text/plain"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            names = []
            for el in (data.get("elements") or []):
                tags = el.get("tags") or {}
                name = tags.get("name") or tags.get("name:en")
                if not name:
                    continue
                if not any(k in tags for k in (
                        "amenity", "shop", "tourism", "historic", "leisure",
                        "public_transport", "railway", "aeroway", "place", "building")):
                    continue
                if len(name) > 60:
                    continue
                names.append(name)
            with self._lock:
                self._pending = names
            self.status = f"found {len(names)} nearby"
        except Exception as exc:
            self.status = f"offline ({type(exc).__name__})"
        finally:
            self._fetching = False
