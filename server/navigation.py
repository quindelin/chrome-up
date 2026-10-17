"""Turn directions (Meta Maps / Google Maps / Apple Maps / OSRM) into a
world-pinned objective marker for the compass.

Three ways to feed it:
  1. `navigation.destination` in config.yaml (lat/lon or a place name)
  2. POST /api/destination  {"link": "<any maps share URL>"} or {"lat":..,"lon":..}
  3. POST /api/route        {"destination": {...}, "steps": [{lat, lon, instruction}]}
     <- paste the steps out of Meta Maps / any maps app

You are located either by `navigation.origin` or by GPS from the /phone page.
"""
from __future__ import annotations

import json
import math
import re
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

EARTH_R = 6371008.8
UA = {"User-Agent": "HUDstream/0.2 (POV stream overlay)"}
COORD_RE = re.compile(r"(-?\d{1,3}\.\d{3,})\s*[,%/ +\s]\s*(-?\d{1,3}\.\d{3,})")


# --------------------------------------------------------------------- geo math
def haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_R * math.asin(min(1.0, math.sqrt(h)))


def initial_bearing(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def parse_coords(text: str) -> Optional[Tuple[float, float]]:
    """Pull lat/lon out of a maps share link (google/maps/apple/meta/osm)."""
    if not text:
        return None
    text = urllib.parse.unquote(text)
    for key in ("daddr=", "saddr=", "destination=", "q=", "ll=", "@"):
        idx = text.find(key)
        if idx >= 0:
            m = COORD_RE.search(text[idx:])
            if m:
                return float(m.group(1)), float(m.group(2))
    m = COORD_RE.search(text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


# --------------------------------------------------------------------- state
@dataclass
class Objective:
    name: str = ""
    bearing: float = 0.0
    distance: float = 0.0
    step: str = ""
    icon: str = "diamond"
    mode: str = "straight"   # straight | route


class Navigation:
    def __init__(self, cfg: dict):
        self.cfg = cfg or {}
        self.enabled = bool(self.cfg.get("enabled"))
        self.provider = str(self.cfg.get("provider", "osrm"))
        self.profile = str(self.cfg.get("profile", "driving"))
        self.refresh_s = float(self.cfg.get("refresh_s", 30))
        self.arrive_m = float(self.cfg.get("arrive_m", 15))

        origin = self.cfg.get("origin") or {}
        self.pos: Optional[Tuple[float, float]] = _pair(origin.get("lat"), origin.get("lon"))
        dest = self.cfg.get("destination") or {}
        self.dest: Optional[Tuple[float, float]] = _pair(dest.get("lat"), dest.get("lon"))
        self.dest_name: str = dest.get("query") or ""
        self.steps: List[Dict[str, Any]] = []
        self.route_distance: float = 0.0
        self.route_duration: float = 0.0
        self.status: str = "idle"

        self._lock = threading.Lock()
        self._last_fetch = 0.0
        self._fetching = False

        if self.dest is None and dest.get("query"):
            self._geocode_async(dest["query"])
        self._maybe_fetch(force=True)

    # ------------------------------------------------------------------ inputs
    def set_position(self, lat: float, lon: float) -> None:
        self.pos = (float(lat), float(lon))
        self._maybe_fetch()

    def set_destination(self, lat: float = None, lon: float = None,
                        query: str = None, name: str = None) -> bool:
        coords = _pair(lat, lon)
        if coords:
            with self._lock:
                self.dest = coords
                self.dest_name = name or f"{coords[0]:.4f}, {coords[1]:.4f}"
                self.steps = []
                self.enabled = True
            self._maybe_fetch(force=True)
            return True
        if query:
            self._geocode_async(query)
            self.enabled = True
            self.dest_name = name or query
            return True
        return False

    def clear(self) -> None:
        with self._lock:
            self.dest = None
            self.steps = []
            self.dest_name = ""
            self.enabled = False
            self.status = "idle"

    def set_route(self, destination: dict = None, steps: List[dict] = None) -> None:
        """Accept pre-computed steps from any maps app (incl. Meta Maps)."""
        with self._lock:
            if destination:
                coords = _pair(destination.get("lat"), destination.get("lon"))
                if coords:
                    self.dest = coords
                self.dest_name = destination.get("name") or self.dest_name
            if steps:
                clean = []
                for s in steps:
                    c = _pair(s.get("lat"), s.get("lon"))
                    if c:
                        clean.append({
                            "lat": c[0], "lon": c[1],
                            "instruction": s.get("instruction", ""),
                            "distance": float(s.get("distance", 0) or 0),
                            "type": s.get("type", ""),
                        })
                self.steps = clean
                self.enabled = True
                self.status = "manual route"
                self.provider = "manual"

    # ------------------------------------------------------------------ fetch
    def _maybe_fetch(self, force: bool = False) -> None:
        if not self.enabled or self.provider != "osrm":
            return
        if self.dest is None or self.pos is None:
            return
        now = _now()
        if not force and (self._fetching or now - self._last_fetch < self.refresh_s):
            return
        self._fetching = True
        self._last_fetch = now
        threading.Thread(target=self._fetch_osrm, daemon=True).start()

    def _fetch_osrm(self) -> None:
        try:
            a, b = self.pos, self.dest
            url = (f"https://router.project-osrm.org/route/v1/{self.profile}/"
                   f"{a[1]},{a[0]};{b[1]},{b[0]}?overview=false&steps=true")
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            routes = data.get("routes") or []
            if not routes:
                self.status = "no route"
                return
            route = routes[0]
            steps = []
            for leg in route.get("legs", []):
                for st in leg.get("steps", []):
                    loc = (st.get("maneuver") or {}).get("location") or [None, None]
                    if loc[0] is None:
                        continue
                    steps.append({
                        "lat": float(loc[1]), "lon": float(loc[0]),
                        "instruction": _instruction(st),
                        "distance": float(st.get("distance", 0)),
                        "type": (st.get("maneuver") or {}).get("type", ""),
                    })
            with self._lock:
                self.steps = steps
                self.route_distance = float(route.get("distance", 0))
                self.route_duration = float(route.get("duration", 0))
                self.status = "route"
        except Exception as exc:
            self.status = f"route unavailable ({exc})"
        finally:
            self._fetching = False

    def _geocode_async(self, query: str) -> None:
        threading.Thread(target=self._geocode, args=(query,), daemon=True).start()

    def _geocode(self, query: str) -> None:
        try:
            url = ("https://nominatim.openstreetmap.org/search?format=json&limit=1&q="
                   + urllib.parse.quote(query))
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if not data:
                self.status = "geocode failed"
                return
            lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
            with self._lock:
                self.dest = (lat, lon)
                self.dest_name = data[0].get("display_name", query)[:48]
                self.enabled = True
            self._maybe_fetch(force=True)
        except Exception as exc:
            self.status = f"geocode failed ({exc})"

    # ------------------------------------------------------------------ tick
    def tick(self) -> Dict[str, Any]:
        if not self.enabled:
            return {"active": False}
        with self._lock:
            pos, dest, steps = self.pos, self.dest, list(self.steps)
        if pos is None:
            return {"active": False, "status": "waiting for GPS", "statusOnly": True}
        if dest is None:
            return {"active": False, "status": self.status or "no destination",
                    "statusOnly": True}

        target = dest
        step_text = ""
        icon = "diamond"
        mode = "straight"
        for st in steps:
            pt = (st["lat"], st["lon"])
            if haversine(pos, pt) > max(20.0, self.arrive_m):
                target = pt
                step_text = st.get("instruction", "")
                mode = "route"
                icon = _icon_for(st.get("type", ""))
                break

        distance = haversine(pos, target)
        bearing = initial_bearing(pos, target)
        arrived = distance <= self.arrive_m

        obj = Objective(
            name=self.dest_name or "Objective",
            bearing=round(bearing, 1),
            distance=round(distance, 1),
            step=step_text,
            icon=icon,
            mode=mode,
        )
        return {
            "active": not arrived,
            "arrived": arrived,
            "objective": asdict(obj),
            "route_distance": round(self.route_distance, 1),
            "route_duration": round(self.route_duration, 1),
            "status": self.status,
        }


def _pair(lat, lon):
    try:
        if lat is None or lon is None:
            return None
        return (float(lat), float(lon))
    except (TypeError, ValueError):
        return None


def _now() -> float:
    import time
    return time.time()


def _instruction(step: dict) -> str:
    man = step.get("maneuver") or {}
    kind = (man.get("type") or "").replace("-", " ")
    mod = man.get("modifier") or ""
    name = step.get("name") or ""
    parts = [p for p in (f"{kind} {mod}".strip(), f"onto {name}" if name else "") if p]
    text = " ".join(parts).strip()
    return text[:1].upper() + text[1:] if text else "Continue"


def _icon_for(kind: str) -> str:
    kind = (kind or "").lower()
    if "arrive" in kind:
        return "home"
    if "turn" in kind or "fork" in kind or "merge" in kind:
        return "diamond"
    if "roundabout" in kind or "rotary" in kind:
        return "diamond"
    return "diamond"
