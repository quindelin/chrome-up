# Clip posting from the companion app

autoclip cuts clips. You review them in the LiveVision app's **Clips** tab,
fix the caption, pick platforms and post:

| platform | posted by | how |
|---|---|---|
| YouTube Shorts | the VPS (autoclip `youtube`) | Data API v3 upload, **public** by default |
| Instagram Reels | the VPS (autoclip `instagram`) | Graph API (Facebook Login, Page token) |
| TikTok | the phone | Share Kit opens TikTok with the clip; you finish the post there |
| X | the phone | share sheet → X's composer with the clip and the caption, as a draft |

Twitch clips aren't supported (Twitch can't take an uploaded file).

---

## 1. On the phone

**Clips** tab:

- **Waiting for you**: every clip autoclip rendered, with thumbnail, title,
  caption, length, score and a chip per platform it already went to. Swipe
  to drop one.
- Tap a clip to watch it (looping), then edit **Title** (YouTube),
  **Caption** and **#hashtags**. One caption serves every platform. The
  footer counts it per selected platform (YouTube title 100, Instagram
  2 200, TikTok 2 200, X 280) and flags anything over the limit.
- **Post to**: YouTube and Instagram are on when the VPS has their
  credentials. Otherwise they're greyed out with what's missing. TikTok and
  X are off until you turn them on. YouTube gets a visibility picker
  (public by default).
- **Post**: the VPS answers at once and uploads in the background. The
  **Status** section shows *waiting → uploading → posted* (with **Open**)
  or *failed* with the platform's reason and **Retry**. Retry only re-posts
  what failed.
- TikTok and X open after the VPS has started. The caption is copied to
  the clipboard, because TikTok doesn't take one from apps. TikTok gets the
  clip through Photos (LiveVision asks to *add* to Photos once). If TikTok
  doesn't report back (see §3), the row says *not confirmed* and has
  **Mark posted** and **Share again**.
- A clip moves to **Posted** once every platform you sent it to is done.
- While the VM is in `dry_run`, a banner says so, and "posted" means
  *copied to the VPS outbox* (shown as *dry run ✓*).

## 2. How it works (server)

- **The queue doesn't depend on the kill switch.** `publish.queue: always`
  (the default) queues every rendered clip, `dry_run` or not.
  `publish.mode` (`AUTOCLIP_PUBLISH` on the VM) then only decides whether
  Post reaches YouTube and Instagram. `approve` no longer forces `live`.
  `queue: live_only` brings back the old behaviour, where dry_run clips go
  straight to the outbox.
- `autoclip/posting.py` `ClipPoster` keeps each queue item as a record in
  `state.json`:

  ```json
  {"id": "3f9c…_0", "cycle": "3f9c…", "clip": {...}, "platforms": ["youtube", "instagram"],
   "edits": {"title": "...", "caption": "...", "hashtags": ["..."], "youtube_privacy": "public"},
   "posts": {"youtube": {"state": "posted", "url": "https://youtube.com/shorts/…", "message": "uploaded"},
             "tiktok": {"state": "shared"}},
   "status": "ready | posting | partial | done", "video_url": "outbox/….mp4", "thumb_url": "outbox/….jpg"}
  ```

  Each server platform posts on its own thread: `queued → uploading →
  posted | dry_run | failed`. Posts that were in flight when the container
  restarted come back as `failed`, and Post retries them. Every change also
  goes on the event bus as `clip_status` (SSE `/events`). Done records move
  to `posted` (last 50).
- Retention never deletes a clip that is still in the queue.

### REST (behind Caddy basic auth, `https://$DOMAIN/autoclip/…`)

| method | path | body → answer |
|---|---|---|
| GET | `/api/autoclip/platforms` | `{mode, platforms: [{name, path: server\|device, configured, reason, limits}], youtube_privacy, youtube_privacy_options}` |
| GET | `/api/autoclip/pending` | `{pending: [record]}` |
| GET | `/api/autoclip/posted` | `{posted: [record]}`, newest first |
| GET | `/api/autoclip/clips/{id}` | record (the app polls this every 2 s while posting) |
| PATCH | `/api/autoclip/clips/{id}` | `{title?, caption?, hashtags?, youtube_privacy?}` → record |
| POST | `/api/autoclip/clips/{id}/post` | `{platforms?, title?, caption?, hashtags?, youtube_privacy?}` → **202** record. Only `youtube`/`instagram`; posted ones are skipped |
| POST | `/api/autoclip/clips/{id}/shared` | `{platform: tiktok\|x, state: shared\|cancelled\|failed, message?}` → record |
| POST | `/api/autoclip/clips/{id}/reject` | `{rejected: bool}` |
| POST | `/api/autoclip/approve/{id}` | as before: posts and waits, returns `{results}` (web page, scripts) |

Errors are `404` (no such clip) and `422` with a `detail` the app shows.
Also: MCP `autoclip_platforms` and `autoclip_clip_post`, and CLI
`python -m autoclip post <id> --platforms youtube --caption "…"`.

Auth is the approval-page password (`AUTOCLIP_PASSWORD`, already in the app
from `gcp.sh companion`). There's no second factor for posting. The outbox
stays public because Instagram fetches the video from it.

## 3. Setup

Everything goes in the VM's `.env` with `./gcp.sh env NAME`. It prompts
with the input hidden and re-runs setup. Run these from
`livevision/deploy/obs-vps` while the VM is running. Then redeploy once so
the image picks up the Google client libraries: `./gcp.sh deploy`.

### YouTube Shorts

The same Google OAuth client and refresh token as the stream title
([STREAM_TITLE.md](STREAM_TITLE.md)). If you already set those up, there's
nothing to do. Otherwise:

1. console.cloud.google.com → enable **YouTube Data API v3** → OAuth client
   ID, type **Desktop app**. On the consent screen, add yourself and
   **publish the app**: refresh tokens from apps left in *Testing* expire
   after 7 days.
2. On the laptop, from `livevision/`:
   `python -m autoclip title-auth youtube --client-id … --client-secret …`
   (scope `youtube.force-ssl`, which also covers uploads).
3. `./gcp.sh env YOUTUBE_CLIENT_ID`, `./gcp.sh env YOUTUBE_CLIENT_SECRET`,
   `./gcp.sh env YOUTUBE_REFRESH_TOKEN`.

Quota: 100 uploads per day. Shorts are public unless you pick otherwise
per clip. `publish.youtube.privacy` in `autoclip.yaml` sets the default.

### Instagram Reels (Business account linked to a Facebook Page)

1. developers.facebook.com → create an app (type *Business*), add the
   **Instagram** product. You're an app admin, so no App Review is needed
   for your own account.
2. Graph API Explorer → that app → *User Token* with `instagram_basic`,
   `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement` (and `business_management` if the Page is in a
   Business Portfolio) → copy the short-lived token.
3. On the laptop, from `livevision/`:
   `python -m autoclip ig-token --app-id <APP_ID>`. It prompts, hidden,
   for the app secret and the token. It turns them into a Page token that
   **doesn't expire** and prints `INSTAGRAM_USER_ID` and
   `INSTAGRAM_ACCESS_TOKEN`. Use `--page "Name"` if you run several Pages.
4. `./gcp.sh env INSTAGRAM_USER_ID`, `./gcp.sh env INSTAGRAM_ACCESS_TOKEN`.

Instagram fetches the clip from `https://$DOMAIN/autoclip/outbox/…`, so the
VM must be reachable when you post. The limit is 100 API posts per day.

### TikTok (Share Kit, on the phone)

1. developers.tiktok.com → Manage apps → create an app, add **Share Kit**,
   and register the iOS bundle id (`com.chromeup.livevision` or yours).
   Copy the **Client key**.
2. In `companion/ios/Config/Secrets.xcconfig`:
   `TIKTOK_CLIENT_KEY = <client key>`. `gcp.sh companion` keeps this line
   when it rewrites the file.
3. Build. Xcode resolves the `tiktok-opensdk-ios` 2.5.0 package.

Without a client key, TikTok goes through the share sheet instead, and you
finish there in the same way.

Share Kit's callback goes to `https://$DOMAIN/autoclip/tiktok`. Without a
universal link, that page opens in Safari ("Back to LiveVision"), and the
app asks you to **Mark posted**. To get the result back automatically:
add the *Associated Domains* capability (`applinks:<your host>`), serve
`/.well-known/apple-app-site-association` from Caddy, and register the
link in the TikTok app settings. That works best with a static IP
(`STATIC_IP=1`), because the sslip.io host follows the IP.

### X

Nothing to set up. X opens from the share sheet with the clip and the
caption, and you post from X. No paid API is involved.

### Going live

`./gcp.sh env AUTOCLIP_PUBLISH live`. Until then every Post is a dry run.

## 4. Platform constraints (checked 2026-10-20)

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
recommended. autoclip uses the Facebook Login path with a Page token made
from a long-lived user token (`ig-token`). Such Page tokens don't expire,
so nothing has to refresh them. A password change or revoking the app
invalidates them, and then you rerun `ig-token`. Your own account works
with Standard access through app roles, with no App Review.
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


## 5. Not done / possible next steps

- TikTok Direct Post from the VPS (needs TikTok's audit; until then API
  posts can only be private).
- Universal link for TikTok's callback (see §3).
- X posting from the VPS: `publishers/x.py` still uses the retired v1.1
  upload and X now charges per post. Phone drafts replace it.
- Twitch "clip now" (`POST /helix/clips`, live only).
