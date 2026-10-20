"""Local outbox publisher: always available, and the default (dry-run) target."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from ..clips import Clip
from . import PublishResult, Publisher


class LocalPublisher(Publisher):
    name = "local"

    def publish(self, clip: Clip, cfg: dict, workdir: Path) -> PublishResult:
        outbox = Path(workdir) / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        dest = outbox / clip.path.name
        if clip.path.resolve() != dest.resolve():
            shutil.copy2(clip.path, dest)
        for extra in (clip.srt, clip.thumb):
            if extra and extra.exists():
                shutil.copy2(extra, outbox / extra.name)
        meta = outbox / f"{clip.path.stem}.json"
        meta.write_text(json.dumps(clip.to_dict(), indent=2), encoding="utf-8")
        return PublishResult(platform="local", ok=True, dry_run=True, url=str(dest),
                             media_id=clip.path.stem, message="written to outbox")
