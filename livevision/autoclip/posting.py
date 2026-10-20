"""Clip posting: the approval queue as records the phone can edit and post.

Every rendered clip lands in `state["pending"]` (publish.queue: always), so the
queue is there in dry_run too; publish.mode only decides whether Post reaches
the platforms. Posting is asynchronous: one thread per platform, and each
platform's progress is kept on the record and emitted as a `clip_status` event.

  server platforms  youtube, instagram: autoclip uploads them (publishers/)
  device platforms  tiktok, x: the phone hands the clip to the TikTok app
                    (Share Kit) or X's composer and reports back with mark()

A record:

  {"id", "cycle", "created", "clip": {...}, "platforms": [...suggested],
   "edits": {"title", "caption", "hashtags", "youtube_privacy"},
   "posts": {"youtube": {"state", "url", "message", "dry_run", "at"}, ...},
   "status": "ready | posting | partial | done"}

Post states: queued -> uploading -> posted | dry_run | failed; device
platforms: shared | cancelled | failed. A record moves to `state["posted"]`
once every platform it was posted to is posted / dry_run / shared.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .agents import ClipDecision
from .clips import Clip
from .publishers import get_publisher, publish_one

SERVER = ("youtube", "instagram")
DEVICE = ("tiktok", "x")
DONE = ("posted", "dry_run", "shared")
BUSY = ("queued", "uploading")
DEVICE_STATES = ("shared", "cancelled", "failed")
PRIVACY = ("public", "unlisted", "private")
KEEP_POSTED = 50

# what the phone's caption counters and checks use
LIMITS = {
    "youtube": {"title": 100, "caption": 5000, "max_seconds": 180},
    "instagram": {"caption": 2200, "max_seconds": 900},
    "tiktok": {"caption": 2200, "max_seconds": 600},
    "x": {"caption": 280, "max_seconds": 140},
}


def new_record(item_id: str, cycle: str, clip: Clip, platforms: List[str]) -> dict:
    d = clip.decision
    return {
        "id": item_id, "cycle": cycle, "created": round(time.time(), 3),
        "clip": clip.to_dict(), "platforms": list(platforms),
        "edits": {"title": d.title, "caption": d.caption, "hashtags": list(d.hashtags)},
        "posts": {}, "status": "ready",
    }


def _clip_from(rec: dict) -> Clip:
    info = rec["clip"]
    edits = rec.get("edits") or {}
    decision = ClipDecision.from_any(info.get("decision") or {}, {}) or ClipDecision(0, 0)
    decision.title = str(edits.get("title", decision.title) or "")
    decision.caption = str(edits.get("caption", decision.caption) or "")
    decision.hashtags = [str(h).lstrip("#") for h in edits.get("hashtags", decision.hashtags) or []]
    return Clip(path=Path(info["path"]), start=float(info.get("start", 0)),
                end=float(info.get("end", 0)), duration=float(info.get("duration", 0)),
                decision=decision,
                srt=Path(info["srt"]) if info.get("srt") else None,
                thumb=Path(info["thumb"]) if info.get("thumb") else None)


def _status(rec: dict) -> str:
    posts = rec.get("posts") or {}
    if not posts:
        return "ready"
    states = [p.get("state") for p in posts.values()]
    if any(s in BUSY for s in states):
        return "posting"
    if all(s in DONE for s in states):
        return "done"
    return "partial"


class ClipPoster:
    def __init__(self, cfg: Dict[str, Any], workdir: Path, state: Dict[str, Any],
                 lock: threading.RLock, save: Callable[[], None],
                 on_status: Optional[Callable[[dict], None]] = None):
        self.cfg = cfg
        self.workdir = Path(workdir)
        self.state = state
        self.lock = lock
        self.save = save
        self.on_status = on_status
        self._threads: Dict[str, List[threading.Thread]] = {}
        # posts that were mid-upload when the process died are not coming back
        with self.lock:
            for rec in self.state.get("pending", []):
                for post in (rec.get("posts") or {}).values():
                    if post.get("state") in BUSY:
                        post.update(state="failed", message="interrupted by a restart: post again")
                rec["status"] = _status(rec)

    # ------------------------------------------------------------------ config
    @property
    def pub_cfg(self) -> dict:
        # public_url_for (Instagram hosting: static) reads server.public_base_url
        return {**(self.cfg.get("publish", {}) or {}), "server": self.cfg.get("server", {}) or {}}

    @property
    def live(self) -> bool:
        return str(self.pub_cfg.get("mode", "dry_run")).lower() == "live"

    def platforms(self) -> dict:
        """What the phone can offer, and why something is greyed out."""
        pub = self.pub_cfg
        out = []
        for name in SERVER:
            cls = get_publisher(name)
            if cls is None:
                ok, why = False, "publisher not installed in this image"
            else:
                pub_obj = cls()
                ok = bool(pub_obj.enabled(pub))
                why = "" if ok else getattr(pub_obj, "missing", lambda c: "not configured")(pub)
            out.append({"name": name, "path": "server", "configured": ok, "reason": why,
                        "limits": LIMITS[name]})
        for name in DEVICE:
            out.append({"name": name, "path": "device", "configured": True,
                        "reason": "", "limits": LIMITS[name]})
        yt = pub.get("youtube", {}) or {}
        return {"mode": "live" if self.live else "dry_run", "platforms": out,
                "youtube_privacy": str(yt.get("privacy", "public")),
                "youtube_privacy_options": list(PRIVACY)}

    # ------------------------------------------------------------------ records
    def _find(self, item_id: str) -> dict:
        for rec in self.state.get("pending", []):
            if rec.get("id") == item_id:
                return rec
        for rec in self.state.get("posted", []):
            if rec.get("id") == item_id:
                return rec
        raise KeyError(f"no clip {item_id!r}")

    def get(self, item_id: str) -> dict:
        with self.lock:
            return _public(self._find(item_id))

    def pending(self) -> List[dict]:
        with self.lock:
            return [_public(r) for r in self.state.get("pending", [])]

    def posted(self) -> List[dict]:
        with self.lock:
            return [_public(r) for r in reversed(self.state.get("posted", []))]

    def edit(self, item_id: str, title: Optional[str] = None, caption: Optional[str] = None,
             hashtags: Optional[List[str]] = None, youtube_privacy: Optional[str] = None) -> dict:
        with self.lock:
            rec = self._find(item_id)
            edits = rec.setdefault("edits", {})
            if title is not None:
                edits["title"] = " ".join(str(title).split())
            if caption is not None:
                edits["caption"] = str(caption).strip()
            if hashtags is not None:
                edits["hashtags"] = [h for h in (str(x).strip().lstrip("#") for x in hashtags) if h]
            if youtube_privacy is not None:
                if youtube_privacy not in PRIVACY:
                    raise ValueError(f"youtube_privacy must be one of {PRIVACY}")
                edits["youtube_privacy"] = youtube_privacy
            self.save()
            return _public(rec)

    def reject(self, item_id: str) -> bool:
        with self.lock:
            before = len(self.state.get("pending", []))
            self.state["pending"] = [r for r in self.state.get("pending", []) if r.get("id") != item_id]
            self.save()
            return len(self.state["pending"]) < before

    # ------------------------------------------------------------------ posting
    def post(self, item_id: str, platforms: Optional[List[str]] = None,
             wait: bool = False, **edits: Any) -> dict:
        """Start posting to the server platforms. Already-posted platforms are
        skipped, so calling this again is Retry. Device platforms are refused:
        the phone shares those itself and reports with mark()."""
        if any(v is not None for v in edits.values()):
            self.edit(item_id, **edits)
        with self.lock:
            rec = self._find(item_id)
            names = list(dict.fromkeys(platforms or [p for p in rec.get("platforms") or []
                                                     if p in SERVER]))
            unknown = [p for p in names if p not in SERVER]
            if unknown:
                raise ValueError(f"not a server platform: {unknown} (server: {list(SERVER)}; "
                                 f"tiktok and x are shared from the phone)")
            posts = rec.setdefault("posts", {})
            todo = [p for p in names if (posts.get(p) or {}).get("state") not in (*DONE, *BUSY)]
            for p in todo:
                posts[p] = {"state": "queued", "url": "", "message": "", "at": round(time.time(), 3)}
            rec["status"] = _status(rec)
            self.save()
        threads = [threading.Thread(target=self._run, args=(item_id, p), daemon=True,
                                    name=f"post-{item_id}-{p}") for p in todo]
        self._threads[item_id] = threads
        for t in threads:
            t.start()
        for p in todo:
            self._emit(item_id, p)
        if wait:
            for t in threads:
                t.join()
        return self.get(item_id)

    def _run(self, item_id: str, platform: str) -> None:
        with self.lock:
            rec = self._find(item_id)
            clip = _clip_from(rec)
            privacy = (rec.get("edits") or {}).get("youtube_privacy")
            rec["posts"][platform].update(state="uploading", at=round(time.time(), 3))
            self.save()
        self._emit(item_id, platform)
        cfg = self.pub_cfg
        if privacy:
            cfg["youtube"] = {**(cfg.get("youtube") or {}), "privacy": privacy}
        res = publish_one(clip, platform, cfg, self.workdir)
        if res.ok:
            state = "dry_run" if res.dry_run else "posted"
        else:
            state = "failed"
        self._finish(item_id, platform, {
            "state": state, "url": res.url if not res.dry_run else "",
            "media_id": res.media_id, "message": res.message, "dry_run": bool(res.dry_run)})

    def mark(self, item_id: str, platform: str, state: str, message: str = "",
             url: str = "") -> dict:
        """The phone shared a device platform (TikTok, X) or gave up."""
        if platform not in DEVICE:
            raise ValueError(f"not a device platform: {platform!r} (device: {list(DEVICE)})")
        if state not in DEVICE_STATES:
            raise ValueError(f"state must be one of {DEVICE_STATES}")
        self._finish(item_id, platform, {"state": state, "message": message, "url": url})
        return self.get(item_id)

    def _finish(self, item_id: str, platform: str, post: dict) -> None:
        with self.lock:
            rec = self._find(item_id)
            rec.setdefault("posts", {})[platform] = {**post, "at": round(time.time(), 3)}
            rec["status"] = _status(rec)
            if rec["status"] == "done" and rec in self.state.get("pending", []):
                self.state["pending"].remove(rec)
                posted = self.state.setdefault("posted", [])
                posted.append(rec)
                del posted[:-KEEP_POSTED]
            self.save()
        self._emit(item_id, platform)

    def _emit(self, item_id: str, platform: str) -> None:
        if not self.on_status:
            return
        try:
            with self.lock:
                rec = self._find(item_id)
                post = dict((rec.get("posts") or {}).get(platform) or {})
                status = rec.get("status")
            self.on_status({"id": item_id, "platform": platform, "status": status, **post})
        except Exception:  # noqa: BLE001 - an event must never break a post
            pass

    def results(self, item_id: str) -> List[dict]:
        """Per-platform answers in the publishers' {platform, ok, ...} shape."""
        rec = self.get(item_id)
        return [{"platform": p, "ok": v.get("state") in DONE, "dry_run": bool(v.get("dry_run")),
                 "url": v.get("url", ""), "media_id": v.get("media_id", ""),
                 "message": v.get("message", "")} for p, v in rec.get("posts", {}).items()]


def _public(rec: dict) -> dict:
    """The record as the phone sees it: outbox-relative media paths added."""
    out = dict(rec)
    clip = rec.get("clip") or {}
    stem = Path(clip.get("path", "")).stem
    out["video_url"] = f"outbox/{Path(clip.get('path', '')).name}" if stem else ""
    out["thumb_url"] = f"outbox/{Path(clip['thumb']).name}" if clip.get("thumb") else ""
    out.setdefault("edits", {})
    out.setdefault("posts", {})
    out["status"] = _status(rec)
    return out
