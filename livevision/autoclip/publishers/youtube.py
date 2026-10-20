"""YouTube (Shorts) upload via the Data API v3 resumable endpoint.

Credentials, first match wins:
  1. publish.youtube client_id / client_secret / refresh_token: the same
     YOUTUBE_CLIENT_ID / _SECRET / _REFRESH_TOKEN the stream title uses
     (`python -m autoclip title-auth youtube`; its youtube.force-ssl scope is
     accepted by videos.insert). This is the headless path the VPS uses.
  2. a cached authorized-user file at publish.youtube.credentials
  3. laptop only: a Desktop OAuth client JSON at publish.youtube.client_secrets,
     which opens a browser once (needs google-auth-oauthlib and a terminal)

  pip install google-api-python-client google-auth
"""
from __future__ import annotations

import sys
from pathlib import Path

from ..clips import Clip
from . import PublishResult, Publisher

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


class YouTubePublisher(Publisher):
    name = "youtube"

    def _creds_path(self, cfg: dict) -> Path:
        return Path(cfg.get("credentials") or "var/autoclip/youtube_creds.json")

    @staticmethod
    def _refreshable(yt: dict) -> bool:
        return all(yt.get(k) for k in ("client_id", "client_secret", "refresh_token"))

    def enabled(self, cfg: dict) -> bool:
        yt = cfg.get("youtube", {}) or {}
        return self._refreshable(yt) or self._creds_path(yt).exists()

    def missing(self, cfg: dict) -> str:
        yt = cfg.get("youtube", {}) or {}
        need = [env for key, env in (("client_id", "YOUTUBE_CLIENT_ID"),
                                     ("client_secret", "YOUTUBE_CLIENT_SECRET"),
                                     ("refresh_token", "YOUTUBE_REFRESH_TOKEN")) if not yt.get(key)]
        return f"set {', '.join(need)} (python -m autoclip title-auth youtube)" if need else ""

    def _service(self, yt: dict):
        from google.oauth2.credentials import Credentials  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
        from googleapiclient.discovery import build  # type: ignore

        if self._refreshable(yt):
            # no scopes: refresh keeps whatever the consent granted
            # (youtube.force-ssl from title-auth covers uploads)
            creds = Credentials(token=None, refresh_token=yt["refresh_token"],
                                client_id=yt["client_id"], client_secret=yt["client_secret"],
                                token_uri=TOKEN_URI)
            creds.refresh(Request())
            return build("youtube", "v3", credentials=creds, cache_discovery=False)

        creds_path = self._creds_path(yt)
        creds = None
        if creds_path.exists():
            creds = Credentials.from_authorized_user_file(str(creds_path), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            secrets = yt.get("client_secrets")
            if not secrets or not Path(secrets).exists() or not sys.stdin.isatty():
                raise RuntimeError("no YouTube credentials: set YOUTUBE_CLIENT_ID, "
                                   "YOUTUBE_CLIENT_SECRET and YOUTUBE_REFRESH_TOKEN")
            from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
            creds = flow.run_local_server(port=0)
            creds_path.parent.mkdir(parents=True, exist_ok=True)
            creds_path.write_text(creds.to_json(), encoding="utf-8")
        return build("youtube", "v3", credentials=creds, cache_discovery=False)

    def publish(self, clip: Clip, cfg: dict, workdir: Path) -> PublishResult:
        from googleapiclient.http import MediaFileUpload  # type: ignore

        yt = cfg.get("youtube", {}) or {}
        service = self._service(yt)
        body = video_body(clip, cfg)
        media = MediaFileUpload(str(clip.path), mimetype="video/mp4",
                                resumable=True, chunksize=8 * 1024 * 1024)
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()
        video_id = response.get("id", "")
        url = f"https://youtube.com/shorts/{video_id}" if video_id else ""
        return PublishResult(platform="youtube", ok=bool(video_id), url=url,
                             media_id=video_id, message="uploaded", raw=response)


def video_body(clip: Clip, cfg: dict) -> dict:
    yt = cfg.get("youtube", {}) or {}
    tags = list(clip.decision.hashtags) or list(cfg.get("default_tags") or [])
    return {
        "snippet": {
            "title": (clip.decision.title or cfg.get("default_title", "Clip"))[:100],
            "description": _description(clip, cfg),
            "tags": [t.lstrip("#") for t in tags][:30],
            "categoryId": str(yt.get("category", "22")),
        },
        "status": {
            "privacyStatus": str(yt.get("privacy", "public")),
            "selfDeclaredMadeForKids": bool(yt.get("made_for_kids", False)),
            "embeddable": True,
        },
    }


def _description(clip: Clip, cfg: dict) -> str:
    parts = []
    if clip.decision.caption:
        parts.append(clip.decision.caption)
    tags = [f"#{h.lstrip('#')}" for h in clip.decision.hashtags]
    if not any(t.lower() == "#shorts" for t in tags):
        tags.append("#Shorts")
    parts.append(" ".join(tags))
    return "\n\n".join(p for p in parts if p)[:5000]
