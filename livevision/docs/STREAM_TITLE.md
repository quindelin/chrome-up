# Stream title — change it on the go

The companion app's **Status** tab has a *Stream title* field above the
restream toggles. **Save** sends it to every restream platform that has an
API for it and lists what each one said ("Twitch ✓ · YouTube: no OAuth
client set").

```
POST /api/autoclip/live/title  {"title": "Walking Shibuya at night", "platforms": ["twitch"]}
GET  /api/autoclip/live/title  -> {title, updated_at, results, platforms:[{name, supported, configured}]}
```

No `platforms` means every `live_streams` target. Each answer is
`{platform, ok, message}`, and tokens never appear in it. Missing
credentials give `ok: false` with a reason. They never raise an error.
Also: `python -m autoclip title "..."`, MCP `autoclip_live_title`, and a
`stream_title` event on the bus.

The last title is kept in `var/autoclip/title.json`. When a restream starts
later ("go live on twitch", the app's toggle), the title is applied to that
platform again. It retries after 30 s and 90 s while the platform is not
ready, for example while YouTube is still creating the broadcast.

| platform | API | what you need |
|---|---|---|
| Twitch | Helix `PATCH /helix/channels` | app + user token with `channel:manage:broadcast` |
| YouTube | Data API v3 `liveBroadcasts.update` (active, else upcoming broadcast) | Google OAuth client + refresh token, scope `youtube.force-ssl` |
| Kick | public API `PATCH /public/v1/channels` `stream_title` | app + user token with `channel:write` |
| X | none: X's Livestream API is not self-serve | set it in X Media Studio / Live Studio |
| Rumble | none: the Live Stream API is read-only | set it on rumble.com |

Titles are cut to Twitch 140, YouTube 100 and Kick 100 characters. The
result says when a title was cut.

## Getting the tokens

Every platform works the same way. You register an app once, run
`title-auth` on your laptop (it opens the consent page, catches the
redirect on `http://localhost:8765/callback` and prints the lines), then put
the values in the VM's `.env`:

```bash
cd livevision
python -m autoclip title-auth twitch --client-id ... --client-secret ...
cd deploy/obs-vps
./gcp.sh env TWITCH_CLIENT_ID          # prompts, hidden; re-runs setup
./gcp.sh env TWITCH_CLIENT_SECRET
./gcp.sh env TWITCH_REFRESH_TOKEN
```

autoclip refreshes the access tokens itself. Twitch and Kick replace the
refresh token on every refresh, so the newest one is kept in
`var/autoclip/title_tokens.json` (mode 0600, in the autoclip data volume).
Once that file exists, the `.env` value is only a fallback. If you revoke
access, run `title-auth` again and delete that file.

### Twitch

1. [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps) → Register
   Your Application. OAuth Redirect URL `http://localhost:8765/callback`,
   category *Broadcasting Suite*, client type *Confidential*.
2. Copy the Client ID and create a New Secret.
3. Run `title-auth twitch` and sign in as the channel owner.
4. In `.env`: `TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`,
   `TWITCH_REFRESH_TOKEN`. `TWITCH_BROADCASTER_ID` is optional because it
   is looked up from the token.

Shortcut: `TWITCH_CLIENT_ID` + `TWITCH_USER_TOKEN` (for example from
`twitch token -u -s channel:manage:broadcast` with the Twitch CLI) also
works, but that token expires after a few hours and there is no refresh.

### YouTube

1. [console.cloud.google.com](https://console.cloud.google.com) → enable
   **YouTube Data API v3** → Credentials → Create OAuth client ID → type
   **Desktop app**. Desktop clients accept any localhost redirect.
2. OAuth consent screen: add yourself as a test user. While the app is in
   *Testing*, Google expires refresh tokens after 7 days. Publish the app
   (it stays unverified, which is fine for your own account) so the token
   lasts.
3. Run `title-auth youtube` and pick the channel's account.
4. In `.env`: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`,
   `YOUTUBE_REFRESH_TOKEN`.

The title goes on the broadcast that is live right now. If nothing is live,
it goes on the next upcoming one. With the default "Stream now" key,
YouTube only creates the broadcast after video arrives, so the 30 s / 90 s
retries matter there. The clip uploader's token (`publish.youtube`) has
only the upload scope, so it can't be reused here.

### Kick

1. kick.com → Settings → Developer → Create App. Redirect URL
   `http://localhost:8765/callback`, scope **channel:write**.
2. Run `title-auth kick`. Kick requires PKCE, which the helper handles.
3. In `.env`: `KICK_CLIENT_ID`, `KICK_CLIENT_SECRET`, `KICK_REFRESH_TOKEN`
   (or a short-lived `KICK_USER_TOKEN`).

## Checking it

```bash
python -m autoclip title                         # configured: true per platform?
python -m autoclip title "test title" --platforms twitch
```

The stream HUD does not show the title on purpose. Viewers already see it
on every platform's page, and the HUD bars are full.
