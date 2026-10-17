# OBS voice control — glasses → OBS on the VM

The HUD agent (see [`OBS_MCP_GUIDE.md`](OBS_MCP_GUIDE.md)) owns *what gets
rendered*. This is the other half: autoclip driving **OBS itself** over
obs-websocket v5, straight from speech picked up by the glasses.

```
  glasses mic ──▶ RTMP ──▶ Whisper ──▶ voice parser ──▶ EventBus
                                                            │
                                                  CommandDispatcher
                                                            │
                                                     OBSController
                                                            │
                                              ws://127.0.0.1:4455 ──▶ OBS
```

Scene switches, mute, volume, recording, OBS's own stream output, the
virtual camera, the replay buffer — all reachable by voice, and all
gated (see [§4](#4-guardrails)).

If you only want the HUD overlay vocabulary, you want
[`VOICE_COMMANDS.md`](VOICE_COMMANDS.md) instead.

---

## 1. Turn it on

Nothing touches OBS until you opt in. Three edits:

**OBS** ▸ Tools ▸ obs-websocket Settings ▸ enable, port 4455, set a password.

**`autoclip.yaml`**:

```yaml
obs:
  password: "your-obs-websocket-password"
  voice:
    enabled: true
```

Confirm it connected:

```bash
python -m autoclip obs
```

```json
{"enabled": true, "connected": true, "scene": "Live",
 "scenes": ["Live", "MapScene", "Ending"],
 "sources": ["Mic/Aux", "Compass", "Subtitle", "DragonRoar"],
 "recording": false, "streaming": false, "intents": ["broadcast", ...]}
```

If `connected` is false, `error` tells you why (usually the password).

---

## 2. The vocabulary

| spoken | intent | what happens |
|---|---|---|
| `switch to the map scene` | `scene` | `SetCurrentProgramScene` |
| `go to the ending scene` | `scene` | ″ |
| `scene map` / `cut to the map` | `scene` | ″ |
| `mute the mic` / `mute` | `mute` | `SetInputMute` on the resolved input |
| `unmute mic` | `unmute` | ″ |
| `volume 50` / `set volume to 30` | `volume` | `SetInputVolume` (mul 0..1) |
| `set mic volume to 80` | `volume` | ″ |
| `turn the volume up` / `volume down` | `volume` | relative ±10 % |
| `start recording` / `record this` | `record` | `StartRecord` |
| `stop recording` | `unrecord` | `StopRecord` — **gated** |
| `start the virtual camera` | `vcam` | `StartVirtualCam` |
| `stop virtual cam` | `unvcam` | `StopVirtualCam` — **gated** |
| `start streaming` / `start the stream` | `broadcast` | `StartStream` (OBS's own output) |
| `stop broadcasting` / `stop the stream` | `unbroadcast` | `StopStream` — **gated** |
| `save the replay` / `replay that` | `replay` | `SaveReplayBuffer` |
| `clip this` | `clip` | `SaveReplayBuffer` (same as `replay`) |
| `set transition to fade` | `transition` | `SetCurrentSceneTransition` |

Opt-in extras (off by default because the HUD agent normally owns them —
see [§5](#5-who-owns-showhidetoggle)):

| spoken | intent |
|---|---|
| `show the compass` | `show` |
| `hide health bar` | `hide` |
| `toggle night vision` | `toggle` |
| `set weather to snow` | `set` (writes a text source) |
| `play dragon roar` | `play` (restarts a media source / refreshes a browser source) |

### "streaming" means two different things

This trips people up, so it is worth stating explicitly:

| you say | who handles it | what it does |
|---|---|---|
| `go live on twitch` | `LiveStreamManager` | starts autoclip's own ffmpeg republisher for that platform |
| `start streaming on twitch` | `LiveStreamManager` | ″ |
| `start streaming` (bare, no platform) | `OBSController` | starts **OBS's** stream output |
| `start the stream` / `start broadcasting` | `OBSController` | ″ |

A platform name after the verb ⇒ the multi-stream path
([`LIVE_STREAMING.md`](LIVE_STREAMING.md)). No platform ⇒ OBS itself.
Both can run at the same time; they are independent outputs.

---

## 3. How a spoken name becomes an OBS name

You say `compass`; OBS calls the source `Compass Image`. The controller
resolves in four steps, returning the **OBS** spelling:

1. **alias** — `obs.voice.aliases: {compass: "Compass Image"}` (exact, wins)
2. **exact** — after folding case and punctuation (`compass image` = `CompassImage`)
3. **substring** — either direction, so `compass` matches `Compass Image`
   and `Compass Image` matches `compass`
4. **fuzzy** — `difflib` at `match_cutoff` (default 0.6), so `helth bar`
   still finds `HealthBar`

If nothing clears the cutoff you get `{"ok": false, "message": "no source
matching '…'"}` and **nothing is sent to OBS**. Add an alias when fuzzy
picks the wrong thing — that is what it is for.

```yaml
obs:
  voice:
    aliases:
      compass: "Compass"
      health: "HealthBar"
      mic: "Mic/Aux"
    scene_aliases:
      map: "MapScene"
      outro: "Ending"
```

Bare `mute` / `volume 50` need a target. Set `default_audio`, or let it
autodetect the first input whose kind contains `audio`/`wasapi`
(falling back to `Mic/Aux`).

---

## 4. Guardrails

Streaming live by voice is fine. Accidentally ending a broadcast because
the mic caught a false positive is not. Four independent gates, all
checked **before** anything is written to the socket:

| gate | default | effect |
|---|---|---|
| `voice.enabled` | `false` | no obs-websocket connection is opened at all |
| `voice.intents` | 12 safe intents | an intent not on the list is refused |
| `voice.allow_dangerous` | `false` | required for `unbroadcast`, `unrecord`, `unvcam` |
| `voice.scenes` | `[]` (all) | allowlist of voice-switchable scenes |

Volumes are clamped to 0–100 %. Unknown scenes/sources/transitions are
refused rather than guessed at.

To allow ending a broadcast by voice:

```yaml
obs:
  voice:
    allow_dangerous: true
```

To stop voice from switching into a scene you don't want it near:

```yaml
obs:
  voice:
    scenes: ["Live", "MapScene"]   # "Ending" becomes unreachable by voice
```

A refusal is still reported — `{"ok": false, "message": "…is destructive…"}`
— and still emits an `obs_status` event, so false positives are visible
in the event log rather than silent.

---

## 5. Who owns show/hide/toggle?

Both the HUD agent and this controller *can* act on `show`, `hide`,
`toggle`, `set`, and `play`. Enabling both means every "show the compass"
fires twice.

Default: **the HUD agent owns them.** `obs.voice.intents` ships without
them, so the dispatcher lets those events pass straight through to the
SSE stream and OBS is never touched.

Only add them if you are *not* running a HUD agent and want autoclip to
be the whole thing:

```yaml
obs:
  voice:
    intents: [scene, mute, unmute, volume, record, unrecord, vcam,
              unvcam, broadcast, unbroadcast, replay, clip,
              show, hide, toggle, set, play]
```

Source visibility is applied to `obs.voice.scene` when set, otherwise
whatever scene is currently live.

---

## 6. Surfaces

Everything below hits the same `OBSController`, so behaviour is identical.

### REST

```bash
curl http://localhost:8899/api/autoclip/obs
curl -XPOST http://localhost:8899/api/autoclip/obs/command \
  -H "Content-Type: application/json" \
  -d '{"intent":"scene","target":"map"}'
curl -XPOST http://localhost:8899/api/autoclip/obs/command \
  -H "Content-Type: application/json" \
  -d '{"intent":"mute","target":"mic"}'
```

### MCP

| tool | args |
|---|---|
| `autoclip_obs_status` | – |
| `autoclip_obs_command` | `intent`, `target?`, `value?` |

### CLI

```bash
python -m autoclip obs                  # status
python -m autoclip obs scene map
python -m autoclip obs mute mic
python -m autoclip obs volume 50
python -m autoclip obs record
python -m autoclip obs broadcast
```

### Python

```python
from autoclip.obs import OBSClient
from autoclip.obsctl import OBSController

ctl = OBSController(OBSClient(cfg["obs"]), cfg["obs"]["voice"])
ctl.handle("scene", "map").ok          # -> True
```

---

## 7. The `obs_status` event

Every action publishes an event so the HUD can show state (and so you
can audit what voice actually did):

```json
{"type": "obs_status", "intent": "scene", "target": "MapScene",
 "source": "dispatcher",
 "extra": {"result": {"ok": true, "action": "scene",
                      "message": "switched to 'MapScene'"}}}
```

`extra.result` is the full `OBSResult`: `ok`, `action`, `target`,
`message`, `detail`. On SSE the LIVE/recording badge should follow
`obs_status`, not `voice_command` — `voice_command` only means something
was *said*.

---

## 8. Verify without speaking

```bash
# 1. does OBS answer at all?
python -m autoclip obs

# 2. inject commands (no mic needed)
curl -XPOST http://localhost:8899/api/autoclip/command \
  -H "Content-Type: application/json" -d '{"text":"switch to the map scene"}'

# 3. confirm the refusal path still refuses
curl -XPOST http://localhost:8899/api/autoclip/obs/command \
  -H "Content-Type: application/json" -d '{"intent":"unbroadcast"}'
# -> {"ok": false, "message": "'unbroadcast' is destructive; set obs.voice.allow_dangerous"}

# 4. watch what voice did
tail -f var/autoclip/events.jsonl | grep obs_status
```

---

## 9. Troubleshooting

| symptom | cause / fix |
|---|---|
| every action returns `"obs voice control disabled"` | `obs.voice.enabled` is still false |
| `connected: false`, `error: "OBS requires a websocket password"` | set `obs.password` |
| `"no source matching 'x'"` | the name never resolved — add `obs.voice.aliases` |
| `"'x' is not an item in scene 'Live'"` | the source exists but isn't in the scene you pinned; clear `obs.voice.scene` or add the source |
| `show`/`hide` do nothing | they're not in the default `intents` — see §5 |
| `stop recording` refuses | expected; set `allow_dangerous: true` |
| commands land twice | both the HUD agent and `obs.voice.intents` own the intent — see §5 |
| scene switches but nothing visible | you switched OBS's *program* scene while in studio mode, where the audience sees *preview*; use `transition` or leave studio mode |

---

## 10. Files

| file | what |
|---|---|
| `autoclip/obs.py` | obs-websocket v5 protocol client (thin) |
| `autoclip/obsctl.py` | semantic layer: name resolution, policy, `OBSResult` |
| `autoclip/voice.py` | `DEFAULT_PATTERNS` — the grammar |
| `autoclip/dispatcher.py` | routes intents to OBS or the live re-streamers |
| `docs/VOICE_COMMANDS.md` | HUD overlay vocabulary (the other half) |
| `docs/LIVE_STREAMING.md` | per-platform re-streaming |
