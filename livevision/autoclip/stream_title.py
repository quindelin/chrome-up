"""Live stream title: set it on every restream platform that has an API for it.

POST /api/autoclip/live/title {"title": "...", "platforms": [...]} lands here.
Each platform answers {platform, ok, message}; tokens never leave this module.

  twitch   Helix PATCH /helix/channels (scope channel:manage:broadcast)
  youtube  Data API v3 liveBroadcasts.update on the active (else upcoming)
           broadcast's snippet (scope youtube or youtube.force-ssl)
  kick     public API PATCH /public/v1/channels stream_title (scope channel:write)
  x        no public API for a live broadcast's title (Media Studio only)
  rumble   the Live Stream API is read-only

Credentials come from autoclip.yaml `stream_title:` (env vars in .env, see
docs/STREAM_TITLE.md). With a refresh token + client secret, access tokens
are refreshed here and the newest refresh token (Twitch and Kick rotate them)
is kept in <workdir>/title_tokens.json, mode 0600. Missing credentials are an
`ok: false` answer, never an exception.

The last title is remembered in <workdir>/title.json, so a restream that
starts later ("go live on twitch") gets it re-applied.
"""
from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .livestream import resolve_name

SUPPORTED = ("twitch", "youtube", "kick")
UNSUPPORTED = {
    "x": "not supported: X has no public API for a live broadcast's title "
         "(set it in Media Studio / Live Studio)",
    "rumble": "not supported: Rumble's Live Stream API is read-only "
              "(set it on rumble.com)",
}
DEFAULT_PLATFORMS = ("twitch", "youtube", "kick", "x", "rumble")
MAX_LEN = {"twitch": 140, "youtube": 100, "kick": 100}

TWITCH_API = "https://api.twitch.tv/helix"
TWITCH_TOKEN = "https://id.twitch.tv/oauth2/token"
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
KICK_API = "https://api.kick.com/public/v1"
KICK_TOKEN = "https://id.kick.com/oauth/token"


class _Fail(Exception):
    """A platform said no. `retry`: worth trying again later (no broadcast yet, network)."""

    def __init__(self, message: str, retry: bool = False):
        super().__init__(message)
        self.retry = retry


def _http(method: str, url: str, *, headers: Optional[Dict[str, str]] = None,
          json_body: Any = None, form: Optional[Dict[str, str]] = None,
          timeout: float = 10.0) -> Tuple[int, Any]:
    """One HTTP call -> (status, parsed JSON or text). Tests replace this."""
    data = None
    hdrs = dict(headers or {})
    if json_body is not None:
        data = json.dumps(json_body).encode()
        hdrs["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read()
    text = raw.decode("utf-8", errors="replace")
    try:
        return status, json.loads(text) if text else None
    except ValueError:
        return status, text


def _call(method: str, url: str, **kw) -> Tuple[int, Any]:
    try:
        return _http(method, url, **kw)
    except Exception as exc:  # noqa: BLE001 - DNS, timeout, TLS
        raise _Fail(f"unreachable: {type(exc).__name__}", retry=True)


def _why(body: Any) -> str:
    """The platform's own error text, short. Never the request (it has the token)."""
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):             # Google: {"error": {"message": ...}}
            return str(err.get("message") or err.get("status") or "")[:200]
        msg = body.get("message") or body.get("error_description") or err or ""
        return str(msg)[:200]
    return str(body or "")[:200]


class StreamTitle:
    def __init__(self, cfg: Dict[str, Any], workdir: Path,
                 platforms: Optional[List[str]] = None,
                 on_change: Optional[Callable[[dict], None]] = None):
        self.cfg = cfg or {}
        self.workdir = Path(workdir)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.workdir / "title.json"
        self.tokens_path = self.workdir / "title_tokens.json"
        self.platforms = [resolve_name(p) for p in (platforms or DEFAULT_PLATFORMS)]
        self.on_change = on_change
        self.retry_delays = [float(x) for x in self.cfg.get("retry_delays", [30, 90])]
        self._lock = threading.Lock()
        self.state = self._read(self.state_path)
        self._tokens = self._read(self.tokens_path)

    # ------------------------------------------------------------------ files
    @staticmethod
    def _read(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - missing / corrupt = start empty
            return {}

    def _save_state(self) -> None:
        try:
            self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

    def _save_tokens(self) -> None:
        try:
            fd = os.open(self.tokens_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._tokens, fh)
        except Exception:  # noqa: BLE001
            pass

    # ------------------------------------------------------------------ public
    def configured(self, platform: str) -> bool:
        c = self.cfg.get(platform) or {}
        if platform == "youtube":
            return bool(c.get("client_id") and c.get("client_secret")
                        and (c.get("refresh_token") or self._tokens.get("youtube", {}).get("refresh_token")))
        if platform in ("twitch", "kick"):
            cache = self._tokens.get(platform, {})
            refreshable = bool(c.get("client_id") and c.get("client_secret")
                               and (c.get("refresh_token") or cache.get("refresh_token")))
            if platform == "kick":      # Kick needs no Client-Id header: a token is enough
                return bool(c.get("user_token") or refreshable)
            return bool(c.get("client_id") and (c.get("user_token") or refreshable))
        return False

    def status(self) -> dict:
        return {
            "title": self.state.get("title", ""),
            "updated_at": self.state.get("updated_at"),
            "results": self.state.get("results", []),
            "platforms": [{"name": p, "supported": p in SUPPORTED,
                           "configured": self.configured(p)} for p in self.platforms],
        }

    def set(self, title: str, platforms: Optional[List[str]] = None) -> dict:
        title = " ".join(str(title or "").split())
        if not title:
            return {"ok": False, "title": "", "message": "title is empty", "results": []}
        names = [resolve_name(p) for p in (platforms or self.platforms)]
        if "all" in names:
            names = list(self.platforms)
        names = list(dict.fromkeys(names))
        # in parallel: the phone is waiting, and each platform is a few round trips
        with ThreadPoolExecutor(max_workers=max(1, len(names))) as pool:
            results = [r for r, _ in pool.map(lambda n: self._apply(n, title), names)]
        with self._lock:
            self.state = {"title": title, "updated_at": round(time.time(), 3), "results": results}
            self._save_state()
        out = {"ok": any(r["ok"] for r in results), "title": title, "results": results}
        if self.on_change:
            try:
                self.on_change(out)
            except Exception:  # noqa: BLE001
                pass
        return out

    def apply(self, platform: str) -> Optional[dict]:
        """Re-apply the remembered title to one platform (None if there is none)."""
        title = self.state.get("title")
        if not title:
            return None
        res = self._apply(resolve_name(platform), title)[0]
        with self._lock:
            kept = [r for r in self.state.get("results", []) if r.get("platform") != res["platform"]]
            self.state["results"] = kept + [res]
            self._save_state()
        return res

    def reapply_async(self, platform: str) -> None:
        """A restream just started: give it the title, retrying while the
        platform is still bringing the broadcast up (YouTube takes a while)."""
        if not self.state.get("title"):
            return

        def run() -> None:
            for delay in [0.0, *self.retry_delays]:
                time.sleep(delay)
                title = self.state.get("title")
                if not title:
                    return
                res, retry = self._apply(resolve_name(platform), title)
                with self._lock:
                    kept = [r for r in self.state.get("results", [])
                            if r.get("platform") != res["platform"]]
                    self.state["results"] = kept + [res]
                    self._save_state()
                if res["ok"] or not retry:
                    return

        threading.Thread(target=run, name=f"title-{platform}", daemon=True).start()

    # ------------------------------------------------------------------ per platform
    def _apply(self, platform: str, title: str) -> Tuple[dict, bool]:
        if platform in UNSUPPORTED:
            return {"platform": platform, "ok": False, "message": UNSUPPORTED[platform]}, False
        fn = {"twitch": self._twitch, "youtube": self._youtube, "kick": self._kick}.get(platform)
        if fn is None:
            return {"platform": platform, "ok": False,
                    "message": "not supported: no title API for this target"}, False
        cut = title[:MAX_LEN.get(platform, 140)]
        try:
            fn(cut)
        except _Fail as exc:
            return {"platform": platform, "ok": False, "message": str(exc)}, exc.retry
        except Exception as exc:  # noqa: BLE001 - never let one platform break the rest
            return {"platform": platform, "ok": False, "message": f"error: {type(exc).__name__}"}, False
        msg = "title set" if cut == title else f"title set (cut to {len(cut)} characters)"
        return {"platform": platform, "ok": True, "message": msg}, False

    # ---- tokens
    def _token(self, platform: str, token_url: str, force_refresh: bool = False) -> str:
        """Cached access token, else refreshed, else the static user token."""
        c = self.cfg.get(platform) or {}
        cache = self._tokens.get(platform, {})
        if not force_refresh and cache.get("access_token") and cache.get("expires_at", 0) > time.time() + 60:
            return cache["access_token"]
        refresh = cache.get("refresh_token") or c.get("refresh_token")
        if c.get("client_id") and c.get("client_secret") and refresh:
            status, body = _call("POST", token_url, form={
                "grant_type": "refresh_token", "refresh_token": refresh,
                "client_id": c["client_id"], "client_secret": c["client_secret"]})
            if status == 200 and isinstance(body, dict) and body.get("access_token"):
                with self._lock:
                    self._tokens[platform] = {
                        **cache,
                        "access_token": body["access_token"],
                        "refresh_token": body.get("refresh_token") or refresh,
                        "expires_at": time.time() + float(body.get("expires_in") or 3600),
                    }
                    self._save_tokens()
                return body["access_token"]
            raise _Fail(f"token refresh failed ({status}): {_why(body) or 'redo the OAuth step'}",
                        retry=status >= 500)
        if c.get("user_token") and not force_refresh:
            return c["user_token"]
        raise _Fail("no token set")

    def _authed(self, platform: str, token_url: str, method: str, url: str,
                headers: Callable[[str], Dict[str, str]], **kw) -> Tuple[int, Any]:
        """Call once; on 401 refresh the token and call again."""
        status, body = _call(method, url, headers=headers(self._token(platform, token_url)), **kw)
        if status == 401:
            try:
                tok = self._token(platform, token_url, force_refresh=True)
            except _Fail:
                raise _Fail(f"token rejected (401): {_why(body) or 'expired or revoked'}")
            status, body = _call(method, url, headers=headers(tok), **kw)
        return status, body

    # ---- twitch
    def _twitch(self, title: str) -> None:
        c = self.cfg.get("twitch") or {}
        if not c.get("client_id"):
            raise _Fail("no client id set (TWITCH_CLIENT_ID)")

        def hdrs(tok: str) -> Dict[str, str]:
            return {"Authorization": f"Bearer {tok}", "Client-Id": c["client_id"]}

        bid = c.get("broadcaster_id") or self._tokens.get("twitch", {}).get("broadcaster_id")
        if not bid:   # the token's own user: GET /users with no arguments
            status, body = self._authed("twitch", TWITCH_TOKEN, "GET", f"{TWITCH_API}/users", hdrs)
            users = (body or {}).get("data") if isinstance(body, dict) else None
            if status != 200 or not users:
                raise _Fail(f"could not look up the channel ({status}): {_why(body)}", retry=status >= 500)
            bid = users[0]["id"]
            with self._lock:
                self._tokens.setdefault("twitch", {})["broadcaster_id"] = bid
                self._save_tokens()
        status, body = self._authed(
            "twitch", TWITCH_TOKEN, "PATCH",
            f"{TWITCH_API}/channels?broadcaster_id={urllib.parse.quote(str(bid))}",
            hdrs, json_body={"title": title})
        if status != 204:
            raise _Fail(f"Twitch said {status}: {_why(body)}", retry=status >= 500)

    # ---- youtube
    def _youtube(self, title: str) -> None:
        c = self.cfg.get("youtube") or {}
        if not (c.get("client_id") and c.get("client_secret")):
            raise _Fail("no OAuth client set (YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET)")

        def hdrs(tok: str) -> Dict[str, str]:
            return {"Authorization": f"Bearer {tok}"}

        broadcast = None
        for state in ("active", "upcoming"):
            status, body = self._authed(
                "youtube", GOOGLE_TOKEN, "GET",
                f"{YOUTUBE_API}/liveBroadcasts?part=snippet&broadcastStatus={state}"
                "&broadcastType=all&maxResults=5", hdrs)
            if status != 200:
                raise _Fail(f"YouTube said {status}: {_why(body)}", retry=status >= 500)
            items = (body or {}).get("items") or []
            if items:
                broadcast = items[0]
                break
        if broadcast is None:
            raise _Fail("no live or upcoming broadcast yet", retry=True)
        snip = broadcast.get("snippet") or {}
        # update replaces the whole snippet: carry what's there, swap the title
        new = {"title": title, "description": snip.get("description", ""),
               "scheduledStartTime": snip.get("scheduledStartTime")}
        if snip.get("scheduledEndTime"):
            new["scheduledEndTime"] = snip["scheduledEndTime"]
        status, body = self._authed(
            "youtube", GOOGLE_TOKEN, "PUT", f"{YOUTUBE_API}/liveBroadcasts?part=snippet",
            hdrs, json_body={"id": broadcast["id"], "snippet": new})
        if status != 200:
            raise _Fail(f"YouTube said {status}: {_why(body)}", retry=status >= 500)

    # ---- kick
    def _kick(self, title: str) -> None:
        c = self.cfg.get("kick") or {}
        if not c.get("client_id") and not c.get("user_token"):
            raise _Fail("no token set (KICK_USER_TOKEN or KICK_CLIENT_ID + secret + refresh token)")

        def hdrs(tok: str) -> Dict[str, str]:
            return {"Authorization": f"Bearer {tok}", "Accept": "application/json"}

        status, body = self._authed("kick", KICK_TOKEN, "PATCH", f"{KICK_API}/channels",
                                    hdrs, json_body={"stream_title": title})
        if status not in (200, 204):
            raise _Fail(f"Kick said {status}: {_why(body)}", retry=status >= 500)


# --------------------------------------------------------------------------- OAuth helper
# `python -m autoclip title-auth twitch|youtube|kick` on a laptop: opens the
# platform's consent page, catches the redirect on localhost, prints the
# .env lines. Each needs an app registered with redirect URI
# http://localhost:8765/callback (Google: a "Desktop app" client needs none).
AUTH = {
    "twitch": ("https://id.twitch.tv/oauth2/authorize", TWITCH_TOKEN, "channel:manage:broadcast"),
    "youtube": ("https://accounts.google.com/o/oauth2/v2/auth", GOOGLE_TOKEN,
                "https://www.googleapis.com/auth/youtube.force-ssl"),
    "kick": ("https://id.kick.com/oauth/authorize", KICK_TOKEN, "channel:write"),
}


def oauth_login(platform: str, client_id: str, client_secret: str, port: int = 8765) -> dict:
    import base64
    import hashlib
    import http.server
    import secrets
    import webbrowser

    auth_url, token_url, scope = AUTH[platform]
    redirect = f"http://localhost:{port}/callback"
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    params = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect,
              "scope": scope, "state": state, "code_challenge": challenge,
              "code_challenge_method": "S256"}
    if platform == "youtube":
        params.update(access_type="offline", prompt="consent")   # or no refresh token
    got: Dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            if q.get("state") == state:
                got.update(q)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Done - back to the terminal.")

        def log_message(self, *a):  # quiet
            pass

    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    print(f"Opening {auth_url} ... if nothing opens, visit:\n{url}\n")
    webbrowser.open(url)
    with http.server.HTTPServer(("127.0.0.1", port), Handler) as srv:
        while "code" not in got and "error" not in got:
            srv.handle_request()
    if "error" in got:
        raise SystemExit(f"{platform} refused: {got.get('error_description') or got['error']}")
    status, body = _http("POST", token_url, form={
        "grant_type": "authorization_code", "code": got["code"], "redirect_uri": redirect,
        "client_id": client_id, "client_secret": client_secret, "code_verifier": verifier})
    if status != 200 or not isinstance(body, dict) or not body.get("refresh_token"):
        raise SystemExit(f"token exchange failed ({status}): {_why(body)}")
    return body
