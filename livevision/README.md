# HUDstream

A Skyrim-style HUD for POV streams (built for Meta Ray-Ban Display glasses).
It is an **OBS browser source** that reacts to what the camera sees and what the
mic hears, and hands out skill points like the real game.

- **Compass bar** — real heading pulled off the device (phone bridge, UDP IMU,
  BLE beacon or serial IMU), with world-pinned quest markers **and a live
  navigation objective** built from your maps directions.
- **Audio-reactive ring** — spectrum spokes + loudness arc around the avatar.
- **VTube avatar** (bottom-right) — canvas rig that lip-syncs to your mic
  (visemes A/E/I/O/U), blinks, bobs when you talk, blushes on "rizz", sweats
  while you run.
- **Vitals** — Health / Magicka / Stamina drain and regen from real behaviour.
- **Gesture-opened menu** — tap/pinch to open a Skyrim menu (Skills / Stats /
  Objectives), swipe to change tab. Driven by the Neural Band (via a bridge),
  Stream Deck, the control panel, or hotkeys.
- **Skill engine** — 9 XP rules over the live mic + video analysis, with
  "Speech increased to 24" toasts and character level-ups.

```
mic ─┐
cam ─┼─► server/*.py ──WebSocket (20Hz)──► overlay/index.html ──► OBS browser source
imu ─┤   audio · video · sensors · navigation · gestures · skills
gps ─┘
```

## Quick start

```bash
./run.sh                     # creates .venv, installs deps, starts the server
# or:  source .venv/bin/activate && python -m server.main
```

Open <http://127.0.0.1:8787> for the control panel + live preview.

### Add to OBS

Sources ➜ **Browser** ➜ URL `http://127.0.0.1:8787/overlay/index.html`,
Width `1920`, Height `1080`. Uncheck "Shutdown source when not visible".

Useful flags:

```bash
python -m server.main --sim              # simulate everything, no hardware
python -m server.main --no-video         # keep the mic, fake the camera
python -m server.main --optin-attributes # REQUIRED for face-attribute inference
python -m server.main --ssl-cert certs/cert.pem --ssl-key certs/key.pem
```

---

## 1. Compass data off the device

`heading.mode` picks the transport; `auto` uses whichever source produced data
in the last 5 seconds.

| mode | how | needs |
| --- | --- | --- |
| `phone` | Open `http://<lan-ip>:8787/phone` on the phone paired with the glasses. Streams DeviceOrientation (compass) **and GPS** over WebSocket. | HTTPS on iPhone (see below) |
| `udp` | Any IMU streamer (HyperIMU, Sensor Stream IMU+, your own app) → UDP `5555`. JSON `{"heading": 123.4}` or CSV (`udp_heading_index`). | — |
| `ble` | BLE IMU beacon over Nordic UART service. Set `heading.ble.address` or a `name_hint`. | `pip install bleak` |
| `serial` | USB/serial IMU pushing JSON or CSV lines. | `pip install pyserial` |
| `sim` | Slow drift for layout work. | — |

iOS will not hand over compass/GPS over plain http:

```bash
./scripts/https.sh                 # self-signed cert for your LAN IP
python -m server.main --ssl-cert certs/cert.pem --ssl-key certs/key.pem
```

Android on a hostile network: `./scripts/adb_reverse.sh 8787` then open
`http://localhost:8787/phone` on the phone over USB.

Calibrate with `heading.offset` (degrees). The control panel shows which
transport is live and how stale it is.

> Meta's Wearables Device Access Toolkit does not yet expose a live POV stream
> or raw IMU; the phone/UDP/BLE/serial transports above are the routes that work
> today. `server/devices/meta_glass.py` is where a native bridge goes.

## 2. Maps directions → compass objective

**Best path: Apple Maps on the phone.** Pick the place in the LiveVision
companion's search, or share it from Apple Maps (Share › LiveVision); it resolves the
place with MapKit, routes it with MKDirections, tracks you along it and sends
`{"route": …}` over `/ws/phone`; while that is fresh it wins, the quest marker
points at the *next maneuver*, and the line under the compass reads
"Turn left onto Market St 120 m" over "FERRY BUILDING 1.4 KM · 18 MIN". It can
also draw the compass on the Ray-Ban Display lens. Contract:
[`docs/NAVIGATION.md`](docs/NAVIGATION.md).

Without the phone's route, three server-side ways in, all producing the same
quest marker (bearing + distance + "turn left onto Market St"):

1. `navigation.destination` in `config.yaml` (lat/lon, or `query` geocoded via
   Nominatim). Route comes from OSRM (free, no API key).
2. `POST /api/destination` with `{"link": "<any maps share URL>"}` — Google,
   Apple, Meta or OSM links are parsed for coordinates.
3. `POST /api/route` with steps you paste out of **Meta Maps** (or any app):

```json
{"destination": {"lat": 37.8029, "lon": -122.4058, "name": "Coffee"},
 "steps": [{"lat": 37.779, "lon": -122.419, "instruction": "Turn left onto Market St",
            "distance": 220, "type": "turn"}]}
```

Your position comes from `navigation.origin` or the phone's GPS (`/phone` →
"Share GPS"). The compass draws the objective as a pulsing quest marker with a
distance readout, clamps it to an edge chevron when it is off-screen, and shows
a "you are facing it" arrow when it is dead ahead. Arriving within
`navigation.arrive_m` fires a Skyrim arrival banner.

Live control: control panel "Navigation objective" box, or
`GET /api/navigation`.

## 3. Gesture menu (Neural Band)

The band has no public API yet, so the gesture bus takes names from anything:

```bash
curl -X POST localhost:8787/api/gesture -d '{"gesture":"pinch"}'
```

- `POST /api/gesture` — Stream Deck, hotkeys, a band bridge app
- `WS /ws/gesture` — phone/wearable bridge
- control-panel gesture pad (or **M** to toggle, **←/→** tab, **↑/↓** scroll)
- the `/phone` page has tap / swipe / spread buttons

Default mapping (edit `gestures.mapping`):

| gesture | action |
| --- | --- |
| `tap`, `pinch`, `double_tap` | toggle menu |
| `swipe_left` / `swipe_right` | previous / next tab |
| `swipe_up` / `swipe_down`, `rotate_cw` / `rotate_ccw` | scroll |
| `spread` | close menu |

Tabs: **Skills** (level + XP bars), **Stats** (vitals, activity, sources),
**Objectives** (live navigation + pinned markers).

## 4. Skills

| Skill | Awarded when |
| --- | --- |
| Speech | talking at all (scaled by loudness) |
| Speechcraft | talking to 3+ people in frame |
| Rizz | 1-on-1 conversation — or gender-keyed, see below |
| Agility | running — camera frame-diff **or** phone IMU (3 Hz footfalls) |
| Sneak | slow, deliberate movement (shows a green "hidden" eye over the crosshair) |
| Exploration | you face a new compass sector (16 sectors, 45s cooldown) |
| Bard | loud, sustained, expressive voice |
| Strength | weight lifting: slow, heavy, repetitive reps |
| Combat | boxing: fast repetitive bursts in front of the camera |
| **Intelligence** | reading: a book/PDF/doc app is in focus, or the POV shows many text rows on a still frame. Avatar puts on round glasses. |
| **Enchanting** | coding: a code editor is in focus. Avatar puts on dark glasses with code reflections. |

Strength vs combat vs running is separated by the **shape** of the motion
signal, not just its magnitude: global scene flow vs central-region flow,
transient spike rate, and cadence from zero-crossings.

```
running  high global flow          (> 0.45)
boxing   central flow, 1-6 Hz, ≥1.2 spikes/s
lifting  central flow, 0.15-1.3 Hz, low global flow
walking  low steady flow
```

Intelligence vs Enchanting is driven by the **camera focus** module — a
heuristic that decides "book / reading" vs "code editor" vs "other" from the
POV image itself, so the HUD works on devices where you cannot ask the OS
which app is in the foreground (Meta Ray-Ban Display, phone-as-POV, etc.).
The desktop module is still available but is **informational only**.

How the focus recognizer decides:

1. Count horizontal text-like rows via a vertical Sobel on a 160x120 crop.
2. Measure mean brightness, mean HSV saturation, and the fraction of
   saturated coloured pixels (syntax-highlighted tokens).
3. Combine into `{reading, coding, other}` with a confidence, smoothed with
   an EMA so the label does not flicker.

Verified against synthetic frames: book → `reading 0.72 · 12 text rows`,
code → `coding 0.95 · syntax 0.15`, random → `other`.

You can still push a frontmost app from anywhere with
`POST /api/desktop {app, title}` (Hammerspoon, AutoHotkey, xdotool, the
dashboard button) — it shows up in the dashboard for the audience to see
but does not award skills. Use `POST /api/focus {kind: reading|coding|other}`
only for testing.

Rates live in `config.yaml` under `skills.rules`. Every 10 skill levels is a
character level-up.

### Opt-in face attributes (gender-keyed rizz)

```yaml
attributes: { enabled: true, backend: onnx, model: "models/gender.onnx" }
skills: { rizz: { mode: gender, target: female } }
```

```bash
python -m server.main --optin-attributes
```

**Both are required** — config flag *and* CLI flag. With neither, the module
reports `off` and the control panel says `attributes: off`. Face-attribute
inference is imperfect and biased; it stays dark until you deliberately turn it
on, and the overlay prints "face attributes: opt-in active" in the Stats tab
while it runs. `backend: deepface` also works (`pip install deepface`).

## 5. Video + audio sources

- `video.source`: camera index, file, or **RTSP/HTTP URL**. To get the glasses
  POV in today, run a phone camera app that publishes RTSP and point it here.
- `audio.device`: index or name substring; `audio.gain` / `audio.gate` tune the
  speech gate. macOS: grant the terminal microphone access, otherwise it falls
  back to simulated audio (control panel shows `audio: sim`).

Everything degrades to a simulated source, so the overlay never dies mid-stream.

### Privacy blur (blur bystanders' faces)

The overlay badge (`#privacy`, top-right) mirrors autoclip's face-blur switch.
Say **"blur faces"** and every face is blurred — in the clips autoclip
publishes, and optionally on the live OBS output. **"unblur faces"** /
**"privacy off"** turns it back off; **"toggle face blur"** flips it.

- The blur itself runs in autoclip (ffmpeg patches + an OBS patch scene). A
  browser source cannot read the pixels under it, so the overlay only shows
  state — see [`docs/PRIVACY_BLUR.md`](docs/PRIVACY_BLUR.md).
- Point the badge at your autoclip REST server with
  `data-autoclip="http://127.0.0.1:8899"` on `#privacy` in `overlay/index.html`.
- No autoclip running (or `privacy.enabled: false`) → the badge stays hidden.

```bash
./run_autoclip.sh privacy            # state
./run_autoclip.sh privacy on | off | toggle
```

## HTTP / WS API

| endpoint | purpose |
| --- | --- |
| `GET /api/status` | sources, skills, vitals, nav, ui, attributes, desktop, shout, discovery |
| `GET /api/config` | markers, gesture map, tick rate |
| `GET /api/navigation` | current objective |
| `POST /api/destination` | `{lat,lon}` \| `{query}` \| `{link}` \| `{clear:true}` |
| `POST /api/route` | pre-computed steps from any maps app, or `{route}`: the phone's Apple Maps progress (testing) |
| `POST /api/gesture` | `{gesture}` |
| `POST /api/desktop` | `{app, title}` from an external agent (informational only) |
| `POST /api/focus` | `{kind}` to force-set reading/coding/other (testing) |
| `POST /api/imu` | `{samples:[{ax,ay,az,gx,gy,gz,t}], reset?}` batched devicemotion |
| `WS /ws/imu` | streaming devicomotion (JSON or `[sample,...]`) |
| `GET /api/vtube` | VTube Studio connection status |
| `POST /api/vtube` | `{action}` — fire a VTS hotkey or expression by name |
| `POST /api/avatar` | `{theme}` — switch the procedural avatar's palette |
| `POST /api/shout` | `{word}` to force a shout (testing) |
| `GET /api/progress` | saved skill snapshot |
| `WS /ws` | 20 Hz frame to the overlay |
| `WS /ws/phone` | heading + GPS (+ gestures) from the phone |
| `WS /ws/gesture` | gesture stream |

## Layout

```
server/
  main.py       FastAPI app, WebSocket fan-out, REST control
  audio.py      mic -> level / spectrum / speech gate / visemes / onset
  video.py      camera -> motion / faces / people / activity / text rows
  sensors.py    heading hub: phone · udp · ble · serial · sim
  navigation.py maps directions -> compass objective
  gestures.py   gesture bus -> menu state
  attributes.py opt-in face-attribute classifier
  focus.py      camera-only book-vs-code recognizer (Intelligence / Enchanting)
  imu.py        phone devicemotion hub (Agility / Strength / Combat)
  vtube_studio.py  VTube Studio Plugin API client (auth + hotkey/expression)
  desktop.py    frontmost-app reporting via osascript / xdotool (informational)
  shouts.py     loud-onset Thu'um with cooldown
  discovery.py  OSM POI discovery from GPS
  progress.py   atomic save/load of skill progress
  skills.py     XP rules, levels, vitals
  devices/      Meta Ray-Ban Display bridge helpers
overlay/        OBS browser source (vanilla JS, no build step)
  src/compass.js  hud.js  menu.js  ring.js  avatar.js  net.js
web/            control panel + phone compass bridge
scripts/        https.sh (iOS sensors), adb_reverse.sh (Android over USB)
```

## Cool extras

These came along for free and turned out to be the most fun parts of the HUD:

- **Thu'um shouts** — a sharp loud mic onset (level ≥ 0.82 and rising fast)
  fires a random Thu'um with a 60s cooldown meter at the bottom of the screen.
  A shout is the only thing that pauses your voice-driven magicka drain.
- **Discovery** — every 60s the server queries the OpenStreetMap Overpass API
  for POIs within 80m of your GPS. New names get a `Discovered: <name>` toast
  and +1 exploration XP. Free on foot, no API key.
- **Stealth eye** — when Sneak is active, a green `hidden` eye appears just
  under the crosshair, Skyrim-style.
- **Avatar glasses** — the vtuber puts on round glasses while reading and
  dark "coder" glasses while coding. State text under the avatar shows
  `reading` / `coding` / `boxing` / `lifting` / `running` / `1-on-1` …
- **Persistent skills** — `data/progress.json` is saved every 30s (atomic
  write) and loaded on boot, so you level up across streams.

## Avatar

The overlay ships with a **procedural canvas VTuber** in the bottom-right
corner. Mouth is driven by the server's viseme estimate (loudness + spectral
centroid → `A/E/I/O/U/closed`), eyes blink on a Poisson schedule, body bobs
with the mic level, blushes when Rizz is active, sweats while Agility is
grinding, and swaps round vs dark "coder" glasses depending on the focus
kind. Pick a palette with `avatar.theme` in `config.yaml`:

| theme | look |
| --- | --- |
| `default` | purple, casual |
| `dark_swordsman` | black hair, blue eyes, dark cloak |
| `green_scout` | brown hair, green eyes, forest jacket |
| `silver_knight` | silver hair, red eyes, white cloak |
| `blonde_prince` | blonde, teal eyes, blue coat |
| `hacker` | black hair, neon-green eyes, dark terminal gear |

These are original recolorings — not copies of any specific character.

### Loading a real anime model

HUDstream ships no copyrighted characters. Three legal paths:

1. **VTube Studio** (recommended) — install, load whatever model you own
   (commissioned, your own art, or a CC0/CC-BY model from the model store),
   turn on the Plugin API (Settings → Plugins → "Start API Server"), and
   fill the hotkey IDs in `config.yaml` under `vtube_studio.hotkeys`. The
   HUD triggers those hotkeys automatically whenever the matching skill
   fires or you shout. The auth flow (token cached at
   `~/.cache/hudstream/vts_token.json`) is handled by
   `server/vtube_studio.py`. Verified against a mock Plugin API:

   ```
   connected: True
   token acquired: deadbeef-token
   trigger shout_fus: True
   trigger rizz    : True
   throttle again  : False (within 0.6s cooldown)
   after cooldown  : True
   ```

2. **Free CC0 Live2D base in the overlay** — drop `model.moc3` +
   `texture_00.png` + `live2dcubismcore.min.js` (from
   https://www.live2d.com/en/sdk/download/web/) into
   `overlay/assets/live2d/`, write a `manifest.json`, and set
   `avatar.engine: live2d`. The HUD falls back to procedural if anything
   is missing. See `overlay/assets/live2d/README.md`.

3. **Stick with the procedural avatar** — pick one of the built-in themes
   above; no downloads, no licenses, works today.

### Audio routing (mic → HUD → OBS → VTube Studio)

For the avatar's mouth to stay in sync with what viewers hear, the
microphone that HUDstream captures must be the **same** signal OBS
captures, and (if you use one) VTube Studio listens to:

- **macOS** — install [BlackHole 2ch](https://github.com/ExistentialAudio/BlackHole),
  create a Multi-Output Device in **Audio MIDI Setup** combining BlackHole
  + your speakers, and set it as the system output. HUDstream's mic stays
  as a normal input; OBS adds it as a Mic/Aux source.
- **Windows** — install [VoiceMeeter Banana](https://vb-audio.com/Voicemeeter/banana/),
  set VoiceMeeter Output as OBS's mic source and VTube Studio's mic input.
- **Linux** — PulseAudio monitor of the source the mic sits on, or a
  loopback with `module-loopback`.

VTube Studio's mic lipsync is independent of HUDstream's — the model moves
its mouth because VTube Studio hears the same mic that the procedural
avatar's mouth keys off, so they move together.

## Roadmap

- Native bridge once Meta exposes live video / IMU (or the band's gesture events).
- "Rested" buff: idle for 5 min gives +10% XP for the next minute.
- Reverse-geocoded addresses on top of POI discovery.

