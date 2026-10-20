"""Instagram Reels publish via the Instagram Graph API (two-step container flow).

Requires:
  - A Business/Creator Instagram account linked to a Facebook Page
  - A Page access token with instagram_content_publish (env var, see config);
    `python -m autoclip ig-token` turns a short-lived user token into a Page
    token that does not expire and prints the IG user id
  - A publicly reachable URL for the video -> set publish.instagram.hosting
      static : this app serves /outbox/<file>, so publish.server.public_base_url
               must be a public URL (ngrok / cloudflared / your domain)
      s3     : uploads to S3/R2 first (pip install boto3)
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

from ..clips import Clip
from . import PublishResult, Publisher, public_url_for


class InstagramPublisher(Publisher):
    name = "instagram"

    def enabled(self, cfg: dict) -> bool:
        ig = cfg.get("instagram", {}) or {}
        env = ig.get("access_token_env", "INSTAGRAM_ACCESS_TOKEN")
        return bool(ig.get("ig_user_id")) and bool(os.environ.get(env))

    def missing(self, cfg: dict) -> str:
        ig = cfg.get("instagram", {}) or {}
        need = []
        if not ig.get("ig_user_id"):
            need.append("INSTAGRAM_USER_ID")
        if not os.environ.get(ig.get("access_token_env", "INSTAGRAM_ACCESS_TOKEN")):
            need.append(ig.get("access_token_env", "INSTAGRAM_ACCESS_TOKEN"))
        if not need and not str((cfg.get("server", {}) or {}).get("public_base_url") or ""):
            return "server.public_base_url is not set (Instagram fetches the clip from it)"
        return f"set {', '.join(need)} (python -m autoclip ig-token)" if need else ""

    def _token(self, cfg: dict) -> str:
        ig = cfg.get("instagram", {}) or {}
        return os.environ.get(ig.get("access_token_env", "INSTAGRAM_ACCESS_TOKEN"), "")

    def _api(self, cfg: dict, path: str, params: dict | None = None,
             method: str = "GET") -> dict:
        version = str((cfg.get("instagram", {}) or {}).get("graph_version", "v23.0"))
        url = f"https://graph.facebook.com/{version}/{path}"
        data = dict(params or {})
        data["access_token"] = self._token(cfg)
        if method == "GET":
            full = f"{url}?{urllib.parse.urlencode(data)}"
            req = urllib.request.Request(full, method="GET")
        else:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(),
                                         method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"Graph API {method} {path} -> {exc.code}: {body[:400]}") from exc

    def publish(self, clip: Clip, cfg: dict, workdir: Path) -> PublishResult:
        ig = cfg.get("instagram", {}) or {}
        ig_user_id = ig.get("ig_user_id")
        if not ig_user_id:
            return PublishResult(platform="instagram", ok=False,
                                 message="publish.instagram.ig_user_id not set")

        video_url = public_url_for(clip, cfg, workdir)
        if not video_url:
            return PublishResult(
                platform="instagram", ok=False,
                message="Instagram needs a public video URL: set server.public_base_url "
                        "(hosting=static) or instagram.hosting_s3 (hosting=s3)")

        caption = clip.decision.caption or clip.decision.title or cfg.get("default_title", "")
        if clip.decision.hashtags:
            caption = f"{caption}\n\n" + " ".join(
                f"#{h.lstrip('#')}" for h in clip.decision.hashtags)

        created = self._api(cfg, f"{ig_user_id}/media", {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "share_to_feed": "true" if ig.get("share_to_feed", True) else "false",
        }, method="POST")
        container_id = created.get("id")
        if not container_id:
            return PublishResult(platform="instagram", ok=False,
                                 message=f"container create failed: {created}")

        # poll until FINISHED (Instagram transcodes before it will publish)
        deadline = time.time() + float(ig.get("poll_timeout", 300))
        while time.time() < deadline:
            status = self._api(cfg, container_id, {"fields": "status_code,status"})
            code = (status or {}).get("status_code")
            if code == "FINISHED":
                break
            if code == "ERROR":
                return PublishResult(platform="instagram", ok=False, media_id=str(container_id),
                                     message=f"container error: {status}")
            time.sleep(float(ig.get("poll_seconds", 5)))

        published = self._api(cfg, f"{ig_user_id}/media_publish",
                              {"creation_id": container_id}, method="POST")
        media_id = str(published.get("id") or container_id)
        return PublishResult(platform="instagram", ok=bool(published.get("id")),
                             media_id=media_id, message="published",
                             url=f"https://www.instagram.com/reel/{media_id}/" if published.get("id") else "",
                             raw=published)


# --------------------------------------------------------------------------- token helper
# `python -m autoclip ig-token` on a laptop. Facebook Login path: a Page token
# made from a long-lived user token does not expire, so nothing has to
# refresh it on the VM.
def page_token(app_id: str, app_secret: str, user_token: str,
               version: str = "v23.0", page: str = "") -> dict:
    """short-lived user token -> long-lived user token -> Page token + IG user id."""
    base = f"https://graph.facebook.com/{version}"

    def get(path: str, **params) -> dict:
        url = f"{base}/{path}?{urllib.parse.urlencode(params)}"
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8", "replace") or "{}")
            msg = (body.get("error") or {}).get("message", "") if isinstance(body, dict) else ""
            raise SystemExit(f"Graph API {path} -> {exc.code}: {msg[:300]}") from None

    long_user = get("oauth/access_token", grant_type="fb_exchange_token", client_id=app_id,
                    client_secret=app_secret, fb_exchange_token=user_token)["access_token"]
    pages = get("me/accounts", access_token=long_user,
                fields="id,name,access_token,instagram_business_account").get("data") or []
    pages = [p for p in pages if p.get("instagram_business_account")]
    if page:
        pages = [p for p in pages if page in (p.get("id"), p.get("name"))]
    if not pages:
        raise SystemExit("no Facebook Page with a linked Instagram business account "
                         "(token needs pages_show_list, instagram_basic, "
                         "instagram_content_publish, pages_read_engagement)")
    p = pages[0]
    return {"page": p.get("name", ""), "page_id": p["id"], "access_token": p["access_token"],
            "ig_user_id": p["instagram_business_account"]["id"],
            "others": [x.get("name") for x in pages[1:]]}
