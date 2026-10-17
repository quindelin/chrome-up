# Voice commands — the bus the HUD agent listens on

This is the contract between `autoclip` (which knows what was said)
and the HUD / stream-element agent (which knows how to render
things). The wire is HTTP, the data is JSON, and the bus is in
`autoclip/events.py`.

## At a glance

```
  glasses audio ──▶ phone RTMP ──▶ cloud Whisper ──▶ voice parser
                                                          │
                                                          ▼
                                              EventBus (JSONL + SSE)
                                                          │
                          ┌───────────────────────────────┼─────────────────────────┐
                          ▼                               ▼                         ▼
               /api/autoclip/events         /api/autoclip/events/history   /api/autoclip/command
                  (SSE stream)                  (last N events)            (manual injection)
                          │                               │                         │
                          └──────────── HUD agent ────────┴─────────────────────────┘
```

## Event shape

Every event is a JSON object with this schema:

```ts
type StreamEvent = {
  type: "voice_command" | "transcript_chunk" | "stream_gap" | "stream_status" | "obs_status";
  ts: number;          // wall-clock seconds when emitted
  window_t: number;    // seconds from the start of the current 5-min window
  text: string;        // for voice_command/transcript_chunk: the spoken words
  intent: string;      // show | hide | toggle | set | play | add | clip | scene |
                       // mute | unmute | volume | record | unrecord | vcam | unvcam |
                       // broadcast | unbroadcast | replay | transition |
                       // stream | unstream | manual | unknown
  target: string;      // the noun (e.g. "compass", "health bar", "weather")
  value: string;       // optional (e.g. for "set weather to snow", value="snow")
  confidence: number;  // 0..1, default 0.7
  source: string;      // "regex" | "llm" | "manual" | "phone"
  extra: {             // context the HUD might want
    t0?: number;       // for transcript_chunk: first word's window_t
    t1?: number;       // for transcript_chunk: last word's window_t
    window_start_wall?: number;   // unix-seconds the current window started
    window_end_wall?: number;
  };
};
```

The HUD agent maps `target` to its own scene graph. autoclip does
**not** know what "compass" or "dragon counter" means in your HUD —
that's your concern. The default vocabulary is in
`autoclip/voice.py:DEFAULT_PATTERNS`. Override via
`autoclip.yaml` (`voice.patterns`).

## Default command vocabulary

The regex parser recognises these out of the box. All are
case-insensitive and tolerate filler words ("show the", "please",
trailing period).

| spoken | intent | target | value |
|---|---|---|---|
| `show the compass` | `show` | `compass` | – |
| `hide health bar` | `hide` | `health bar` | – |
| `toggle night vision` | `toggle` | `night vision` | – |
| `set weather to snow` | `set` | `weather` | `snow` |
| `play dragon roar` | `play` | `dragon roar` | – |
| `add subtitle: hello there` | `add` | `subtitle` | `hello there` |
| `caption: this is a test` | `add` | `subtitle` | `this is a test` |
| `clip this` | `clip` | – | – |
| `mark a clip` | `clip` | – | – |
| `go live on twitch` | `stream` | `twitch` | – |
| `start streaming on kick` | `stream` | `kick` | – |
| `go live everywhere` | `stream` | `all` | – |
| `stop twitch` | `unstream` | `twitch` | – |
| `stop all streams` | `unstream` | `all` | – |

### Which intents autoclip handles itself

Three families never reach your HUD, because autoclip acts on them
directly. Everything else is yours to render.

| intents | handled by | see |
|---|---|---|
| `stream`, `unstream` | `LiveStreamManager` — starts/stops per-platform ffmpeg re-broadcasts | [`LIVE_STREAMING.md`](LIVE_STREAMING.md) |
| `scene`, `mute`, `unmute`, `volume`, `record`, `unrecord`, `vcam`, `unvcam`, `broadcast`, `unbroadcast`, `replay`, `clip`, `transition` | `OBSController` — drives OBS over obs-websocket v5 | [`OBS_VOICE_CONTROL.md`](OBS_VOICE_CONTROL.md) |
| `show`, `hide`, `toggle`, `set`, `play` (only if the operator adds them to `obs.voice.intents`) | `OBSController` | [`OBS_VOICE_CONTROL.md`](OBS_VOICE_CONTROL.md) |

`clip` is in both camps: it is in the default `obs.voice.intents` (saves the
OBS replay buffer) *and* it is a normal HUD event. Disable it under
`obs.voice.intents` if you only want the HUD behaviour.

You will also see `obs_status` events — those are autoclip reporting what it
just did, not something you need to render.

Add your own:

```yaml
# autoclip.yaml
voice:
  name: regex
  patterns:
    - intent: add
      re: '^\s*spawn\s+(?P<target>.+?)\s*$'
    - intent: set
      re: '^\s*(?P<target>mana|stamina|health)\s+(?:to\s+)?(?P<value>\d+)\s*$'
```

## REST endpoints

The HUD agent has three options for getting events. Pick one based
on how it runs.

### Server-Sent Events — `/api/autoclip/events`

Long-lived HTTP connection. The server pushes one JSON object per
line, prefixed with `data: ` (standard SSE). Includes a `: keepalive`
line every 15 s so HTTP intermediaries don't kill the connection.

```js
const es = new EventSource("http://AUTOCLIP_HOST:8899/api/autoclip/events");
es.onmessage = (e) => {
  const ev = JSON.parse(e.data);
  switch (ev.type) {
    case "voice_command":    hud.handleCommand(ev);        break;
    case "transcript_chunk": hud.drawCaption(ev);          break;
    case "stream_gap":       hud.freezeFrame();            break;
    case "stream_status":    hud.setLiveBadge(ev.target, ev.intent === "stream"); break;
    case "obs_status":       hud.setObsBadge(ev.target, ev.extra.result?.ok); break;
  }
};
```

### Polling — `/api/autoclip/events/history?type=voice_command&n=50`

For HTTP-only clients (no streaming). Returns:

```json
{"events": [ {type, ts, text, intent, target, ...}, ... ]}
```

Poll every 1–2 s. The `ts` field is the dedupe key.

### Manual injection — `POST /api/autoclip/command`

Useful for HUD hotkeys, debugging, or bypassing the voice pipeline
when the user types a command:

```bash
curl -XPOST http://localhost:8899/api/autoclip/command \
  -H "Content-Type: application/json" \
  -d '{"text":"show the dragon counter", "intent":"show", "target":"dragon counter"}'
```

The event goes through the same bus, so SSE subscribers receive it
within milliseconds.

## Which endpoint to use when

| HUD runs as… | use |
|---|---|
| OBS browser source | SSE via `EventSource` (JavaScript in the dock) |
| A local Python service | either; polling is fine at 1 Hz |
| An MCP-aware agent | polling, then `autoclip_publish` on decisions |
| A phone app mirroring the HUD | SSE through a reverse proxy |

## Latency

The default pipeline cycle is 30 s. Voice events are emitted at the
end of each cycle, so the worst-case latency from "word spoken" to
"event delivered" is `cycle_seconds + whisper_time + ~1s`.

For sub-second latency, set `window.cycle_seconds: 10` in
`autoclip.yaml` (the cost is more CPU on the cloud VM — whisper-base
runs 3–5 s per 30 s window). For 1 s latency, you need on-device
command detection on the phone and `POST /api/autoclip/command`
directly.

## Custom parsers (LLM, remote)

Two are built in:

- `voice.name: regex` (default) — pure Python, zero dependencies.
- `voice.name: llm` — OpenAI-compatible `/chat/completions`. The
  system prompt is in `autoclip/voice.py:LLMParser.PROMPT`. The
  model is asked to return strict JSON. Use this when commands are
  phrased loosely ("can you put the dragon health on screen" should
  become `intent=show target=health`).

Or in Python, register your own:

```python
from autoclip import register_voice_parser
from autoclip.voice import StreamEvent

class MyParser:
    name = "minecraft"
    def parse(self, transcript, window_t=0.0):
        return [StreamEvent(intent="...", target="...", ...)
                for word in transcript.text.split()
                if word.startswith("@")]

register_voice_parser("minecraft", lambda cfg: MyParser())
```

Then `voice.name: minecraft` in the YAML.

## How the HUD should react

A robust HUD should:

1. **Subscribe via SSE** at startup. Buffer events while the
   connection is down (the bus keeps a 500-event in-memory history
   and the events.jsonl file is persistent).
2. **Dedupe by `(ts, intent, target)`** in case SSE reconnects send
   a duplicate (rare, but possible).
3. **Treat `target` as opaque** — map to your scene elements; never
   crash on an unknown value.
4. **Use `window_t` to time animations** — a "show compass" event
   at `window_t=42` should appear at the same `window_t=42` in the
   recording playback, not at "now".
5. **Log to the same `events.jsonl`** for post-hoc debugging
   (optional — autoclip already does).

## End-to-end smoke test

```bash
# 1. start the pipeline in cloud mode
./run_autoclip.sh cloud

# 2. start a fake RTMP source that talks
ffmpeg -re -f lavfi -i testsrc -f lavfi -i "sine=frequency=440" \
       -c:v libx264 -c:a aac -shortest -f flv \
       rtmp://127.0.0.1:1935/live/KEY

# 3. in another shell, watch events
curl -N http://127.0.0.1:8899/api/autoclip/events

# 4. inject a manual command (no real audio needed)
curl -XPOST http://127.0.0.1:8899/api/autoclip/command \
  -H "Content-Type: application/json" \
  -d '{"text":"show the compass", "intent":"show", "target":"compass"}'
# expect: data: {"type":"voice_command", ...}
```

## Why this design

We considered three alternatives:

1. **MQTT pub/sub** — battle-tested but adds a broker. SSE is enough
   for a single subscriber (the HUD), and a JSONL file is a permanent
   record that survives restarts.
2. **Webhooks** — autoclip POSTs to a registered URL on each event.
   Works but ties the pipeline's health to the consumer's. SSE
   inverts this so a slow/dead consumer never blocks autoclip.
3. **Let the HUD agent read the transcript itself** — fine if the HUD
   also has Whisper, but then the HUD has to do the analysis too.
   Splitting detection from rendering is what the bus enables.

This stays one-process and zero-dep. The bus file is `var/autoclip/
events.jsonl` — `tail -f` it to see what's going on.
