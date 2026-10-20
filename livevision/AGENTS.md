# AGENTS.md — autoclip

> You are an agent working in this repo. This file is the contract for
> `autoclip/`: a rolling-buffer clip pipeline that watches a POV stream, decides
> what is worth posting, cuts it, captions it, and publishes it.
>
> **Read this before touching `autoclip/`.** It is written so *any* agent
> (Claude Code, Codex, Copilot, Cursor, Muse, a custom bot, an MCP client) can
> drive the pipeline without reading the source.

---

## 1. What it does

```
OBS (or glasses) ──► rolling 5-min buffer ──► local signal analysis ──► AGENT decides
                                                                            │
                                        ffmpeg cut + reframe + burn captions ─┘
                                                     │
                                        YouTube / Instagram / X (or outbox)
```

The "editor" is a pluggable agent. Everything else is deterministic plumbing.

---

## 2. Install / first run

```bash
brew install ffmpeg                 # required, not a pip package
./run_autoclip.sh doctor            # verify ffmpeg, OBS, optional deps
python tests/smoke.py               # 10 checks, no ffmpeg needed
./run_autoclip.sh run               # one cycle
```

With no OBS and no footage it degrades cleanly: `run` returns a cycle with notes
explaining why nothing was captured. Never crashes on missing hardware.

---

## 3. Three ways an agent can drive it

### A. MCP (preferred — native tools)

```bash
python -m autoclip mcp --list-tools     # print tool metadata
```

Register in any MCP client:

```json
{
  "mcpServers": {
    "autoclip": {
      "command": "python",
      "args": ["-m", "autoclip.mcp_server", "--config", "autoclip.yaml"]
    }
  }
}
```

Tools (all return JSON text):

| tool | args | returns |
|---|---|---|
| `autoclip_status` | – | source, buffer depth, agent, publish mode |
| `autoclip_window` | – | materialized window `{path, start_wall, duration}` |
| `autoclip_analyze` | `window_path?`, `with_frames?` | per-second signals, moments, transcript, frames |
| `autoclip_propose` | `window_path?`, `agent?` | the agent's clip decisions |
| `autoclip_render` | `window_path`, `start`, `end`, `title?`, `caption?`, `platforms?` | clip + srt + thumb |
| `autoclip_publish` | `clip_path`, `platforms?`, `live?` | per-platform results |
| `autoclip_run` | `agent?`, `publish?` | one full cycle |
| `autoclip_clips` | – | clips produced so far |
| `autoclip_pending` / `autoclip_approve` | `id`, `platforms?` | approval queue |
| `autoclip_events` | – | **SSE stream** of `voice_command` + `transcript_chunk` events for HUD agents |
| `autoclip_events_history` | `n?`, `type?` | last N events (JSON, for polling) |
| `autoclip_command` | `text`, `intent?`, `target?`, `value?` | inject a voice event manually |
| `autoclip_live_status` | – | per-platform live streaming status |
| `autoclip_live_start` / `_stop` | `name` | start/stop one platform (`all` = every target) |
| `autoclip_obs_status` | – | OBS scenes, sources, armed voice intents |
| `autoclip_obs_command` | `intent`, `target?`, `value?` | drive OBS directly (scene/mute/volume/record/…) |

**Recommended loop for an agent:** `status` → `window` → `analyze` →
`propose` (or decide yourself from `analyze`) → `render` → `publish`.

### B. REST + OpenAPI

```bash
./run_autoclip.sh serve                      # http://127.0.0.1:8899/docs
curl -s localhost:8899/api/autoclip/schema   # machine-readable operation list
curl -s -XPOST localhost:8899/api/autoclip/run
```

`GET /api/autoclip/schema` is self-describing — fetch it first if you are an
agent that has never seen this repo.

### C. CLI

```bash
./run_autoclip.sh status | window | analyze | propose | render | publish | run | loop
./run_autoclip.sh pending | approve <id> | reject <id>
./run_autoclip.sh live status|start|stop|start-all|stop-all
./run_autoclip.sh obs | obs <intent> [target] [value]
```

---

## 4. Plugging in your own "editor" agent

A decision is just this. Times are **seconds from the start of the window**:

```json
{"start": 42.0, "end": 71.5, "score": 0.83,
 "title": "…", "caption": "…", "hashtags": ["…"],
 "platforms": ["youtube","instagram","x"], "hook": "…", "why": "…"}
```

Return `{"clips": [...]}` (or a bare list). Malformed entries are repaired, not
rejected: short clips get padded, long clips get trimmed, `null`s get defaults.
**Returning `{"clips": []}` is a valid, encouraged answer.**

## 3b. Voice commands → HUD / stream elements

If the live stream has a HUD (e.g. a Skyrim-style overlay), the HUD
agent subscribes to the SSE event stream and reacts to voice commands
detected in the transcript. The full contract is in
[`docs/VOICE_COMMANDS.md`](docs/VOICE_COMMANDS.md); short version:

```
GET  /api/autoclip/events            SSE: voice_command + transcript_chunk
GET  /api/autoclip/events/history    last N events
POST /api/autoclip/command           inject a manual command (HUD hotkeys)
```

Voice command grammar is pluggable (`voice.name: regex|llm|off` in
`autoclip.yaml`). The default regex parser recognises show / hide /
toggle / set / play / add / clip intents — extend `voice.patterns`
to add your own. The LLM parser is OpenAI-compatible and returns
strict JSON for loosely-phrased commands.

The HUD agent that drives OBS should be set up per
[`docs/OBS_MCP_GUIDE.md`](docs/OBS_MCP_GUIDE.md) — that doc is the
handoff point for the parallel agent working on the live HUD.

## 3c. Live multi-streaming (voice-controlled)

Re-broadcast the POV stream to N platforms at once, starting/stopping each
by voice. One source, one `ffmpeg -c copy` republisher per platform. Full
details in [`docs/LIVE_STREAMING.md`](docs/LIVE_STREAMING.md).

```yaml
live_streams:
  enabled: true                       # false = no ffmpeg, no thread, no network
  source: "rtmp://127.0.0.1:1935/live/${RTMP_STREAM_KEY:-glasses}"
  targets:
    - {name: twitch,  key: "${TWITCH_STREAM_KEY}",  enabled: false}
    - {name: youtube, key: "${YOUTUBE_STREAM_KEY}", enabled: false}
```

Voice grammar (→ `LiveStreamManager` via `CommandDispatcher`):

| spoken | intent | target |
|---|---|---|
| `go live on twitch` | `stream` | `twitch` |
| `start streaming on kick` | `stream` | `kick` |
| `go live everywhere` | `stream` | `all` |
| `stop twitch` | `unstream` | `twitch` |
| `stop all streams` | `unstream` | `all` |

Guardrails: unknown platform ⇒ `{"ok": false}`, missing key ⇒ refuses to
start, `status()` never returns keys (only `key_set: bool`), and nothing
goes live unless you set `enabled: true`.

REST: `GET /api/autoclip/live`, `POST /api/autoclip/live/{start,stop}/{name}`,
`POST /api/autoclip/live/{start_all,stop_all}`.

**Stream title** ([`docs/STREAM_TITLE.md`](docs/STREAM_TITLE.md)):
`GET|POST /api/autoclip/live/title {"title", "platforms"?}` sets it on
Twitch / YouTube / Kick (X and Rumble: `ok: false`, no API), answering
`{platform, ok, message}` each. No credentials means `ok: false`, never an
exception. The last title is re-applied when a restream starts. CLI
`python -m autoclip title "..."`, MCP `autoclip_live_title`, event `stream_title`.
CLI: `python -m autoclip live status|start|stop|start-all|stop-all`.

## 3d. Voice commands → OBS (on the VM)

autoclip can also drive **OBS itself** over obs-websocket v5: scene
switches, mute, volume, recording, OBS's own stream output, the virtual
camera, and the replay buffer. Full contract in
[`docs/OBS_VOICE_CONTROL.md`](docs/OBS_VOICE_CONTROL.md).

```yaml
obs:
  password: "${OBS_WS_PASSWORD}"
  voice:
    enabled: false          # nothing touches OBS until this is true
    allow_dangerous: false  # required for unbroadcast / unrecord / unvcam
    aliases: {compass: "Compass", mic: "Mic/Aux"}   # spoken -> OBS name
```

| spoken | intent | note |
|---|---|---|
| `switch to the map scene` | `scene` | fuzzy-resolves the scene name |
| `mute the mic` / `unmute mic` | `mute` / `unmute` | |
| `volume 50` / `turn the volume up` | `volume` | `50`→50 %, clamped |
| `start recording` / `stop recording` | `record` / `unrecord` | stop is gated |
| `start the virtual camera` | `vcam` / `unvcam` | stop is gated |
| `start streaming` / `stop broadcasting` | `broadcast` / `unbroadcast` | OBS's own output; stop is gated |
| `save the replay` / `clip this` | `replay` / `clip` | `SaveReplayBuffer` |

**`streaming` is ambiguous — read this.** A named platform
(`go live on twitch`, `start streaming on twitch`) is §3c's
`LiveStreamManager`. A bare `start streaming` / `start the stream` is
OBS's own output. Both can run at once.

Guardrails: `enabled: false` ⇒ no socket is opened; an intent not in
`voice.intents` is refused; `unbroadcast`/`unrecord`/`unvcam` need
`allow_dangerous`; `scenes` allowlists voice-switchable scenes; unknown
names are refused rather than guessed. `show`/`hide`/`toggle`/`set`/`play`
are deliberately **not** in the default intents, because the HUD agent
usually owns them — enabling both fires every command twice.

REST: `GET /api/autoclip/obs`, `POST /api/autoclip/obs/command`
`{intent, target?, value?}`.
MCP: `autoclip_obs_status`, `autoclip_obs_command`.
CLI: `python -m autoclip obs [intent [target [value]]]`.

Every action emits an `obs_status` event on the bus with
`extra.result` (`{ok, action, target, message, detail}`), so the HUD can
badge state and you can audit what voice actually did.

## 3e. Privacy blur — "blur faces"

One boolean that blurs every face, flipped by voice. Full contract in
[`docs/PRIVACY_BLUR.md`](docs/PRIVACY_BLUR.md).

| spoken | intent |
|---|---|
| `blur faces` / `privacy mode on` / `start blurring` | `blur` |
| `unblur faces` / `stop blurring` / `privacy off` | `unblur` |
| `toggle face blur` / `toggle privacy` | `toggle` (target = faces/privacy/blur) |

```yaml
privacy:
  enabled: true          # nothing runs until this is true
  default_on: true
  mode: clip             # clip | obs | both
```

* `clip` → ffmpeg `crop`+`boxblur`+`overlay` patches on every rendered clip.
  Faces are detected on frames decoded *through* the reframe chain, so boxes
  are already in output pixels.
* `obs` → a `PrivacyBlur` scene holding one cropped copy of the same video
  source per face, plus a single Blur filter. No plugins, no second decoder.

REST: `GET /api/autoclip/privacy`, `POST /api/autoclip/privacy`
`{"on": bool}` or `{"toggle": true}`.
MCP: `autoclip_privacy_status`, `autoclip_privacy_set`.
CLI: `python -m autoclip privacy [status|on|off|toggle]`.
Events: `privacy_status` (`extra.on`, `extra.mode`, `extra.faces`).

## 4b. Length — tuned for virality

Short-form reach is driven by completion rate and loop replays, so the default
length band is intentionally tight:

| key | default | why |
|---|---|---|
| `min_clip_seconds` | 10 | floor: short of this, no payoff |
| `target_clip_seconds` | 25 | ideal loop length for Reels / Shorts |
| `max_clip_seconds` | 30 | hard ceiling: longer clips lose completion rate |

`find_moments` already respects this band: short runs grow toward the target
when there's room, long runs are trimmed to the **densest** `max` around the
peak (not chopped from the head). The LLM prompt is told the same — it should
pick a sub-window of a long moment rather than covering the whole thing.

Raise `max_clip_seconds` to 60 if you want YouTube Shorts to have more room.

Three supported plug-in points (set `agent.name` in `autoclip.yaml`):

1. **`heuristic`** (default, offline) — rules over loudness / motion / scene cuts.
2. **`llm`** — OpenAI-compatible `/chat/completions`. VLM sees sampled frames.
   Set `agent.llm.base_url` / `model` / `api_key_env`.
3. **`remote`** — POST the context JSON to your URL, read `{"clips":[…]}` back.
   Set `agent.remote.url`. Works with n8n, Cloudflare Workers, Slack bots, etc.

Or in Python:

```python
from autoclip import register_agent, AgentContext, ClipDecision

class MyAgent:
    name = "mine"
    def propose(self, ctx: AgentContext) -> list[ClipDecision]:
        return [ClipDecision(start=10, end=40, score=0.9, title="…")]

register_agent("mine", lambda cfg: MyAgent())
```

`AgentContext` gives you `window`, `analysis` (per-second `rms_db`, `speech`,
`motion`, `brightness`, `cut`; pre-scored `moments`), `transcript` (word-level),
`frames` (stills with timestamps), `constraints`, and `previous` clips (dedupe).

---

## 5. Source: OBS today, glasses next

`source.mode` in `autoclip.yaml`:

| mode | what it does |
|---|---|
| `replay_buffer` | OBS keeps the last N seconds in RAM; we call `SaveReplayBuffer` over obs-websocket v5 → one clean file. **Best path.** |
| `watch_dir` | Tails OBS's recording dir (enable Settings ▸ Advanced ▸ automatically split recording). |
| `stream_url` | ffmpeg pulls OBS's SRT/RTMP output and segments it locally. |
| `rtmp` | Cloud: ffmpeg subscribes to a live RTMP feed (phone → MediaMTX) and writes 30 s `.ts` chunks. See §5b. |
| `file` | One local video. Use this for offline dev. |
| `auto` | replay_buffer → watch_dir → file. |

OBS setup: Tools ▸ obs-websocket Settings ▸ enable (port 4455, set a password →
`obs.password`); Settings ▸ Output ▸ Replay Buffer ▸ enable, duration 300s.

### Swapping in Meta glasses later

The pipeline only ever consumes `Segment`s stamped with wall-clock times, so the
glasses become a fourth source with no changes above `ingest.py`. Research notes
(Meta Wearables Device Access Toolkit, a.k.a. DAT):

- SDK: `mwdat-core` + `mwdat-camera` (iOS SPM / Android `com.meta.wearable`).
- Camera stream exposes a `videoFramePublisher`; photos can be captured
  mid-stream. Audio streaming through Camera Stream is **experimental**.
- `mwdat-motion` (accel/gyro/mag), `mwdat-display` (Ray-Ban Display),
  `mwdat-inputs`, `mwdat-speech`; `mwdat-mockdevice` for glasses-free testing.
- Docs: `https://wearables.developer.meta.com/docs/develop/` (login required);
  public API reference at `/docs/reference/ios_swift/dat/latest`.
- Docs MCP (no auth): `https://mcp.developer.meta.com/wearables`, tool
  `search_dat_docs`. llms.txt: `https://wearables.developer.meta.com/llms.txt?full=true`.
- Repos: `github.com/facebook/meta-wearables-dat-ios` / `-android`.
- Practical today: DAT is mobile-only, so the phone bridge relays to OBS
  (RTMP/SRT) and nothing below `ingest.py` changes. The A/V sync and
  network-smoothing contract the phone has to honor is in
  [`docs/AUDIO_VIDEO_SYNC.md`](docs/AUDIO_VIDEO_SYNC.md).

## 5b. Cloud deployment — phone → cloud VM

The right way to ship the glasses path. The phone app is a thin bridge
that pulls frames from DAT's `videoFramePublisher` and pushes them as a
single RTMP stream to a public ingest. Everything heavy lives on a small
always-on VM.

```
[Ray-Ban Display] ─BLE/Wi-Fi─▶ [Phone: DAT + RTMP publisher]
                                     │  rtmp://HOST:1935/live/<key>
                                     ▼
                              ┌──────────────────┐
                              │  MediaMTX :1935  │  ~30 MB container
                              └──────────────────┘
                                     │  rtmp://localhost:1935/live/<key>  (subscriber)
                                     ▼
                              ┌──────────────────┐
                              │     autoclip     │  built from this repo
                              │  ffmpeg→Whisper  │
                              │  →agent→render   │
                              │  →publish        │
                              └──────────────────┘
```

Bring it up (Google Cloud, one script, from your laptop):

```bash
cd deploy/obs-vps
./gcp.sh up        # first time: firewall + VM + build + start
./gcp.sh deploy    # after code changes
./gcp.sh info      # ingest URLs, approval page URL + password
./gcp.sh stop      # stop paying for the VM when not streaming
```

`autoclip` is one service of the streaming stack in
`deploy/obs-vps/docker-compose.yml` (MediaMTX, headless OBS + HUD, Caddy;
host network). It runs `serve --loop` in one process (cycle loop + REST on
`127.0.0.1:8899`), capped at `cpus: 1.5` and `nice 15` so OBS never drops
frames, with `transcribe_model: tiny`. Its config is the repo
`autoclip.yaml` with [`deploy/obs-vps/autoclip.vps.yaml`](deploy/obs-vps/autoclip.vps.yaml)
merged on top by `setup.sh`.

- **Clips** come from the raw glasses feed `live/<STREAM_KEY>`.
- **Restreams** (`go live on twitch`) pull OBS's composited program —
  HUD + avatar — which OBS publishes back into MediaMTX as `live/program`
  (publish allowed from localhost only).
- **Approval queue** for the phone: `https://<ip>.sslip.io/autoclip/`
  behind Caddy `basic_auth` (password generated into `.env`).
  `/autoclip/outbox/*` stays public so Instagram `hosting: static` can fetch
  clips; `server.public_base_url` follows the boot's IP.
- Guardrails hold: `AUTOCLIP_PUBLISH=dry_run` and `AUTOCLIP_LIVE_STREAMS=0`
  in `.env` by default.

(`deploy/cloud/`, the old standalone MediaMTX + autoclip compose, is gone;
this stack supersedes it.)

**Source driver in `autoclip.yaml`:**

```yaml
source:
  mode: rtmp
  rtmp:
    url: "rtmp://127.0.0.1:1935/live"   # mediamtx on the same host
    stream_key: "${STREAM_KEY}"         # ${VAR:-default} also supported
    dir: var/autoclip/incoming
    chunk_seconds: 30
```

`${VAR}` and `${VAR:-default}` are expanded at config load against the
process environment. The full phone-app contract (what the iOS/Android
client must do) is in [`docs/PHONE_APP.md`](docs/PHONE_APP.md).

**Why this shape and not "do it all on the phone"**: iOS suspends
ffmpeg/Whisper, Android thermal-throttles, and the glasses + phone
already pull ~1 A combined. Cloud CPU (~$8–20/mo) is always on, never
throttles, and is the cheapest way to actually ship this.

---

## 6. Guardrails (do not break these)

- **`publish.mode` defaults to `dry_run`.** Nothing leaves the machine unless a
  human flips it to `live` and approves.
- **`publish.require_approval` defaults to `true`.** In live mode clips land in
  the pending queue; publish via `approve`.
- Every external service degrades gracefully. Missing SDK/creds ⇒ `ok=False,
  dry_run=True`, never an exception that kills the loop.
- Captions burn in through one of two paths, chosen automatically
  (`render.caption_style.burn: auto`):
  1. ffmpeg's `subtitles` filter (needs libass) — best quality
  2. pre-rendered RGBA PNG sequence + `overlay` (needs `Pillow`) — works on any
     ffmpeg build, **including Homebrew's ffmpeg 9, which ships without libass**
  If neither is available, the clip still renders and an `.srt` sidecar is kept.

## 6b. Live (animated) subtitles

Captions burned into every clip are animated word-by-word. Set
`render.caption_style.mode`:

| mode | effect |
|---|---|
| `karaoke` (default) | line stays up; the active word fills in colour as it is spoken (ASS `\kf` sweep) |
| `pop` | one event per word — the active word highlights and pops in scale (CapCut / TikTok style) |
| `line` | static, no animation |

Both animated modes need **word-level timestamps**, which come from
`faster-whisper` (`word_timestamps=True`). If transcription is unavailable the
writer silently falls back to `line`.

Tuning: `primary` / `secondary` are ASS `&HAABBGGRR` (active vs not-yet-sung);
`active_inline` / `inactive_inline` are `&HBBGGRR` per-word colours used by
`pop`; `pop_scale`, `pop_ms`, `fade_ms`, `margin_v`, `max_words`, `max_chars`.
`max_words: 3` and `max_chars: 28` give the 2–3-word-per-screen look.
PNG-mode extras: `burn` (`auto|ass|images`), `caption_fps` (12), `stroke` (5).

A sidecar `<clip>.srt` is always written next to the clip for platform
uploads (YouTube captions API, etc.).
- `source.mode: file` + a local mp4 is the offline path — use it in tests.
- Instagram needs a **public** URL for the video (`server.public_base_url` for
  `hosting: static`, or `hosting: s3`).

## 7. Layout

```
autoclip/
  config.py     defaults + deep merge (autoclip.yaml)
  obs.py        obs-websocket v5 client
  ingest.py     replay_buffer | watch_dir | stream_url | rtmp | file  -> Segments
  buffer.py     RollingWindow -> materialize one Window file
  signals.py    audio/motion/scene-cut analysis + candidate moments
  transcript.py faster-whisper word timestamps
  voice.py      transcript -> voice_command StreamEvents (regex|llm parsers)
  events.py     in-process EventBus (JSONL log + SSE fanout)
  livestream.py one source -> N platform RTMP republishers (-c copy)
  dispatcher.py EventBus -> side effects (routes stream/unstream to livestream)
  captions.py   SRT + ASS burn-in
  clips.py      ffmpeg cut/reframe/caption/normalize
  agents.py     ClipDecision, AgentContext, heuristic/llm/remote + registry
  publishers/   local (outbox), youtube, instagram, x
  pipeline.py   run_cycle(): the whole product
  api.py        FastAPI REST + OpenAPI + SSE
  mcp_server.py MCP over stdio (no SDK dependency)
  cli.py        `python -m autoclip …`
```
