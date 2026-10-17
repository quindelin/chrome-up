"""Skyrim-style skill engine: rules watch the mic + POV video and award XP."""
from __future__ import annotations

import time
from typing import Dict

from .state import AudioSnapshot, HeadingSnapshot, VisionSnapshot, World

# config rule key -> display name shown in the HUD
SKILL_NAMES = {
    "speech": "Speech",
    "speechcraft": "Speechcraft",
    "rizz": "Rizz",
    "agility": "Agility",
    "sneak": "Sneak",
    "exploration": "Exploration",
    "bard": "Bard",
    "strength": "Strength",
    "combat": "Combat",
    "intelligence": "Intelligence",
    "enchanting": "Enchanting",
}

SECTORS = 16
SECTOR_COOLDOWN = 45.0


class SkillEngine:
    def __init__(self, cfg: dict):
        self.enabled = bool(cfg.get("enabled", True))
        self.xp_per_level = float(cfg.get("xp_per_level", 100))
        self.rules = {k: dict(v) for k, v in (cfg.get("rules") or {}).items()}
        self.vitals_cfg = cfg.get("vitals") or {}
        self.rizz_cfg = cfg.get("rizz") or {}
        self.skills: Dict[str, dict] = {
            key: {"xp": 0.0, "level": 1, "total": 0.0, "active": False, "flash": 0.0}
            for key in SKILL_NAMES
        }
        self.player_level = 1
        self._sector_seen: Dict[int, float] = {}

    # ------------------------------------------------------------------ xp
    def _award(self, key: str, amount: float, world: World) -> None:
        s = self.skills[key]
        s["xp"] += amount
        s["total"] += amount
        s["flash"] = min(1.0, s["flash"] + amount / max(1.0, self.xp_per_level * 0.15))
        while s["xp"] >= self.xp_per_level:
            s["xp"] -= self.xp_per_level
            s["level"] += 1
            world.events.append({
                "type": "skill_level",
                "skill": SKILL_NAMES[key],
                "level": s["level"],
                "text": f"{SKILL_NAMES[key]} increased to {s['level']}",
            })

    # ------------------------------------------------------------------ tick
    def update(self, dt: float, world: World) -> None:
        audio: AudioSnapshot = world.audio
        vision: VisionSnapshot = world.vision
        heading: HeadingSnapshot = world.heading
        for s in self.skills.values():
            s["flash"] = max(0.0, s["flash"] - dt * 1.2)

        if not self.enabled:
            self._update_vitals(dt, world)
            return

        audience = max(vision.people, vision.faces)
        loud = audio.level
        speaking = audio.speaking
        activity = getattr(vision, "activity", "idle") or "idle"
        active = {k: False for k in SKILL_NAMES}

        # --- talking at all
        if speaking:
            active["speech"] = True
            self._award("speech", self._rate("speech") * (0.5 + 0.9 * loud) * dt, world)

        # --- talking to a crowd (3+ people in frame)
        if speaking and audience >= 3:
            active["speechcraft"] = True
            self._award("speechcraft", self._rate("speechcraft") * dt, world)

        # --- rizz: 1-on-1 conversation, or gender-keyed if you opted in
        if speaking and not vision.running and self._rizz_match(vision, audience):
            active["rizz"] = True
            self._award("rizz", self._rate("rizz") * dt, world)

        # --- running / heavy motion
        if vision.running or activity == "running":
            active["agility"] = True
            self._award("agility", self._rate("agility") * (0.5 + vision.motion) * dt, world)

        # --- slow deliberate movement
        if not vision.running and 0.03 < vision.motion < 0.16:
            active["sneak"] = True
            self._award("sneak", self._rate("sneak") * dt, world)

        # --- new compass sector surveyed
        sector = int(heading.deg // (360.0 / SECTORS)) % SECTORS
        now = time.time()
        last = self._sector_seen.get(sector, 0.0)
        if now - last > SECTOR_COOLDOWN:
            self._sector_seen[sector] = now
            active["exploration"] = True
            self._award("exploration", self._rate("exploration"), world)

        # --- big expressive performance voice
        if speaking and loud > 0.55 and audio.talk_ratio > 0.45:
            active["bard"] = True
            self._award("bard", self._rate("bard") * dt, world)

        # --- weight lifting (slow, heavy, repetitive reps)
        if activity == "lifting":
            active["strength"] = True
            self._award("strength", self._rate("strength") * (0.5 + vision.motion) * dt, world)

        # --- boxing / sparring (fast repetitive bursts)
        if activity == "boxing":
            active["combat"] = True
            self._award("combat", self._rate("combat") * (0.5 + vision.motion) * dt, world)

        # --- reading (Intelligence) and coding (Enchanting) when a focus was
        # detected, either by the desktop module or by on-screen text rows
        focus = getattr(vision, "focus", "") or ""
        if focus == "reading":
            active["intelligence"] = True
            self._award("intelligence", self._rate("intelligence") * dt, world)
        elif focus == "coding":
            active["enchanting"] = True
            self._award("enchanting", self._rate("enchanting") * dt, world)

        for key, flag in active.items():
            self.skills[key]["active"] = flag

        self._update_vitals(dt, world)
        self._update_player_level(world)

    def _rizz_match(self, vision: VisionSnapshot, audience: int) -> bool:
        mode = str(self.rizz_cfg.get("mode", "conversation")).lower()
        if mode != "gender":
            return audience == 1
        attrs = getattr(vision, "attributes", {}) or {}
        if not attrs:
            return False                      # opt-in module not running
        target = str(self.rizz_cfg.get("target", "female")).lower()
        if attrs.get(target, 0) < 1:
            return False
        return audience <= 2                  # you + one other person

    def _rate(self, key: str) -> float:
        return float(self.rules.get(key, {}).get("rate", 10))

    def _update_player_level(self, world: World) -> None:
        gained = sum(s["level"] - 1 for s in self.skills.values())
        level = 1 + gained // 10
        if level > self.player_level:
            self.player_level = level
            world.events.append({
                "type": "level",
                "level": level,
                "text": f"You are now level {level}",
            })
        world.player_level = self.player_level

    def _update_vitals(self, dt: float, world: World) -> None:
        v = world.vitals
        c = self.vitals_cfg
        vision: VisionSnapshot = world.vision
        audio: AudioSnapshot = world.audio
        activity = getattr(vision, "activity", "idle") or "idle"

        exerting = vision.running or activity in ("running", "boxing", "lifting")
        if exerting:
            mult = {"boxing": 0.8, "lifting": 1.0, "running": 1.0}.get(activity, 1.0)
            v.stamina -= float(c.get("stamina_drain", 6.0)) * (0.5 + vision.motion) * mult * dt
        else:
            v.stamina += float(c.get("stamina_regen", 3.5)) * dt

        if audio.speaking:
            v.magicka -= float(c.get("magicka_drain", 4.5)) * (0.5 + audio.level) * dt
        else:
            v.magicka += float(c.get("magicka_regen", 3.0)) * dt

        if activity == "boxing":
            v.health -= float(c.get("health_drain", 1.2)) * 1.5 * dt   # sparring bumps
        elif vision.moving and v.stamina < 8.0:
            v.health -= float(c.get("health_drain", 1.2)) * dt
        elif not vision.moving and v.stamina > 40.0:
            v.health += float(c.get("health_regen", 2.0)) * dt

        v.health = max(0.0, min(100.0, v.health))
        v.magicka = max(0.0, min(100.0, v.magicka))
        v.stamina = max(0.0, min(100.0, v.stamina))

    # ------------------------------------------------------------------ output
    def to_dict(self) -> Dict[str, dict]:
        return {
            key: {
                "name": SKILL_NAMES[key],
                "level": int(s["level"]),
                "xp": round(s["xp"] / self.xp_per_level, 3),
                "total": int(s["total"]),
                "active": bool(s["active"]),
                "flash": round(s["flash"], 2),
            }
            for key, s in self.skills.items()
        }

    # ------------------------------------------------------------------ persistence
    def load_state(self, data: dict) -> None:
        if not isinstance(data, dict):
            return
        try:
            self.player_level = max(1, int(data.get("player_level", 1)))
        except (TypeError, ValueError):
            self.player_level = 1
        for key, rec in (data.get("skills") or {}).items():
            if key not in self.skills or not isinstance(rec, dict):
                continue
            try:
                level = max(1, int(rec.get("level", 1)))
                xp = float(rec.get("xp", 0.0))
                total = float(rec.get("total", 0.0))
            except (TypeError, ValueError):
                continue
            xp = max(0.0, min(self.xp_per_level - 0.001, xp))
            self.skills[key]["level"] = level
            self.skills[key]["xp"] = xp
            self.skills[key]["total"] = total

    def export(self) -> dict:
        return {
            "player_level": self.player_level,
            "skills": {
                key: {
                    "level": int(s["level"]),
                    "xp": round(s["xp"], 3),
                    "total": round(s["total"], 3),
                }
                for key, s in self.skills.items()
            },
        }
