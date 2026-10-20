# Body tracking for the avatar

The avatar is driven like a VR body from sparse points: measure what the
wearables can see, infer the rest, and ease any part whose signal drops
back to animation.

| part | source | message field |
|---|---|---|
| head turn / nod / tilt | Ray-Ban Display glasses, DAT Motion `orientation` (source `glasses`) | `head` |
| sitting / standing | iPhone in a front pocket: CoreMotion gravity lies along the thigh | `body.gravity` or `body.posture` |
| walking / running / boxing + cadence | iPhone accelerometer (existing `imu` stream) | `imu` |
| hand positions | glasses camera frames → iOS Vision hand pose | `body.hands` |
| wrist orientation | Apple Watch CMDeviceMotion; Meta Neural Band DAT Motion (source `neuralBand`) | `body.wrists` |
| heart rate | Apple Watch workout (HealthKit live builder) | `body.heart_rate` |
| punches | Apple Watch (100 Hz `userAcceleration`) and Neural Band (DAT Motion accelerometer, 60 Hz) | `body.punch` |

Everything goes to the HUD server on the socket the companion already uses,
`wss://<host>/ws/phone`, as JSON. `POST /api/head` and `POST /api/body` take
the same objects for testing.

## Messages

```jsonc
{"head": {"q": [w, x, y, z], "source": "glasses"}}            // ~10 Hz (DAT Motion default)

{"body": {
  "gravity": [gx, gy, gz],                                     // phone in pocket, 10-15 Hz
  "hands": {                                                   // head-relative metres
    "left":  {"x": -0.18, "y": -0.30, "z": 0.35, "conf": 0.8},
    "right": {"x":  0.20, "y": -0.25, "z": 0.40, "conf": 0.9}},
  "wrists": {
    "left":  {"q": [w, x, y, z], "source": "watch"},
    "right": {"q": [w, x, y, z], "source": "neural_band"}},
  "heart_rate": 96
}}

{"body": {"punch": {"side": "right", "kind": "straight", "strength": 0.8,   // sent the moment it lands
                    "source": "watch"}}}                                   // or "neural_band"
```

Send any subset, as often as it changes. Each part goes stale on its own:
hands after 0.6 s (out of the camera's view), the rest after 2 s.

- **Hands are the wearer's own sides**, head-relative: x = your right, y = up,
  z = forward from your face. The avatar mirrors them like a webcam
  (`avatar.mirror`). Only send a hand you can see.
- **Quaternions are `[w, x, y, z]`.** The first sample after a gap is taken as
  "straight ahead" for the head and "arm relaxed" for a wrist, so the frames of
  the glasses, the watch and the band never need to agree.
- **Posture**: send raw `gravity` and the server decides, with hysteresis
  (standing below 62° from vertical, sitting above 72°: a front-pocket phone
  measured ~42–49° standing and ~84° sitting); or send `posture` yourself.
- **Head level**: yaw drifts back to centre over `head.recenter_s` (20 s),
  pitch and roll more slowly (`pitch_level_s` 30 s, `roll_level_s` 15 s), so a
  reference taken while looking down doesn't leave the avatar staring at the
  floor.

## Punches

The avatar throws a punch on the matching arm (mirrored like the hands) each
time the Watch or the Neural Band feels one, and holds a boxing guard, fists
by the chin, while they keep coming.

**Detection** (`PunchDetector.swift`, the same file in the Watch and iPhone
targets): linear acceleration with gravity removed, in g.

| | value |
|---|---|
| peak | \|a\| > **1.8 g** (2.5 g missed most air punches); the strongest sample of the run is the punch, reported when \|a\| drops back (or 80 ms in) |
| refractory | **180 ms**, and \|a\| must fall below 0.9 g first: the stop at full extension is a second spike of the same punch |
| kind | **uppercut** if > 55 % of the peak is upward (against gravity); **straight** if ≥ 60 % is along the forearm (Watch x axis); else **hook** (also when the wrist swings > 7 rad/s about vertical) |
| strength | 0.3 at 1.8 g → 1.0 at 8 g, never below 0.2 |

- **Watch**: `CMDeviceMotion` at 100 Hz while Start is on (`userAcceleration`
  already excludes gravity). Each punch goes to the phone at once over
  `WCSession.sendMessage` as `{"side", "punch": {...}}`, not on the 10 Hz tick.
- **Neural Band**: DAT Motion runs at **60 Hz** (was 30): a jab's spike lasts
  ~30-50 ms, which 30 Hz catches once at best and often misses. The band's
  accelerometer includes gravity (m/s²), so `BodyTracker` subtracts a slow
  average of it (follows only while the wrist is calm, ~0.4 s). The band's
  axes aren't documented, so it tells straight from hook by wrist rotation only.
  The punch goes to `Settings.bandWrist`.
- **Phone**: relays each punch on `/ws/phone` immediately as `{"body": {"punch": …}}`.

**Server** (`server/body.py`): a punch on the same side within 150 ms of the
last one is the same punch (Watch and band on one wrist) and only raises its
strength. The overlay payload carries `body.punches`, the last 1.5 s of them,
each `{id, side, kind, strength, source, age}` with an increasing `id`: an
overlay plays every id once, skips any older than 0.5 s, and only syncs on its
first payload. `body.punching` stays true 2.5 s after the last punch; while it
is, an idle or walking activity reads as `boxing` (guard up, Combat XP).

**Avatar** (`overlay/src/avatar3d.js`): ~120 ms out (quicker when harder),
~200 ms back to guard, two-bone IK. Straight: forward to the centre line at
chin height. Hook: out and round to the chin, elbow up. Uppercut: dips, then
drives up under the chin. Strength scales reach and speed; the torso and
shoulder turn into it. Test without sensors:
`curl -XPOST localhost:8787/api/body -d '{"punch":{"side":"right","kind":"hook"}}'`.

## Phone side (iOS companion)

Control tab → **Body tracking → avatar**. Each part has a toggle and live status.

| file | does |
|---|---|
| `SensorBridge.swift` | `postureOn`: CoreMotion gravity → `body.gravity` at ~8 Hz on the existing socket |
| `BodyTracker.swift` | attaches DAT **Motion** (60 Hz) to the glasses session the camera holds, re-attaching after reconnects; `.glasses` samples → `head.q`, `.neuralBand` → `body.wrists.<band wrist>`; merges hands + Watch; sends at ~10 Hz; Neural Band punches, relays the Watch's, each at once |
| `HandTracker.swift` | Vision `VNDetectHumanHandPoseRequest` on decoded POV frames (`MediaPump.onPixels`), ~8 Hz on a background queue; depth from the ~9 cm wrist-knuckle span, x/y from `Settings.cameraHFOV` |
| `WatchLink.swift` | WatchConnectivity receiver for the Watch app |
| `BodyViews.swift` | the Control-tab section |

While the glasses stream, phone sensors and body tracking keep running with the
app in the background (the stream's audio background mode keeps it alive);
otherwise they stop with the app as before.

Set **Camera field of view** if the avatar's hand lands nearer or further than
yours (wider = further). Check left/right once: raise your right hand.

## Apple Watch (LiveVisionWatch target)

`LiveVisionWatch/`, embedded in the iPhone app (bundle id
`com.chromeup.livevision.watchkitapp`, watchOS 10+). Start runs an
`HKWorkoutSession` + `HKLiveWorkoutBuilder` (keeps sensors live wrist-down,
gives heart rate; the workout is discarded on Stop), reads
`CMDeviceMotion` at 100 Hz, and sends
`{"wrist": [w,x,y,z], "side": "left", "hr": 96}` to the iPhone at ~10 Hz over
`WCSession.sendMessage`, plus each punch the moment it lands (see Punches).
Pick the wrist on the Watch.

## Not covered (yet)

- **Hands behind you or at your sides**: no camera view, so they animate,
  except the Neural Band / Watch wrist turning the hand.
- **Lying down, crouching, kneeling**: posture is stand / sit only.
- **Absolute position**: no tracker gives where you are in the room, only
  orientation, so the avatar stays in its bar and leaning isn't detected.
