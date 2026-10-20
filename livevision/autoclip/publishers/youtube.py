"""YouTube (Shorts) upload via the Data API v3 resumable endpoint.

Setup:
  pip install google-api-python-client google-auth-oauthlib
  Put a Google Cloud OAuth client (Desktop app) JSON at publish.youtube.client_secrets.
  First run opens a browser and caches the token at publish.youtube.credentials.
"""
from __future__ import annotations

from pathlib import Path

from ..clips import Clip
from . import PublishResult, Publisher

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubePublisher(Publisher):
    name = "youtube"

    def _creds_path(self, cfg: dict) -> Path:
        return Path(cfg.get("credentials") or "var/autoclip/youtube_creds.json")

    def enabled(self, cfg: dict) -> bool:
        return self._creds_path(cfg).exists() or bool(cfg.get("client_secrets"))

    def _service(self, cfg: dict):
        from google.oauth2.credentials import Credentials  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
        from googleapiclient.discovery import build  # type: ignore

        creds_path = self._creds_path(cfg)
        creds = None
        if creds_path.exists():
            creds = Credentials.from_authorized_user_file(str(creds_path), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            secrets = cfg.get("client_secrets")
            if not secrets or not Path(secrets).exists():
                raise RuntimeError("no valid YouTube credentials; set publish.youtube.client_secrets")
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
            creds = flow.run_local_server(port=0)
            creds_path.parent.mkdir(parents=True, exist_ok=True)
            creds_path.write_text(creds.to_json(), encoding="utf-8")
        return build("youtube", "v3", credentials=creds, cache_discovery=False)

    def publish(self, clip: Clip, cfg: dict, workdir: Path) -> PublishResult:
        from googleapiclient.http import MediaFileUpload  # type: ignore

        yt = cfg.get("youtube", {}) or {}
        service = self._service(yt)
        tags = list(clip.decision.hashtags) or list(cfg.get("default_tags") or [])
        body = {
            "snippet": {
                "title": (clip.decision.title or cfg.get("default_title", "Clip"))[:100],
                "description": _description(clip, cfg),
                "tags": tags[:30],
                "categoryId": str(yt.get("category", "22")),
            },
            "status": {
                "privacyStatus": str(yt.get("privacy", "unlisted")),
                "selfDeclaredMadeForKids": bool(yt.get("made_for_kids", False)),
                "embeddable": True,
            },
        }
        media = MediaFileUpload(str(clip.path), mimetype="video/mp4",
                                resumable=True, chunksize=8 * 1024 * 1024)
        request = service.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()
        video_id = response.get("id", "")
        url = f"https://youtu.be/{video_id}" if video_id else ""
        return PublishResult(platform="youtube", ok=bool(video_id), url=url,
                             media_id=video_id, message="uploaded", raw=response)


def _description(clip: Clip, cfg: dict) -> str:
    parts = []
    if clip.decision.caption:
        parts.append(clip.decision.caption)
    if clip.decision.hashtags:
        parts.append(" ".join(f"#{h.lstrip('#')}" for h in clip.decision.hashtags))
    parts.append(f"#{int(clip.start)}s-#{int(clip.end)}s of the rolling buffer")
    return "\n\n".join(p for p in parts if p)[:5000]
