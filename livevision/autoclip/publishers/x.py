"""X (Twitter) video post: chunked media upload (v1.1) + tweet create (v2).

Requires OAuth 1.0a user credentials (4 env vars, see publish.x in autoclip.yaml)
and `pip install requests-oauthlib`.

Note: X caps native video at ~140s; the X config's max_seconds trims accordingly.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
from pathlib import Path

from ..clips import Clip
from . import PublishResult, Publisher

UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"
TWEET_URL = "https://api.twitter.com/2/tweets"


class XPublisher(Publisher):
    name = "x"

    def enabled(self, cfg: dict) -> bool:
        env = self._env(cfg)
        return all(os.environ.get(v) for v in env.values())

    @staticmethod
    def _env(cfg: dict) -> dict:
        x = cfg.get("x", {}) or {}
        return {
            "consumer_key": x.get("consumer_key_env", "X_CONSUMER_KEY"),
            "consumer_secret": x.get("consumer_secret_env", "X_CONSUMER_SECRET"),
            "token": x.get("access_token_env", "X_ACCESS_TOKEN"),
            "token_secret": x.get("access_token_secret_env", "X_ACCESS_TOKEN_SECRET"),
        }

    def _oauth(self, cfg: dict):
        from requests_oauthlib import OAuth1Session  # type: ignore

        env = self._env(cfg)
        values = {k: os.environ.get(v, "") for k, v in env.items()}
        missing = [k for k, v in values.items() if not v]
        if missing:
            raise RuntimeError(f"missing X credentials: {missing} (env: {list(env.values())})")
        return OAuth1Session(
            values["consumer_key"], values["consumer_secret"],
            values["token"], values["token_secret"],
        )

    def _upload(self, session, clip: Clip, cfg: dict) -> str:
        total = clip.path.stat().st_size
        media_type = "video/mp4"

        init = session.post(UPLOAD_URL, data={
            "command": "INIT", "total_bytes": str(total), "media_type": media_type,
            "media_category": "tweet_video",
        }, timeout=60)
        if init.status_code >= 400:
            raise RuntimeError(f"INIT failed {init.status_code}: {init.text[:300]}")
        media_id = str(init.json()["media_id_string"])

        with clip.path.open("rb") as fh:
            index = 0
            while True:
                chunk = fh.read(4 * 1024 * 1024)
                if not chunk:
                    break
                resp = session.post(UPLOAD_URL, data={
                    "command": "APPEND", "media_id": media_id,
                    "segment_index": str(index), "media": chunk,
                }, timeout=180)
                if resp.status_code >= 400:
                    raise RuntimeError(f"APPEND failed {resp.status_code}: {resp.text[:300]}")
                index += 1

        fin = session.post(UPLOAD_URL, data={"command": "FINALIZE", "media_id": media_id},
                           timeout=60)
        if fin.status_code >= 400:
            raise RuntimeError(f"FINALIZE failed {fin.status_code}: {fin.text[:300]}")
        payload = fin.json()
        state = (payload.get("processing_info") or {}).get("state")
        deadline = time.time() + 180
        while state in ("pending", "in_progress") and time.time() < deadline:
            wait = int((payload.get("processing_info") or {}).get("check_after_secs", 5))
            time.sleep(max(1, wait))
            st = session.get(UPLOAD_URL, params={"command": "STATUS", "media_id": media_id},
                             timeout=60)
            payload = st.json() if st.status_code < 400 else {}
            state = (payload.get("processing_info") or {}).get("state")
        if state == "failed":
            raise RuntimeError(f"X media processing failed: {payload}")
        return media_id

    def publish(self, clip: Clip, cfg: dict, workdir: Path) -> PublishResult:
        session = self._oauth(cfg)
        media_id = self._upload(session, clip, cfg)

        text = clip.decision.caption or clip.decision.title or cfg.get("default_title", "")
        if clip.decision.hashtags:
            text = f"{text} " + " ".join(f"#{h.lstrip('#')}" for h in clip.decision.hashtags[:5])
        text = text.strip()[:280] or "clip"

        resp = session.post(TWEET_URL, data=json.dumps({
            "text": text, "media": {"media_ids": [media_id]},
        }), headers={"Content-Type": "application/json"}, timeout=60)
        if resp.status_code >= 400:
            raise RuntimeError(f"tweet create failed {resp.status_code}: {resp.text[:300]}")
        data = resp.json().get("data") or {}
        tweet_id = str(data.get("id", ""))
        return PublishResult(platform="x", ok=bool(tweet_id), media_id=tweet_id,
                             url=f"https://x.com/i/web/status/{tweet_id}" if tweet_id else "",
                             message="posted", raw=data)
