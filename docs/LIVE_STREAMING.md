# Live multi-streaming — one POV feed, N platforms, voice-controlled

This doc covers the **live** path: re-broadcasting the glasses' POV stream
to YouTube / Twitch / Kick / X / anything-with-an-RTMP-endpoint at the same
time, and starting/stopping each one by voice.

This is separate from **clip publishing** (posting a finished 10–30 s clip
to Instagram / Shorts / X), which is what `publish:` in `autoclip.yaml`
already does. Both can run at once.

```
                                   ┌─▶ ffmpeg ─▶ rtmp://youtube/live2/<key>
[glasses] ─▶ [phone] ─▶ MediaMTX ──┼─▶ ffmpeg ─▶ rtmp://twitch/app/<key>
             RTMP        :1935     ├─▶ ffmpeg ─▶ rtmp://kick/app/<key>
                                   └─▶ ffmpeg ─▶ rtmp://x/<key>
                                        │
                                        └─▶ (also) autoclip rolling window
                                             → analyze → clip → publish
```

One source, one ffmpeg republisher per platform, all `-c copy` so no
re-encode and no A/V drift.

---

## 1. Config

```yaml
live_streams:
  enabled: true
  # What the republishers pull from. On the cloud VM this is the local
  # MediaMTX; with OBS it's OBS's RTMP output.
  source: "rtmp://127.0.0.1:1935/live/${RTMP_STREAM_KEY:-glasses}"
  max_restarts: 5
  restart_backoff_seconds: 5
  targets:
    - name: youtube
      url: "rtmp://a.rtmp.youtube.com/live2"
      key: "${YOUTUBE_STREAM_KEY}"
      enabled: false
    - name: twitch
      url: "rtmp://live.twitch.tv/app"
      key: "${TWITCH_STREAM_KEY}"
      enabled: false
```

`${VAR}` is expanded from the environment at config load — see
`docs/PHONE_APP.md` for why keys live in env vars, not YAML.

`enabled: false` on a target means "configured but not live". Only
`live_streams.enabled: true` spawns the manager at all; with it false no
ffmpeg process and no watchdog thread is created, so the pipeline is
untouched.

**Auto-resume:** the manager persists the active set to
`var/autoclip/live/state.json`. Restart autoclip and it resumes whichever
platforms were live before (set them `enabled: true` in YAML for a
permanent default).

---

## 2. Per-platform ingest URLs

Already in `autoclip/livestream.py:PLATFORM_INGESTS`, so you can omit
`url:` and just give a name:

| `name` | ingest URL | where the key comes from |
|---|---|---|
| `youtube` | `rtmp://a.rtmp.youtube.com/live2` | YouTube Studio ▸ Go Live ▸ Stream key. **Persistent** — reuse forever. |
| `twitch` | `rtmp://live.twitch.tv/app` | Twitch Creator Dashboard ▸ Settings ▸ Stream Key. **Rotate it** — treat as a password. |
| `kick` | `rtmp://ingest.kick.com/app` | Kick Dashboard ▸ Settings ▸ Stream Key |
| `x` | `rtmp://ingest.pscp.tv:80/x/` | X Media Studio |
| `facebook` | `rtmp://live-api-s.facebook.com:80/rtmp/` | Live Producer ▸ Stream key |
| `instagram` | `rtmp://live-upload.instagram.com:80/rtmp/` | ⚠️ Instagram Live **restricts** bare RTMP — mostly US-only via the app. Test before relying on it. |
| `tiktok` | `rtmp://push-rtmp-l11-va01.tiktok.com:80/live/` | ⚠️ TikTok Live requires the app + 1k followers. Not reliable over bare RTMP. |

For a self-hosted relay, Restream, or anything else, add a `custom` target
with its own `url`. The manager doesn't care what the URL points at.

**Regional ingest:** Twitch and YouTube have regional ingest hosts
(e.g. `rtmp://live-sfo.twitch.tv/app`). If you see "connection reset"
errors, override `url` with the nearest one.

---

## 3. Voice commands

The regex parser in `autoclip/voice.py` recognises these. All
case-insensitive.

| spoken | intent | target |
|---|---|---|
| `go live on twitch` | `stream` | `twitch` |
| `live on youtube` | `stream` | `youtube` |
| `start streaming on kick` | `stream` | `kick` |
| `start twitch` | `stream` | `twitch` |
| `go live everywhere` | `stream` | `all` |
| `go live on all platforms` | `stream` | `all` |
| `stop streaming to youtube` | `unstream` | `youtube` |
| `stop twitch` | `unstream` | `twitch` |
| `end the youtube stream` | `unstream` | `youtube` |
| `stop all streams` | `unstream` | `all` |

Aliases are resolved by `resolve_name()`: `yt`→youtube, `twitter`→x,
`ttv`→twitch, `fb`→facebook, `ig`/`insta`→instagram.

**Safety:** a `stream` intent only fires for a name in
`live_streams.targets`. "Go live on myspace" produces
`{"ok": false, "message": "unknown target"}` rather than spawning ffmpeg.
A target with a missing stream key refuses to start with
`"missing url or stream key for 'youtube'"` — so an unset
`${YOUTUBE_STREAM_KEY}` can't accidentally go live.

### How the command reaches ffmpeg

```
transcript → voice parser → StreamEvent{intent=stream,target=twitch}
                                  │
                          EventBus (events.jsonl + SSE)
                                  │
                          CommandDispatcher (background thread)
                                  │
                          LiveStreamManager.start("twitch")
                                  │
                          ffmpeg -c copy -f flv rtmp://live.twitch.tv/app/<key>
                                  │
                          StreamEvent{type=stream_status, target=twitch}
                                  │
                          back on the bus → HUD draws "Twitch: LIVE"
```

The dispatcher also publishes a `stream_status` event, so the HUD agent can
render a per-platform live indicator without polling.

---

## 4. Control surfaces

All three do the same thing; pick whichever fits.

### REST

```bash
curl -s localhost:8899/api/autoclip/live                    # status per platform
curl -XPOST localhost:8899/api/autoclip/live/start/twitch
curl -XPOST localhost:8899/api/autoclip/live/stop/youtube
curl -XPOST localhost:8899/api/autoclip/live/start_all
curl -XPOST localhost:8899/api/autoclip/live/stop_all
```

### CLI

```bash
python -m autoclip live                  # status
python -m autoclip live start twitch
python -m autoclip live stop youtube
python -m autoclip live start-all
python -m autoclip live stop-all
```

### MCP (for the HUD agent)

Tools: `autoclip_live_status`, `autoclip_live_start`, `autoclip_live_stop`.
Pass `name: "all"` to start/stop every target.

```json
{"name": "autoclip_live_start", "arguments": {"name": "twitch"}}
```

### Manual injection (tests, hotkeys)

```bash
curl -XPOST localhost:8899/api/autoclip/command \
  -H "Content-Type: application/json" \
  -d '{"text":"go live on twitch", "intent":"stream", "target":"twitch"}'
```

This goes through the same bus, so the dispatcher picks it up.

---

## 5. A/V sync on the re-stream

Each republisher is:

```
ffmpeg -nostdin -hide_banner -loglevel warning \
       -i rtmp://127.0.0.1:1935/live/glasses \
       -c copy -f flv rtmp://live.twitch.tv/app/<key>
```

- **`-c copy`** — no re-encode, so the PTS the phone stamped survives all
  the way to Twitch. This is the single most important flag. Any
  re-encode re-stamps from ffmpeg's clock and you lose sync.
- **no `-re`** — that flag throttles *file* input. On a live network source
  ffmpeg already paces itself, and `-re` can stall the relay.
- **`-f flv`** — every RTMP ingest expects FLV-muxed H.264/AAC.
- **`-nostdin`** — without it, ffmpeg can inherit stdin and hang when the
  parent process is a service.

The phone's keyframe interval (2 s, see
[`AUDIO_VIDEO_SYNC.md`](AUDIO_VIDEO_SYNC.md)) also matters here: platforms
need a keyframe at the start of the connection or the first seconds are
black. 2 s guarantees this.

**Bandwidth.** Each active platform costs you a full upstream copy. At
2.5 Mbps:

| platforms live | upstream from the VM |
|---|---|
| 1 | 2.5 Mbps |
| 3 | 7.5 Mbps |
| 5 | 12.5 Mbps |

Most cloud VMs have 100+ Mbps unmetered, so this is fine. Watch it if you
run the VM at home or on a metered link.

---

## 6. Watchdog + failure modes

The manager runs a background thread every 2 s:

- If an enabled target's ffmpeg has died, read the last ~8 lines of
  `var/autoclip/live/<name>.log` into `status().last_error` and restart
  (backoff 5 s, max 5 restarts).
- If a target is enabled but has no process, start one.

Common failures and what they mean:

| `last_error` | cause | fix |
|---|---|---|
| `Connection refused` | MediaMTX isn't up, or the phone isn't publishing | check `docker compose ps`, check the phone |
| `Server error: Not authorized` | bad stream key | re-copy from the platform dashboard |
| `Invalid data` / `Error muxing` | source has no audio track, or codec isn't H.264+AAC | make sure the phone publishes both; check `source` codecs |
| exit code 1 immediately | `source` URL wrong | `ffprobe` the source URL by hand |

Logs: `var/autoclip/live/<platform>.log`, one per target.

---

## 7. Guardrails

- **`live_streams.enabled` defaults to `false`.** No ffmpeg, no thread, no
  network, until you turn it on.
- **Targets default to `enabled: false`.** Nothing goes live on boot unless
  you explicitly set it.
- **Missing key ⇒ refuse to start.** `${UNSET_KEY}` expands to `""`, and
  `start()` returns `{"ok": false, ...}` rather than trying to connect.
- **`status()` never leaks keys.** It reports `key_set: bool` only. The
  full RTMP URL with key is never logged or returned.
- **Unknown platforms are ignored.** "Go live on myspace" is a no-op with a
  logged reason.

Going live on the wrong platform is embarrassing and hard to undo (viewers
get notified). The defaults are conservative on purpose.

---

## 8. Smoke test

```bash
# 1. enable + set keys in deploy/cloud/.env
LIVE_STREAMS_ENABLED=1
TWITCH_STREAM_KEY=live_123_abc

# 2. confirm the manager sees the targets
python -m autoclip live
# expect: enabled: true, one entry per target, key_set: true for twitch

# 3. push a test source into MediaMTX
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
       -f lavfi -i sine=frequency=440 \
       -c:v libx264 -preset ultrafast -g 60 -c:a aac -ar 48000 \
       -f flv rtmp://127.0.0.1:1935/live/glasses

# 4. go live by voice (or REST)
curl -XPOST localhost:8899/api/autoclip/live/start/twitch
python -m autoclip live          # twitch: active, pid set, uptime climbing

# 5. or inject the voice event and watch the dispatcher do it
curl -XPOST localhost:8899/api/autoclip/command \
  -H "Content-Type: application/json" \
  -d '{"text":"go live on twitch", "intent":"stream", "target":"twitch"}'

# 6. stop
curl -XPOST localhost:8899/api/autoclip/live/stop/twitch
```

To test the manager without any real endpoints, point a target at a local
MediaMTX path — it accepts the publish and you can watch it with `ffplay`.

---

## 9. What's deliberately not here

- **Adaptive bitrate / transcoding.** Each platform gets the same bitrate
  the phone pushed. Real multi-streaming services transcode per platform;
  we don't, because `-c copy` is what preserves sync. If you need a
  1080p Twitch + 720p YouTube split, add two targets with a
  `-vf scale=1280:720 -c:v libx264` `extra_args` on one — accepting the
  re-encode cost on that one leg only.
- **Chat / title / category updates.** Out of scope; those are platform
  REST APIs and belong in a separate integration.
- **Simulcast to non-RTMP.** SRT and WHIP targets would need a different
  muxer. RTMP covers every mainstream platform today.
