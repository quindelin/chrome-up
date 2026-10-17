# Cloud deployment — phone → RTMP → autoclip

This is the "phone is the source, VM does the work" path. The phone app
captures frames from the Meta Ray-Ban Display glasses via the DAT SDK and
pushes them upstream as an RTMP stream. A small always-on VM ingests the
stream, runs the full `autoclip` pipeline, and posts the clips.

```
[Ray-Ban Display] ──BLE/Wi-Fi──▶ [Phone: DAT app]
                                       │  RTMP push (cellular or Wi-Fi)
                                       ▼
                              ┌──────────────────┐
                              │  MediaMTX :1935  │   (public ingest, ~30 MB)
                              └──────────────────┘
                                       │  RTMP pull (same box)
                                       ▼
                              ┌──────────────────┐
                              │     autoclip     │   (FFmpeg + faster-whisper)
                              │  analyze→agent   │
                              │  render→publish  │
                              └──────────────────┘
```

## Why this shape

| option | source | pipeline | works anywhere? |
|---|---|---|---|
| phone does everything | phone | phone | ✗ battery/thermal/iOS-suspend |
| phone → laptop | phone | laptop | ✗ only at a desk |
| phone → home mini-PC | phone | mini-PC | only when home |
| **phone → cloud VM** | phone | cloud VM | **yes** |

The phone only does what phones are good at: receive from the glasses and
push a stream. Everything heavy (decode, Whisper, render, upload) runs on a
machine that's always on and never runs out of battery.

## What you need

- A small VPS: 2 vCPU, 4 GB RAM, 40 GB disk. Hetzner CCX13, Fly.io
  `shared-cpu-2x`, or RunPod CPU are all fine. **No GPU needed.**
- A public IP or hostname the phone can reach on port 1935 (RTMP).
- The `bluenviron/mediamtx` Docker image (pulls automatically).
- A long random `RTMP_STREAM_KEY` (treat as a password).

## Bring it up

```bash
cd deploy/cloud

# 1. set secrets
cp .env.example .env
# edit .env, set RTMP_STREAM_KEY=... (openssl rand -hex 16)
# optionally set OPENAI_API_KEY, social credentials

# 2. start
docker compose up -d --build

# 3. watch
docker compose logs -f
```

The compose file runs two containers:

| service | image | role | ports |
|---|---|---|---|
| `mediamtx` | `bluenviron/mediamtx:v1.10.0` | public RTMP ingest | 1935 |
| `autoclip`  | built from this repo            | pipeline: subscribe + analyze + publish | (internal) |

`autoclip` subscribes back to the **same** RTMP URL the phone publishes to,
segments the stream into 30-second `.ts` files under `var/autoclip/incoming/`,
and feeds them through the rolling window. Everything downstream is the
existing `autoclip` pipeline — no new code paths.

## Phone app contract

The phone app's only job: pull frames from the DAT SDK and push them as
RTMP. See [`docs/PHONE_APP.md`](../../docs/PHONE_APP.md) for the exact
Swift / Kotlin snippets, the publish URL, and what NOT to do (don't try to
transcribe on the phone, don't keep ffmpeg running in the background).

## How the bits fit

| config key | purpose |
|---|---|
| `source.mode: rtmp` | tells `autoclip` to subscribe to a live RTMP feed |
| `source.rtmp.url`  | where to subscribe (default `rtmp://127.0.0.1:1935/live`) |
| `source.rtmp.stream_key` | appended to `url`; the path the phone publishes to |
| `source.rtmp.dir`  | where the ffmpeg chunker writes 30 s `.ts` files |
| `source.rtmp.chunk_seconds` | how big each `.ts` chunk is |

The autoclip config is a copy of the project-root `autoclip.yaml`; the RTMP
block at the top is what differs from a local OBS install.

## Verifying it works without the phone

```bash
# 1. publish a test stream from your laptop
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
       -f lavfi -i sine=frequency=440 \
       -c:v libx264 -preset ultrafast -tune zerolatency \
       -c:a aac -f flv rtmp://127.0.0.1:1935/live/testkey

# 2. in another shell
docker compose exec autoclip python -m autoclip status
# expect source.mode == "rtmp" and incoming/ has .ts files appearing
```

## Live multi-streaming

The VM can also re-broadcast the POV stream to YouTube / Twitch / Kick / X
simultaneously, with each platform startable by voice ("go live on
twitch"). Set `LIVE_STREAMS_ENABLED=1` and the platform keys in `.env`,
then `docker compose restart autoclip`. See
[`docs/LIVE_STREAMING.md`](../../docs/LIVE_STREAMING.md).

Bandwidth note: each live platform costs one full upstream copy of the
stream (~2.5 Mbps each). VM links are unmetered, so 3–5 platforms is fine.

## Out-of-band control

Optional. The `server.enabled: true` block in `autoclip.yaml` exposes a
REST + OpenAPI surface on port 8899 so you can review/approve/reject clips
from a browser. Recommended for live publishing.

```bash
# from the host
curl -s http://127.0.0.1:8899/pending
curl -s -X POST http://127.0.0.1:8899/approve/<id>
```

## Cost ballpark

| item | cost |
|---|---|
| Hetzner CCX13 (2 vCPU / 4 GB) | ~€8 / mo |
| RunPod CPU 2x4 GB | ~$20 / mo |
| Fly.io shared-cpu-1x, 24/7 | ~$7 / mo |
| Domain (optional) | $12 / yr |
| outbound bandwidth (1 GB clips/day) | included or ~$0 |

Cheapest viable setup: **~$7-20 / month**, no GPU, no queue, no managed
service. The `autoclip` container uses ~1-2 GB RAM at idle (a few hundred
MB if you skip `faster-whisper`).

## Security

This config is **open on purpose** for development. Before exposing to the
public internet:

1. Generate a strong `RTMP_STREAM_KEY` (32+ bytes, see `.env.example`).
2. Run MediaMTX behind TLS — either terminate at a reverse proxy or use
   the SRT/WHIP protocols (`rtspAddress: :8322`, `webrtcAddress: :8889`)
   in `mediamtx.yml` instead of plain RTMP.
3. Enable `authMethod: internal` in MediaMTX and create a user.
4. Set `server.api_token` in `autoclip.yaml` and require a bearer token on
   the REST API.
5. Bind the RTMP listener to a specific public IP, not `0.0.0.0`, if the
   VPS has more than one.

## Scaling beyond one user

For multiple streamers, give each user a different RTMP path (e.g.
`rtmp://host:1935/live/alice-secretkey`, `…/bob-secretkey`). MediaMTX will
fan out each publisher to all viewers; each `autoclip` instance subscribes
to a different key, so they don't see each other's footage. One VM per
user is the simplest — they each get a 2 vCPU / 4 GB box and run the same
compose file with a different `RTMP_STREAM_KEY`.
