"""Platform publishers. Every platform is optional and lazy-loaded.

If credentials or SDKs are missing, the platform reports `ok=False, dry_run=True`
instead of crashing the pipeline. Flip `publish.mode: live` when you actually
want to post.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Type

from ..clips import Clip


@dataclass
class PublishResult:
    platform: str
    ok: bool
    dry_run: bool = False
    url: str = ""
    media_id: str = ""
    message: str = ""
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"platform": self.platform, "ok": self.ok, "dry_run": self.dry_run,
                "url": self.url, "media_id": self.media_id, "message": self.message}


class Publisher:
    name = "base"

    def enabled(self, cfg: dict) -> bool:
        return True

    def publish(self, clip: Clip, cfg: dict, workdir: Path) -> PublishResult:
        raise NotImplementedError


# --------------------------------------------------------------------------- registry
def _load(name: str) -> Optional[Type[Publisher]]:
    if name == "local":
        from .local import LocalPublisher
        return LocalPublisher
    if name == "youtube":
        try:
            from .youtube import YouTubePublisher
            return YouTubePublisher
        except Exception:
            return None
    if name == "instagram":
        try:
            from .instagram import InstagramPublisher
            return InstagramPublisher
        except Exception:
            return None
    if name == "x":
        try:
            from .x import XPublisher
            return XPublisher
        except Exception:
            return None
    return None


_CACHE: Dict[str, Optional[Type[Publisher]]] = {}


def get_publisher(name: str) -> Optional[Type[Publisher]]:
    if name not in _CACHE:
        _CACHE[name] = _load(name)
    return _CACHE[name]


def available_platforms() -> List[str]:
    return [p for p in ("local", "youtube", "instagram", "x") if get_publisher(p) is not None]


def publish_one(clip: Clip, platform: str, cfg: dict, workdir: Path) -> PublishResult:
    """Publish to one platform, always falling back to the local outbox."""
    pub_cls = get_publisher(platform)
    mode = str(cfg.get("mode", "dry_run")).lower()
    if pub_cls is None:
        return PublishResult(platform=platform, ok=False, dry_run=True,
                             message=f"publisher {platform!r} unavailable (missing dependency)")
    publisher = pub_cls()  # type: ignore[call-arg]
    if mode != "live" and platform != "local":
        # dry run: drop the artifact in the outbox so a human can eyeball it
        return _dry_run(clip, platform, cfg, workdir,
                        message=f"dry_run: would publish to {platform}")
    try:
        return publisher.publish(clip, cfg, workdir)
    except Exception as exc:  # noqa: BLE001
        return PublishResult(platform=platform, ok=False, dry_run=(mode != "live"),
                             message=f"{platform} publish failed: {exc}")


def _dry_run(clip: Clip, platform: str, cfg: dict, workdir: Path, message: str) -> PublishResult:
    outbox = Path(workdir) / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    dest = outbox / clip.path.name
    try:
        if clip.path.resolve() != dest.resolve():
            shutil.copy2(clip.path, dest)
    except Exception:
        pass
    return PublishResult(platform=platform, ok=True, dry_run=True,
                         url=str(dest), message=message)


def publish_all(clip: Clip, platforms: List[str], cfg: dict, workdir: Path) -> List[PublishResult]:
    return [publish_one(clip, p, cfg, workdir) for p in platforms]


# --------------------------------------------------------------------------- hosting
def public_url_for(clip: Clip, cfg: dict, workdir: Path) -> str:
    """Instagram needs a reachable URL. Two strategies: static (this server) or S3/R2."""
    ig = cfg.get("instagram", {}) or {}
    strategy = str(ig.get("hosting", "static")).lower()
    if strategy == "s3":
        try:
            import boto3  # type: ignore
        except Exception:
            return ""
        s3cfg = ig.get("hosting_s3", {}) or {}
        bucket = s3cfg.get("bucket")
        if not bucket:
            return ""
        key = f"{s3cfg.get('prefix', 'autoclip/')}{clip.path.name}"
        kwargs = {"region_name": s3cfg.get("region") or None,
                  "endpoint_url": s3cfg.get("endpoint") or None}
        kwargs = {k: v for k, v in kwargs.items() if v}
        boto3.client("s3", **kwargs).upload_file(str(clip.path), bucket, key)
        base = str(s3cfg.get("public_base_url") or "").rstrip("/")
        return f"{base}/{key}" if base else f"https://{bucket}.s3.amazonaws.com/{key}"

    base = str(cfg.get("server", {}).get("public_base_url") or "").rstrip("/")
    if not base:
        return ""
    outbox = Path(workdir) / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    dest = outbox / clip.path.name
    try:
        if clip.path.resolve() != dest.resolve():
            shutil.copy2(clip.path, dest)
    except Exception:
        pass
    return f"{base}/outbox/{clip.path.name}"
