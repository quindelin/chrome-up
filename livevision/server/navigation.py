"""Turn directions (Meta Maps / Google Maps / Apple Maps / OSRM) into a
world-pinned objective marker for the compass.

Three ways to feed it:
  1. `navigation.destination` in config.yaml (lat/lon or a place name)
  2. POST /api/destination  {"link": "<any maps share URL>"} or {"lat":..,"lon":..}
  3. POST /api/route        {"destination": {...}, "steps": [{lat, lon, instruction}]}
     <- paste the steps out of Meta Maps / any maps app
  4. {"route": {...}} on /ws/phone: the LiveVision companion's Apple Maps
     turn-by-turn (MKDirections). While fresh it is the source of truth: the
     phone tracks progress, picks the next maneuver and reroutes; we only
     shape it for the compass. See set_phone_route().

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
    mode: str = "straight"   # straight | route | apple
    maneuver: str = ""       # left | right | straight | uturn | arrive | "" (apple only)


# statuses that say nothing about where you are (others can carry a place
# name or an address from a geocode error)
_SAFE_STATUS = {"idle", "route", "manual route", "no route", "arrived",
                "waiting for GPS", "no destination"}


def stream_safe(state: Dict[str, Any]) -> Dict[str, Any]:
    """The navigation state as the stream may show it: the compass marker's
    direction and the distance to the next turn, nothing that names a place.
    Street names, the step text, the destination and the trip's distance /
    ETA would let viewers work out where you are (and where you're going).
    The glasses lens gets the full route from the phone, not from here."""
    out = {k: state[k] for k in ("active", "arrived", "source", "statusOnly") if k in state}
    obj = state.get("objective")
    if isinstance(obj, dict):
        out["objective"] = {k: obj.get(k) for k in ("bearing", "distance", "icon", "mode", "maneuver")}
        out["objective"].update(name="", step="")
    status = state.get("status")
    if status in _SAFE_STATUS:
        out["status"] = status
    return out


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
        # the phone's Apple Maps route; trusted while younger than phone_fresh_s
        self.phone_route: Optional[Dict[str, Any]] = None
        self.phone_route_ts = 0.0
        self.phone_fresh_s = float(self.cfg.get("phone_fresh_s", 15))

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
            self.phone_route = None

    def set_phone_route(self, route: dict) -> bool:
        """The companion's Apple Maps route progress:
        {"active", "instruction", "step_distance", "maneuver": {lat, lon,
         bearing, type}, "next_instruction", "remaining_m", "eta_s",
         "destination": {name, lat, lon}, "transport", "arrived", "status"}.
        {"active": false} without "arrived" hands back to the server route."""
        if not isinstance(route, dict):
            return False
        if not route.get("active") and not route.get("arrived"):
            with self._lock:
                self.phone_route = None
            return True
        man = route.get("maneuver") if isinstance(route.get("maneuver"), dict) else {}
        target = _pair(man.get("lat"), man.get("lon"))
        if route.get("active") and target is None and _num(man.get("bearing")) is None:
            return False                       # nothing to point the marker at
        dest = route.get("destination") if isinstance(route.get("destination"), dict) else {}
        with self._lock:
            self.phone_route = {
                "active": bool(route.get("active")),
                "arrived": bool(route.get("arrived")),
                "instruction": str(route.get("instruction") or "")[:80],
                "next_instruction": str(route.get("next_instruction") or "")[:80],
                "step_distance": _num(route.get("step_distance")),
                "target": target,
                "bearing": _num(man.get("bearing")),
                "maneuver": str(man.get("type") or ""),
                "remaining": _num(route.get("remaining_m")) or 0.0,
                "eta": _num(route.get("eta_s")) or 0.0,
                "transport": str(route.get("transport") or "walking"),
                "status": str(route.get("status") or ""),
                "dest_name": str(dest.get("name") or "")[:48],
            }
            self.phone_route_ts = _now()
            coords = _pair(dest.get("lat"), dest.get("lon"))
            if coords:
                self.dest = coords
            if dest.get("name"):
                self.dest_name = str(dest["name"])[:48]
            self.enabled = True
        return True

    def phone_fresh(self) -> bool:
        return (self.phone_route is not None
                and _now() - self.phone_route_ts < self.phone_fresh_s)

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
        if not self.enabled or self.provider != "osrm" or self.phone_fresh():
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
        if self.phone_fresh():
            return self._tick_phone()
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


    def _tick_phone(self) -> Dict[str, Any]:
        with self._lock:
            r = dict(self.phone_route or {})
            pos = self.pos
        name = r.get("dest_name") or self.dest_name or "Destination"
        destination = {"name": name, "distance": round(r["remaining"], 1),
                       "eta": round(r["eta"], 1)}
        if r.get("arrived"):
            return {"active": False, "arrived": True, "source": "apple",
                    "objective": asdict(Objective(name=name, mode="apple", icon="home",
                                                  maneuver="arrive")),
                    "destination": destination, "status": "arrived"}
        target = r.get("target")
        distance = r.get("step_distance")
        bearing = r.get("bearing")
        # our own GPS is the phone's too: re-aim between route messages
        if pos is not None and target is not None:
            bearing = initial_bearing(pos, target)
            if distance is None:
                distance = haversine(pos, target)
        obj = Objective(
            name=name,
            bearing=round(bearing or 0.0, 1),
            distance=round(distance or 0.0, 1),
            step=r.get("instruction", ""),
            icon="home" if r.get("maneuver") == "arrive" else "diamond",
            mode="apple",
            maneuver=r.get("maneuver", ""),
        )
        return {
            "active": True,
            "arrived": False,
            "source": "apple",
            "objective": asdict(obj),
            "next": r.get("next_instruction", ""),
            "destination": destination,
            "transport": r.get("transport", "walking"),
            "route_distance": round(r["remaining"], 1),
            "route_duration": round(r["eta"], 1),
            "status": r.get("status") or "apple maps",
        }


def _num(v) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


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
