"""Optional shared-key gate for a public deployment (Cloud Run).

Set LINGUALENS_KEY and every request - pages, API, static files and the
websocket - needs the key, given any one of three ways:

  ?key=<key>               once in the URL; answered with a cookie, so the
                           glasses Web App only needs it in the URL it opens
  X-LinguaLens-Key header  the native wrapper's HTTP client
  ll_key cookie            everything after the first page load

With no key set the gate is off (local use on your own network).
"""
from __future__ import annotations

import hmac
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

COOKIE = "ll_key"
OPEN_PATHS = {"/api/health"}          # uptime checks; reveals nothing private


class AccessKey:
    def __init__(self, app, key: str | None):
        self.app = app
        self.key = (key or "").strip()

    def _given(self, scope) -> tuple[str, bool]:
        """(key presented, came from the query string)"""
        qs = parse_qs((scope.get("query_string") or b"").decode("latin-1"))
        if qs.get("key"):
            return qs["key"][0], True
        headers = {k.decode("latin-1").lower(): v.decode("latin-1")
                   for k, v in scope.get("headers") or []}
        if headers.get("x-lingualens-key"):
            return headers["x-lingualens-key"], False
        if "cookie" in headers:
            c = SimpleCookie()
            try:
                c.load(headers["cookie"])
            except Exception:  # noqa: BLE001 - a malformed cookie is just "no key"
                return "", False
            if COOKIE in c:
                return c[COOKIE].value, False
        return "", False

    async def __call__(self, scope, receive, send):
        kind = scope.get("type")
        if not self.key or kind not in ("http", "websocket") or scope.get("path") in OPEN_PATHS:
            return await self.app(scope, receive, send)

        given, from_query = self._given(scope)
        if not hmac.compare_digest(given.encode(), self.key.encode()):
            if kind == "websocket":
                await send({"type": "websocket.close", "code": 4401})
                return
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"content-type", b"text/plain; charset=utf-8")]})
            await send({"type": "http.response.body",
                        "body": b"LinguaLens: open the link that includes ?key=..."})
            return

        if kind == "http" and from_query:
            cookie = (f"{COOKIE}={self.key}; Path=/; Max-Age=31536000; "
                      f"Secure; HttpOnly; SameSite=Lax").encode()

            async def send_with_cookie(message):
                if message["type"] == "http.response.start":
                    message = dict(message)
                    message["headers"] = list(message.get("headers") or []) + [(b"set-cookie", cookie)]
                await send(message)
            return await self.app(scope, receive, send_with_cookie)

        return await self.app(scope, receive, send)
