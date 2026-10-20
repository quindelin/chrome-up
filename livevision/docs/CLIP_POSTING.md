# Clip posting from the companion app (design)

Status: design only, nothing here is built yet. Written 2026-10-20 against
`main` at 631f6d2. The stream-title work (98d4321) is on branch
`claude/cranky-golick-2d6006` and not merged yet. This design reuses its
patterns, so it assumes that branch lands first.

Goal: autoclip cuts a clip. You see it on the phone, fix the caption, pick
the platforms, tap **Post**, and see a link for each platform or the reason
it failed.

---

## 1. What exists today

### Server (autoclip on the VPS)

- `pipeline._run_cycle` renders each clip that scores at least
  `agent.auto_approve_score`. With `publish.mode: live` and
  `require_approval: true`, it copies the clip to `outbox/` and appends
  `{id, cycle, clip, platforms}` to `state["pending"]`.
- **With `mode: dry_run` (the VPS default) nothing is queued.** Clips go to
  `outbox/` and appear under `GET /clips`, but `GET /pending` stays empty.
  The queue and the posting kill switch are the same knob today. That is
  the first thing to split (§4.1).
- `approve(id, platforms)` removes the item from the queue *before*
  publishing. It then calls every publisher synchronously, in sequence, and
  returns the results to the caller only. Nothing persists them. If a post
  fails, the clip has already left the queue.
- `reject(id)` drops the item. Files are kept until retention removes them
  (`clip_hours: 48`, `max_clips_gb: 1.5` on the VPS). Retention never
  touches pending clips.
- You can't edit a clip's caption, title or hashtags after the agent writes
  them. `POST /publish` takes a caption, but only together with a raw
  `clip_path`.
- Auth: Caddy `basic_auth` on `/autoclip/*` (user `clips`,
  `AUTOCLIP_PASSWORD` in `.env`). `/autoclip/outbox/*` is public because
  Instagram fetches `video_url` from there. autoclip also has an optional
  `server.api_token` bearer check, which is off on the VPS.

Publishers (`autoclip/publishers/`):

| platform | how | credentials | works on the VPS today? |
|---|---|---|---|
| `local` | copies to `outbox/` with a `.json` sidecar | none | yes |
| `youtube` | Data API v3 `videos.insert` (google-api-python-client), scope `youtube.upload` | `client_secrets` JSON + cached `youtube_creds.json`. The first run calls `InstalledAppFlow.run_local_server`, which needs a browser | **no**: the image doesn't install `google-api-python-client`, and the browser flow can't run headless |
| `instagram` | Graph API `/{ig_user_id}/media` REELS container → poll → `media_publish`, `video_url` = public outbox URL | `INSTAGRAM_ACCESS_TOKEN` env + `ig_user_id` | yes (stdlib only), once the token and ID are set. Nothing refreshes the token |
| `x` | v1.1 `upload.twitter.com` chunked upload + v2 `POST /2/tweets`, OAuth 1.0a | 4 env vars | **no**: `requests-oauthlib` isn't in the image, and the v1.1 upload host it uses has been retired (see §3) |

Everything that publishes to a platform runs on the server, and the server
holds the credentials. That is the right shape. The gaps are packaging,
token handling and the async flow.

### Companion app

`ClipsView.swift` (the Clips tab) already does the minimum:

- polls `GET /api/autoclip/pending` and `/clips` every 30 s through
  `HUDClient` (basic auth from `Settings.user`/`password` in the Keychain)
- plays `outbox/<file>` with `AVPlayer`, with no login because the outbox is public
- **Post** → `POST /approve/{id}`, **Drop** → `POST /reject/{id}`

Problems:

- `HUDClient`'s session times out after 8 s. A real YouTube upload or an
  Instagram container poll (up to 300 s) runs far longer. The app shows an
  error while the server keeps posting, and the result is lost.
- The app discards the approve response (`_ = try await send(...)`), so
  there's no per-platform status.
- There's no caption editor and no platform picker.

### Stream-title pattern to reuse (98d4321)

`autoclip/stream_title.py` already solved credentials for Twitch, YouTube
and Kick:

- OAuth client ID/secret + **refresh token** in `.env`, set with
  `./gcp.sh env NAME` (hidden prompt, re-runs setup)
- `python -m autoclip title-auth <platform>` runs on the laptop. It opens
  consent, catches `http://localhost:8765/callback` and prints the `.env`
  lines.
- Access tokens refresh on the server. Rotated refresh tokens are kept in
  `<workdir>/title_tokens.json` with mode 0600.
- Platforms run in parallel and each answers `{platform, ok, message}`.
  Missing credentials give `ok: false`, never an exception. Tokens never
  appear in responses.
- `GET` lists `platforms: [{name, supported, configured}]` so the app can
  grey out what isn't set up.
- The companion app gets a field plus per-platform results.
  `StackClient` decodes with `convertFromSnakeCase`.

Clip posting should use the same token module and the same answer shape.
The YouTube refresh token from `title-auth youtube` uses scope
`youtube.force-ssl`, which `videos.insert` also accepts. **One Google
consent covers both titles and uploads.**

---

## 2. Proposed flow

```
autoclip cycle ─► pending (status: ready) ─► phone: Clips tab
                                              │ preview (AVPlayer, outbox URL)
                                              │ edit title / caption / hashtags
                                              │ toggle platforms (configured ones only)
                                              ▼
                         POST /clips/{id}/post  ──► 202 {job}
                                              │ server: per-platform worker threads
                                              ▼
                     poll GET /clips/{id} every 3 s (or SSE clip_status)
                     per platform: queued → uploading → processing → posted(url) | failed(msg)
                                              │
                     on-device-only targets (TikTok public, IG fallback):
                     download clip → Photos → share SDK / share sheet
```

### Phone screens (Clips tab)

1. **List**: one card per pending clip: thumbnail (`outbox/<stem>.jpg`, the
   render already writes it), title, duration, score, and badges for
   platforms already posted or failed. Swipe to Drop. A **Recent** section
   shows posted clips with their links.
2. **Detail** (push on tap):
   - `VideoPlayer` on the outbox URL, looping.
   - Fields: **Title** (YouTube, max 100), **Caption** (one text box with
     live per-platform counters: X 280, Instagram 2 200, TikTok 2 200,
     YouTube description 5 000), **Hashtags** chips. Use **Edit text** to
     save without posting.
   - **Post to** toggles, from `GET /platforms`. Platforms that aren't
     configured are greyed out with the reason ("no refresh token: run
     title-auth youtube"). Twitch is a separate action (§3).
   - YouTube privacy (`private / unlisted / public`, default from
     config). TikTok privacy has **no default**, as TikTok requires (§3).
   - **Post** button. It shows "Dry run" while `publish.mode` is `dry_run`,
     so a test tap is obvious.
3. **Status**: rows per platform with a spinner, then ✓ + **Open** (the URL)
   or ✗ + message + **Retry** (re-posts just that platform). The clip stays
   in the list until every selected platform has posted or you drop it.
4. Optional local notification when a post finishes while the app is in
   the background. The app polls when it comes back. No APNs needed.

### Where each platform posts from

| platform | path | why |
|---|---|---|
| **YouTube Shorts** | **server** (autoclip `youtube`) | Full API, no app review, cheap quota (see §3). No iOS SDK exists, and the YouTube app's share extension can't set title or privacy reliably. |
| **Instagram Reels** | **server** (autoclip `instagram`) | Already implemented. Works for your own professional account without app review. **Share-sheet fallback:** Meta's "Sharing to Reels" (`instagram-reels://share`) opens the Reels composer with the video, and you post by hand in Instagram. Useful if the Graph token lapses. |
| **X** | **server** (rewrite of `x` onto v2 media upload) | Server-side is the only API path. The iOS share sheet to X also works for a manual post. |
| **TikTok** | **iOS Share Kit** now; **server Direct Post** only after a TikTok audit | Unaudited Direct Post clients can only post `SELF_ONLY` (private), and the posting account itself must be private. Share Kit hands the video to the TikTok app, where you finish and post publicly. That needs no audit, but you have to complete the post in TikTok. |
| **Twitch clips** | **server**, but a different feature | Twitch has no API for uploading a video file as a clip. `POST /helix/clips` captures 5–60 s from the *live* broadcast. So it's a "Clip Twitch now" button (or voice `clip this`) while restreaming to Twitch, not a target for autoclip's renders. |
| **Facebook Reels, Kick, etc.** | out of scope | Can be added as publishers later with the same answer shape. |

---

## 3. Platform constraints (checked 2026-10-20)

**YouTube Data API v3, `videos.insert`.** Per the current reference page:
quota "100 calls per day … cost of 1 unit in the Video Uploads quota
bucket". It accepts the scopes `youtube.upload`, `youtube`,
`youtube.force-ssl` and `youtubepartner`. Max file size is 256 GB. The page
now says "Videos uploaded from unverified API projects are not restricted
to private viewing mode", so the old private-only lock for unaudited
projects is gone. Shorts are vertical or square videos up to 3 min. Add
`#Shorts` to the title or description for good measure. Google OAuth apps
left in *Testing* expire refresh tokens after 7 days, so publish the
consent screen as STREAM_TITLE.md already says. No app review is needed
for your own channel.
<https://developers.google.com/youtube/v3/docs/videos/insert>

**Instagram Graph API, Content Publishing.** Two login options:
*Instagram Login* (`graph.instagram.com`, scopes `instagram_business_basic`
and `instagram_business_content_publish`) or *Facebook Login for Business*
(`graph.facebook.com`, scopes `instagram_basic`,
`instagram_content_publish` and `pages_read_engagement`). Requires a
professional (Business or Creator) account. The limit is **100 API posts
per rolling 24 h**. `video_url` must be publicly fetchable when you
publish, which is why the outbox is public. Resumable upload
(`rupload.facebook.com`) is only available with Facebook Login. Reels
specs: MP4 or MOV with the moov atom at the front (autoclip already uses
`faststart`), H.264 or HEVC, 23–60 fps, 3 s–15 min, ≤ 300 MB, 9:16
recommended. The current code uses Facebook-Login Page tokens on
`graph.facebook.com`. Those are long-lived (~60 days) and nothing refreshes
them. **Recommendation:** move to Instagram Login and have autoclip
refresh the long-lived token (`GET /refresh_access_token`, any time after
24 h and before 60 days), saved to the same 0600 token file. Your own
account works with Standard access through app roles, with no App Review.
<https://developers.facebook.com/docs/instagram-platform/content-publishing>,
<https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media>

**Instagram "Sharing to Reels" (iOS).** A custom URL scheme
`instagram-reels` (add it to `LSApplicationQueriesSchemes`) plus a Meta
App ID in Info.plist. The video goes through `UIPasteboard` with a 5-min
expiry, and the Meta app must be live. You post by hand in Instagram.
Sample code: `fbsamples/share_to_reels_ios`.
<https://developers.facebook.com/docs/ios/sharing-to-reels-instagram/>

**X API v2 media upload.** The chunked flow is now
`POST /2/media/upload/initialize` → `/{id}/append` (≤ 5 MB chunks) →
`/{id}/finalize` → `GET /2/media/upload?command=STATUS`, then
`POST /2/tweets`. Auth is an OAuth 2.0 user token with `media.write` (plus
`tweet.write`, `users.read`, `offline.access` for posting and refresh), or
the OAuth 1.0a user context. The v1.1 `upload.twitter.com` endpoints that
`publishers/x.py` uses were retired for self-serve tiers in 2025. Video
limit for `tweet_video`: 20 min / 8 GB by default, so autoclip's 140 s trim
is now overly cautious. **Cost:** X moved to pay-per-use credits in 2026
(third-party sources consistently quote about $0.015 per post and $0.20
for posts that contain a URL). Check this in the Developer Console before
going live. Don't put links in captions sent to X.
<https://docs.x.com/x-api/media/quickstart/media-upload-chunked>,
<https://docs.x.com/x-api/media/initialize-media-upload>,
pricing as reported by <https://www.upload-post.com/x-api-pricing/>

**TikTok Content Posting API.** Scope `video.publish` (Direct Post) or
`video.upload` (send to the creator's inbox as a draft). **Unaudited
clients:** "All content posted by unaudited clients will be restricted to
private viewing mode", at most 5 users per 24 h, and the posting account
must be private. All clients have a creator cap of about 15 posts per day.
`PULL_FROM_URL` needs a verified domain or URL prefix. An `sslip.io` name
that changes with the VM IP won't survive verification, so use
`FILE_UPLOAD` (chunked PUT). Direct Post UX rules: fetch `creator_info`
and show the nickname, let the user pick privacy from
`privacy_level_options` **with no default**, comment/duet/stitch off until
the user turns them on, an editable caption, the commercial-content
disclosure toggle, a consent line linking the Music Usage Confirmation,
and **no watermarks or branding** added to the video. Note that the HUD
overlay isn't in autoclip clips: they come from the raw feed. The audit
reviews exactly this UI, so the iOS detail screen would have to follow
these rules.
<https://developers.tiktok.com/doc/content-posting-api-get-started>,
<https://developers.tiktok.com/doc/content-sharing-guidelines>

**TikTok Share Kit (iOS).** Shares `PHAsset` local identifiers (the app
needs Photos add access), a `client_key` from TikTok for Developers with
the Share Kit product added, and a universal-link `redirectURI`. The user
finishes in TikTok, which reports cancel (-2), failure (-3) or saved as a
draft. The quickstart doesn't mention a content audit for Share Kit, but
TikTok may still review the app when the product is added. Check this
when you register.
<https://developers.tiktok.com/doc/share-kit-ios-quickstart-v2>

**Twitch Helix `POST /helix/clips`.** Needs scope `clips:edit`. Captures
from the live stream only, between 5 and 60 s, and the channel must be
live with clips enabled. It returns `edit_url`, where the title is set by
hand. There's no upload of a file.
<https://dev.twitch.tv/docs/api/clips/>

---

## 4. Server changes

### 4.1 Queue independent of the kill switch

New knob `publish.queue: always | live_only` (default `always` on the
VPS). In `always`, every rendered clip lands in `pending`, whatever the
mode. `publish.mode` then only decides whether *approving* reaches the
platforms (`live`) or only the outbox (`dry_run`, with results marked
`dry_run: true`). Today's `approve()` forces `"mode": "live"`. Make it
respect `publish.mode` so the guardrail in AGENTS.md §6 holds when you
tap Post.

### 4.2 Pending item becomes a record with state

```json
{"id": "c123_0", "cycle": "c123", "created": 1760960000,
 "clip": {...}, "thumb_url": "outbox/c123_0.jpg", "video_url": "outbox/c123_0.mp4",
 "edits": {"title": "", "caption": "", "hashtags": [], "youtube_privacy": "unlisted"},
 "posts": {"youtube": {"state": "posted", "url": "https://youtu.be/…", "at": 1760960100},
           "x": {"state": "failed", "message": "403: …", "at": 1760960090}},
 "status": "ready | posting | done | partial | rejected"}
```

The record is kept in `state.json` (it is already locked by
`_state_lock`). An item leaves `pending` only when it is rejected or every
selected platform reaches `posted`. Posted items move to a `posted` list
(keep the last 50) so the app can show links.

### 4.3 Endpoints (under `/api/autoclip`, behind the same auth)

| method | path | body / answer |
|---|---|---|
| `GET` | `/platforms` | `{mode, platforms: [{name, path: "server"\|"device", configured, reason, limits: {caption, title, max_seconds}}]}`, the stream-title pattern |
| `GET` | `/pending` | (exists) now returns the records above |
| `GET` | `/clips/{id}` | one record, polled while posting |
| `PATCH` | `/clips/{id}` | `{title?, caption?, hashtags?, youtube_privacy?}` → record |
| `POST` | `/clips/{id}/post` | `{platforms: [...], title?, caption?, hashtags?}` → **202** with the record. Each platform runs in a thread. Already-posted platforms are skipped, so this call is also Retry |
| `POST` | `/clips/{id}/reject` | (= the existing `/reject/{id}`, keep both) |
| `GET` | `/posted` | recent posted records with URLs |
| `POST` | `/twitch/clip` | `{title?}` → Helix create clip → `{ok, url, edit_url}` (only while live on Twitch) |
| SSE | `/events` | (exists) add a `clip_status` event `{id, platform, state, url?, message?}` |

Keep `POST /approve/{id}` as a shim that calls `/clips/{id}/post`
synchronously, for the web page and MCP. Mirror the new operations in
`mcp_server.py`, `cli.py` and `/schema`, as the stream-title work did.

### 4.4 Publishers

- **Token module:** extract `stream_title.py`'s refresh and storage code
  into `autoclip/oauth_tokens.py` (one 0600 file, per-platform refresh).
  Both title and clip posting use it.
- **`youtube.py`:** drop `InstalledAppFlow`. Build `Credentials` from
  `YOUTUBE_CLIENT_ID`/`SECRET`/`REFRESH_TOKEN` (the same variables as the
  stream title) and call the REST resumable upload with `urllib`, so the
  image doesn't need the Google client libraries. Add `#Shorts` and set
  `privacyStatus` from the edits.
- **`instagram.py`:** support `graph.instagram.com` (Instagram Login) and
  refresh the long-lived token. Read `content_publishing_limit` before
  publishing and fail cleanly at 100 posts per day.
- **`x.py`:** move to `/2/media/upload/*`. Use OAuth 2.0 PKCE with refresh
  via `title-auth x` (scopes `tweet.write users.read media.write
  offline.access`), or keep OAuth 1.0a signing with stdlib `hmac` so
  `requests-oauthlib` isn't needed. Raise `max_seconds`.
- **`tiktok.py` (later, after an audit):** `FILE_UPLOAD` Direct Post with
  `creator_info` exposed through `/platforms` so the app can render
  TikTok's required UI. Until then, `/platforms` reports TikTok as
  `path: "device"`.
- **Twitch:** add a `create_clip()` helper next to the Twitch title code.
  Its refresh token needs `clips:edit` added to the `title-auth twitch`
  scopes.
- `title-auth` gains `x` and `instagram` and adds scopes (`clips:edit`).

### 4.5 Auth between the app and the server

Keep **Caddy basic auth**. The app already holds the password in the
Keychain, and HTTPS (Let's Encrypt on `sslip.io`) protects it. Posting is
the most dangerous call in the API, so add one guard: set
`server.api_token` (a new `AUTOCLIP_API_TOKEN` in `.env`, written into
`Secrets.xcconfig` by `gcp.sh companion`) and require it **only on the
mutating clip routes** (`PATCH`/`POST /clips/*`, `/twitch/clip`). A leaked
approval-page password then still can't post. That's optional for a
single-user box. Ask the user.

The outbox stays public because Instagram needs it. Filenames are cycle
IDs that can be guessed. If that matters, serve the outbox under a random
per-clip token path (`outbox/<hmac>/<file>`) and keep the public route
only for that.

---

## 5. App changes

| file | change |
|---|---|
| `HUDClient.swift` | record types (`PendingClip`, `PlatformPost`, `PlatformInfo`), `platforms()`, `clip(id)`, `edit(id, …)`, `post(id, platforms, …)` (decode 202), `posted()`. Separate session with a 30 s timeout for posts. Polling stays at 8 s |
| `ClipsView.swift` | list → `ClipDetailView` navigation. Thumbnail instead of a player per row. Status badges |
| `ClipDetailView.swift` (new) | player, caption editor with per-platform counters, platform toggles, YouTube privacy, Post / Retry / Drop, 3 s polling while `status == posting` |
| `ClipShare.swift` (new) | device path: download the outbox mp4 to a temp file → `PHPhotoLibrary` save → TikTok Share Kit (`TikTokOpenShareSDK` SPM) / Instagram `instagram-reels://share` / `UIActivityViewController` fallback |
| `Info.plist` / `Config` | `NSPhotoLibraryAddUsageDescription`, `LSApplicationQueriesSchemes` (`instagram-reels`, `tiktokopensdk`, `tiktoksharesdk`, `snssdk1233`), TikTok `client_key`, Meta App ID, universal link for the TikTok callback |
| `Settings.swift` | `apiToken` (Keychain) if §4.5's token is adopted |
| `Views.swift` (Status tab) | optional "Clip Twitch now" button next to the Twitch restream toggle |

Server files: `autoclip/pipeline.py` (queue knob, records, async post
workers, `posted` list), `autoclip/api.py` (§4.3), `autoclip/config.py` +
`autoclip.yaml` (`publish.queue`, per-platform defaults),
`autoclip/publishers/{youtube,instagram,x}.py`, new `tiktok.py` later,
`autoclip/oauth_tokens.py` (from `stream_title.py`), `autoclip/cli.py`
(`title-auth` scopes, `clips post`), `autoclip/mcp_server.py`,
`autoclip/approve.html` (caption box + per-platform status, optional),
`deploy/obs-vps/setup.sh` (`.env` placeholders `INSTAGRAM_*`,
`X_CLIENT_ID`, `X_REFRESH_TOKEN`, `AUTOCLIP_API_TOKEN`; drop the
`publish.queue` override), `deploy/obs-vps/autoclip.vps.yaml`,
`tests/smoke.py` (fake `_http` like the stream-title tests: queue in
dry_run, `PATCH` edits, post → per-platform states, retry skips posted,
missing creds → `failed` with a reason), and `AGENTS.md` §3/§6 + this doc.

---

## 6. Suggested order

1. Merge the stream-title branch, extract `oauth_tokens.py`.
2. Server: queue knob, records, `PATCH`/`post`/`clips/{id}`/`platforms`,
   async workers, smoke tests. Everything stays `dry_run`.
3. App: detail screen + status polling against dry_run. Results show
   `dry_run: true`.
4. YouTube via refresh token (stdlib) → flip `AUTOCLIP_PUBLISH=live` →
   post one unlisted Short.
5. Instagram Login token + refresh. X v2.
6. Device path: Share Kit + Reels share. Twitch "clip now".
7. TikTok Direct Post only if you want posting with no hands, and after
   TikTok's audit.

## 7. Open questions for the user

1. **Which platforms first?** YouTube + Instagram are cheap and server-side
   today. X now costs money per post. TikTok is phone-only (Share Kit)
   unless you apply for a TikTok audit.
2. **TikTok:** finishing each post in the TikTok app is fine, or do you
   want to go through the audit for hands-free public Direct Post?
3. **Instagram account:** is it Business or Creator, and linked to a
   Facebook Page? (This decides Instagram Login vs. the current Facebook
   Login token path.)
4. **Default YouTube privacy** for posted Shorts: `unlisted` (current
   config) or `public`?
5. **Second factor for posting** (§4.5 API token on the mutating routes),
   or is the basic-auth password enough?
6. **Twitch:** do you want "Clip Twitch now" (a live clip of the last
   5–60 s) as a separate button, given that Twitch can't take autoclip's
   rendered files?
7. **Caption length:** one caption for every platform with counters, or a
   separate caption per platform?
