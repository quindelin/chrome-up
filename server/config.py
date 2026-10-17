"""Config loading with deep-merged defaults."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULTS: Dict[str, Any] = {
    "server": {"host": "0.0.0.0", "port": 8787, "tick_hz": 20},
    "audio": {
        "enabled": True,
        "device": None,
        "sample_rate": 16000,
        "gain": 1.8,
        "gate": 0.015,
        "bars": 12,
    },
    "video": {
        "enabled": True,
        "source": 0,
        "width": 640,
        "height": 360,
        "fps": 15,
        "people_detect": True,
        "motion_threshold": 0.35,
        "activity": True,
    },
    "heading": {
        "mode": "auto",
        "udp_port": 5555,
        "udp_format": "auto",          # auto | json | csv
        "udp_heading_index": 0,
        "offset": 0,
        "smoothing": 0.15,
        "ble": {
            "enabled": False,
            "address": None,
            "name_hint": None,
            "service_uuid": "6e400001-b5a3-f393-e0a9-e50e24dcca9e",
            "char_uuid": "6e400003-b5a3-f393-e0a9-e50e24dcca9e",
        },
        "serial": {"enabled": False, "port": None, "baud": 115200},
    },
    "gestures": {
        "enabled": True,
        "repeat_ms": 220,
        "mapping": {
            "tap": "toggle_menu",
            "pinch": "toggle_menu",
            "double_tap": "toggle_menu",
            "swipe_left": "prev_tab",
            "swipe_right": "next_tab",
            "swipe_up": "scroll_up",
            "swipe_down": "scroll_down",
            "rotate_cw": "scroll_down",
            "rotate_ccw": "scroll_up",
            "spread": "close_menu",
        },
    },
    "navigation": {
        "enabled": False,
        "origin": {"lat": None, "lon": None},
        "destination": {"lat": None, "lon": None, "query": None},
        "provider": "osrm",
        "profile": "driving",
        "refresh_s": 30,
        "arrive_m": 15,
    },
    "attributes": {
        "enabled": False,
        "backend": None,
        "model": None,
        "labels": ["female", "male"],
        "input_size": 224,
        "every_s": 1.0,
    },
    "markers": [],
    "skills": {
        "enabled": True,
        "xp_per_level": 100,
        "rizz": {"mode": "conversation", "target": "female"},
        "rules": {
            "speech": {"rate": 12},
            "speechcraft": {"rate": 26},
            "rizz": {"rate": 22},
            "agility": {"rate": 18},
            "sneak": {"rate": 10},
            "exploration": {"rate": 30, "per_sector": True},
            "bard": {"rate": 16},
            "strength": {"rate": 20},
            "combat": {"rate": 24},
            "intelligence": {"rate": 14},
            "enchanting": {"rate": 20},
        },
    },
    "focus": {
        "enabled": True,
        "min_text_rows": 6,
        "dark_brightness": 95,
        "bright_brightness": 145,
        "syntax_blob_ratio": 0.0025,
    },
    "imu": {
        "enabled": True,
        "window_s": 4.0,
        "stale_s": 2.0,
        "thresholds": {
            "running_z_var": 1.5,
            "running_cadence_lo": 2.4, "running_cadence_hi": 4.0,
            "lifting_cadence_lo": 0.2, "lifting_cadence_hi": 0.8,
            "lifting_z_var": 1.2,
            "boxing_cadence_lo": 1.4, "boxing_cadence_hi": 3.4,
            "boxing_gyro": 0.6,
            "walking_cadence_lo": 1.5, "walking_cadence_hi": 2.6,
        },
    },
    "avatar": {
        # Procedural canvas vtuber palette. These are original recolorings
        # of the HUD's built-in anime base — deliberately NOT copies of any
        # licensed character. Bring your own real model via VTube Studio.
        "theme": "default",   # default | dark_swordsman | green_scout |
                              # silver_knight | blonde_prince | hacker
        "themes": ["default", "dark_swordsman", "green_scout",
                   "silver_knight", "blonde_prince", "hacker"],
        "engine": "procedural",   # procedural | live2d  (see overlay/assets/live2d/)
    },
    "vtube_studio": {
        # Set enabled: true and fill in hotkey IDs once you have VTube Studio
        # running with its Plugin API turned on (Settings -> Plugins ->
        # "Start API Server"). Hotkey IDs are shown in VTube Studio's UI.
        "enabled": False,
        "host": "127.0.0.1",
        "port": 8001,
        "token": "",           # cached at ~/.cache/hudstream/vts_token.json
        "hotkeys": {
            "speech": "", "speechcraft": "", "rizz": "",
            "agility": "", "sneak": "", "exploration": "",
            "bard": "", "strength": "", "combat": "",
            "intelligence": "", "enchanting": "",
            "shout_fus": "", "shout_yol": "", "shout_wuld": "",
            "shout_generic": "", "level_up": "",
        },
        "expressions": {},     # e.g. {"agility": "exp_sweat.json"}
        "reconnect_s": 5.0,
        "hotkey_cooldown_s": 0.6,
    },
    "desktop": {
        "enabled": True,
        "poll_s": 2.0,
        "coding_apps": ["code", "code - insiders", "cursor", "zed", "xcode", "intellij",
                        "pycharm", "webstorm", "goland", "rider", "android studio",
                        "visual studio", "vim", "neovim", "nvim", "emacs", "sublime",
                        "atom", "terminal", "iterm", "warp", "nova", "bbedit", "fleet",
                        "clion", "phpstorm", "rubymine"],
        "reading_apps": ["books", "kindle", "preview", "zotero", "mendeley",
                          "pdf expert", "acrobat", "skim", "safari", "chrome", "chromium",
                          "firefox", "arc", "brave", "edge", "opera", "vivaldi",
                          "notion", "obsidian", "evernote", "papers", "goodnotes"],
        "browser_doc_hints": ["pdf", "arxiv", "wiki", "docs", "doc", "read", "reader",
                                "paper", "manual", "book", "medium", "substack", "article",
                                "documentation", "spec", "rfc"],
    },
    "shouts": {
        "enabled": True,
        "threshold": 0.82,
        "cooldown_s": 60,
        "words": ["Fus Ro Dah", "Yol Toor Shul", "Feim Zii Gron", "Wuld Nah Kest", "Strun Bah Qo"],
    },
    "discovery": {
        "enabled": True,
        "radius_m": 80,
        "min_move_m": 40,
        "every_s": 60,
        "endpoint": "https://overpass-api.de/api/interpreter",
    },
    "progress": {
        "enabled": True,
        "path": "data/progress.json",
        "autosave_s": 30,
    },
    "vitals": {
        "stamina_drain": 6.0,
        "stamina_regen": 3.5,
        "magicka_drain": 4.5,
        "magicka_regen": 3.0,
        "health_drain": 1.2,
        "health_regen": 2.0,
    },
}


def _merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path: str | Path = "config.yaml") -> Dict[str, Any]:
    raw: Dict[str, Any] = {}
    p = Path(path)
    if p.exists():
        with p.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    return _merge(DEFAULTS, raw)
