"""Persist your skill progress to disk between streams.

Atomic write (tmp file + rename). If the file is missing or corrupt the engine
starts fresh and your next save will create a new one.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Optional


def load(path: str | Path) -> Optional[dict]:
    p = Path(path)
    if not p.exists():
        return None
    try:
        with p.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def save(path: str | Path, data: dict) -> bool:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(p.parent),
                                         prefix=".progress-", suffix=".tmp",
                                         encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            tmp = fh.name
        os.replace(tmp, p)
        return True
    except Exception:
        return False
