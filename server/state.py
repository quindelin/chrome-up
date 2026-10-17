"""Shared world state snapshots passed between analyzers, engine and overlay."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class AudioSnapshot:
    level: float = 0.0
    speaking: bool = False
    talk_ratio: float = 0.0
    bands: List[float] = field(default_factory=list)
    viseme: str = "closed"
    openness: float = 0.0
    width: float = 0.5
    source: str = "sim"
    onset: bool = False        # a sharp loud transient since the last tick (for shouts)


@dataclass
class VisionSnapshot:
    motion: float = 0.0
    people: int = 0
    faces: int = 0
    brightness: float = 0.5
    running: bool = False
    moving: bool = False
    fps: float = 0.0
    source: str = "sim"
    # what the wearer appears to be doing: idle | walking | running | boxing | lifting
    activity: str = "idle"
    cadence: float = 0.0
    attributes: Dict[str, int] = field(default_factory=dict)
    text_rows: int = 0       # number of text-like rows detected in the frame
    focus: str = ""          # reading | coding | ""


@dataclass
class DesktopSnapshot:
    app: str = ""
    title: str = ""
    kind: str = "other"      # coding | reading | other
    source: str = "none"     # osascript | xdotool | agent | none


@dataclass
class HeadingSnapshot:
    deg: float = 0.0
    source: str = "sim"
    accuracy: float = 0.0
    raw: float = 0.0


@dataclass
class Vitals:
    health: float = 100.0
    magicka: float = 100.0
    stamina: float = 100.0


@dataclass
class World:
    audio: AudioSnapshot = field(default_factory=AudioSnapshot)
    vision: VisionSnapshot = field(default_factory=VisionSnapshot)
    heading: HeadingSnapshot = field(default_factory=HeadingSnapshot)
    desktop: DesktopSnapshot = field(default_factory=DesktopSnapshot)
    vitals: Vitals = field(default_factory=Vitals)
    imu: Dict[str, object] = field(default_factory=dict)
    skills: Dict[str, dict] = field(default_factory=dict)
    player_level: int = 1
    shout: Dict[str, object] = field(default_factory=dict)
    events: List[dict] = field(default_factory=list)
    started: float = 0.0

    def drain_events(self) -> List[dict]:
        out, self.events = self.events, []
        return out
