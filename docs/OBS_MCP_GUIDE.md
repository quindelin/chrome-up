# OBS MCP guide — for the HUD / stream-element agent

This doc is for the agent that runs the live "Skyrim-style HUD" —
the one that puts compass, health bar, subtitles, sound effects, and
stream alerts on top of the live OBS scene. It tells that agent how
to find OBS, how to talk to it, and how to react to `autoclip`'s
voice command bus.

If you are not that agent, you can ignore this file.

---

## 1. The two things you need to talk to

| thing | URL | auth |
|---|---|---|
| OBS | `ws://127.0.0.1:4455` (default) | password in OBS ▸ Tools ▸ obs-websocket Settings |
| autoclip events | `http://127.0.0.1:8899/api/autoclip/events` (SSE) | optional bearer token |

OBS is your canvas. autoclip is your sense organ. OBS tells you
what's on screen; autoclip tells you what the user just said.

---

## 2. Which OBS MCP server should I use?

There are several, none canonical. Pick one:

| server | protocol | install | tools |
|---|---|---|---|
| [`mcp-obs`](https://github.com/royshil/obs-mcp) by royshil | stdio MCP | `uvx mcp-obs` or `pip install mcp-obs` | get/set scenes, sources, filters, streaming status, recording start/stop |
| [`obs-mcp`](https://github.com/sergei-grechanik/obs-mcp) | stdio MCP | various | scene switching, source toggling |
| obs-websocket v5 directly | raw WebSocket | no extra install; use `obsws-python` or `websocket-client` | everything the OBS plugin exposes |

If your agent already speaks MCP, prefer an MCP server (less glue
code). If you need fine-grained control over recording / streaming
metadata, use the obs-websocket v5 protocol directly.

### Recommended MCP config

```json
{
  "mcpServers": {
    "obs": {
      "command": "uvx",
      "args": ["mcp-obs"],
      "env": {
        "OBS_HOST": "127.0.0.1",
        "OBS_PORT": "4455",
        "OBS_PASSWORD": "<your obs-websocket password>"
      }
    },
    "autoclip": {
      "command": "python",
      "args": ["-m", "autoclip.mcp_server", "--config", "autoclip.yaml"]
    }
  }
}
```

The HUD agent now has two tool families. Use `autoclip_*` to react
to speech, use `obs_*` to manipulate the scene.

---

## 3. OBS settings that matter for sync

If you are also the one running OBS (locally or on a streamer
machine), these are the OBS settings the pipeline assumes. Get them
right or expect lip-sync drift.

### Output ▸ Output mode = Advanced

- **Type: Standard**
- **Encoder: x264** (or NVENC for GPU) — match the `keyframe_interval`
  to 2 s (see below)
- **Rate Control: CBR**
- **Bitrate: 2.5 Mbps** (matches what autoclip's deploy docs recommend)
- **Keyframe Interval: 2** — *critical*. The cloud segmenter cuts on
  keyframe boundaries. If you use OBS's default 5 s, every "30 s
  segment" is actually 30–35 s, which throws off the rolling window.
- **CPU Preset: veryfast** (or NVENC equivalent)
- **Profile: high**
- **Tune: zerolatency** (RTMP is a live stream, not a VOD)
- **Rescale Output: 1920×1080, 30 fps** (or whatever the phone pushes)

### Audio ▸ Sample rate = 48 kHz

`Audio Sample Rate: 48 kHz` everywhere. Mixing 44.1 kHz sources
into a 48 kHz pipeline causes the A/V to drift by ~4 seconds over
an hour, which your viewers will notice.

### Advanced ▸ automatically split recording = ON (when in OBS-source mode)

The `watch_dir` source driver tails this directory. Filename
template should include a timestamp so files are sortable:
`Recording %CCYY-%MM-%DD %hh-%mm-%ss`.

### Tools ▸ obs-websocket Settings = ON

- **Enable WebSocket server**
- **Port: 4455**
- **Enable authentication** with a password
- Apply that password to `autoclip.yaml` (`obs.password`)

---

## 4. Clock handling inside OBS

OBS maintains its own audio + video clock and synchronises them at
the output stage. You don't need to do anything special for
*output* sync.

For *input* sync (the frames coming in from the phone via RTMP
into a Media Source or VLC Source), OBS uses a small jitter
buffer. If you ever route the phone's RTMP through OBS as a Media
Source:

1. Right-click the source ▸ Properties.
2. Set **"Restart playback when source becomes active"** to ON.
3. **"Buffering"** = leave at default unless you see under-runs.

For the HUD agent that needs to know "what time is it in the live
stream right now", the canonical answer is:

```
obs_time = current_obs_recording_duration_seconds()
```

You can read this through the OBS MCP server's `obs_get_recording
_status` or directly via the obs-websocket v5 protocol
(`GetRecordStatus` returns `outputDuration`).

The autoclip pipeline carries the **same** time in its events:
`event.window_t` is seconds from the start of the current 5-minute
window, and `event.extra.window_start_wall` is the unix-seconds
timestamp of that window's start. You can compute "what's happening
in OBS right now" as:

```
obs_now_in_window = (current_wall_time - event.extra.window_start_wall)
```

---

## 5. Reacting to voice commands

Here's a minimal reference for a HUD agent that listens to
autoclip's SSE stream and drives OBS:

```python
import json
import urllib.request

import obsws_python as obs  # pip install obsws-python

def main():
    obs_client = obs.ReqClient(host="127.0.0.1", port=4455, password="...")

    # SSE: read the autoclip event stream line by line
    req = urllib.request.urlopen("http://127.0.0.1:8899/api/autoclip/events")
    for raw in req:
        line = raw.decode().strip()
        if not line.startswith("data: "):
            continue
        ev = json.loads(line[6:])
        if ev["type"] != "voice_command":
            continue

        intent, target = ev["intent"], ev["target"]
        if intent == "show":
            set_source_visibility(obs_client, target, True)
        elif intent == "hide":
            set_source_visibility(obs_client, target, False)
        elif intent == "toggle":
            toggle_source(obs_client, target)
        elif intent == "set":
            set_source_text(obs_client, target, ev["value"])
        elif intent == "play":
            play_media_source(obs_client, target)
        elif intent == "add" and target == "subtitle":
            show_caption_overlay(obs_client, ev["value"])
        elif intent == "clip":
            trigger_autoclip_render(obs_client)

def set_source_visibility(obs_client, name, visible):
    obs_client.set_scene_item_enabled("LiveHUD", name, visible)

def set_source_text(obs_client, name, text):
    obs_client.set_input_settings(name, {"text": text}, overlay=True)

# ... etc
```

The full vocabulary is in
[`docs/VOICE_COMMANDS.md`](VOICE_COMMANDS.md).

---

## 6. The OBS-side scene graph

You (the HUD agent) own this. Recommended structure:

```
Scene: "Live"
├── Media Source: "GlassesFeed"          (the phone's RTMP)
├── Browser Source: "HudOverlay"         (your HUD JS, talks to SSE)
├── Image Source: "Compass"
├── Image Source: "HealthBar"
├── Text (GDI+): "Subtitle"
├── Media Source: "DragonCounter"        (optional)
└── Audio Source: "Mic" + RTMP audio     (mixed into stream)
```

Hide everything by default; show them on `voice_command` events.
A "show the compass" should make the compass source visible
within 100 ms of the event arriving — that's the target.

---

## 7. Testing without the real OBS

autoclip's `POST /api/autoclip/command` lets you inject events
without speaking. Use it for HUD agent tests:

```bash
# render a single command
curl -XPOST http://127.0.0.1:8899/api/autoclip/command \
  -H "Content-Type: application/json" \
  -d '{"text":"show the compass", "intent":"show", "target":"compass"}'

# bulk replay
for cmd in "show compass" "show health bar" "hide compass"; do
  curl -XPOST http://127.0.0.1:8899/api/autoclip/command \
    -H "Content-Type: application/json" \
    -d "{\"text\":\"$cmd\"}"
  sleep 0.5
done
```

The HUD agent should treat each one the same as a real voice event.

---

## 8. What NOT to do

| anti-pattern | why it fails |
|---|---|
| Render HUD updates from a `while True: poll()` loop on the same process as the OBS websocket client | single thread + blocking poll = dropped frames, laggy scene switches |
| Use `obs_source_send_text` for subtitles | the wrong layer; subtitle text belongs in a Browser Source that subscribes to SSE, not in the OBS text source itself (which doesn't sync with audio) |
| Trust `obs_get_recording_status` for A/V sync | it returns output duration, which is a *stream* clock — it can drift from the recording's media clock by tens of ms |
| Subscribe to SSE inside OBS's `on_tick` script | Python is fine; a `while True` in an OBS script is a memory leak and tick rate starvation |
| Re-encode the RTMP feed in OBS to "fix sync" | breaks the assumption that the cloud pipeline's `-c copy` segmenter preserves PTS; you'll re-introduce the drift |

---

## 9. File map for cross-agent coordination

| file | who reads it | what it says |
|---|---|---|
| `docs/VOICE_COMMANDS.md` | you (HUD agent) | the wire format of voice events |
| `docs/AUDIO_VIDEO_SYNC.md` | the phone app | the A/V sync contract |
| `docs/PHONE_APP.md` | the phone app | how to push RTMP up |
| `deploy/obs-vps/gcp.sh` | you (ops) | how to bring up the cloud VM |
| `AGENTS.md` | everyone | the autoclip contract |

If you change a voice command vocabulary, update
`docs/VOICE_COMMANDS.md` *and* the example in this file. Keep them
in sync.
