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
  (standing below 40° from vertical, sitting above 60°); or send `posture`
  yourself.

## Phone side (iOS companion)

Control tab → **Body tracking → avatar**. Each part has a toggle and live status.

| file | does |
|---|---|
| `SensorBridge.swift` | `postureOn`: CoreMotion gravity → `body.gravity` at ~8 Hz on the existing socket |
| `BodyTracker.swift` | attaches DAT **Motion** (30 Hz) to the glasses session the camera holds, re-attaching after reconnects; `.glasses` samples → `head.q`, `.neuralBand` → `body.wrists.<band wrist>`; merges hands + Watch; sends at ~10 Hz |
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
`CMDeviceMotion.attitude` at 25 Hz, and sends
`{"wrist": [w,x,y,z], "side": "left", "hr": 96}` to the iPhone at ~10 Hz over
`WCSession.sendMessage`. Pick the wrist on the Watch.

## Not covered (yet)

- **Hands behind you or at your sides**: no camera view, so they animate,
  except the Neural Band / Watch wrist turning the hand.
- **Lying down, crouching, kneeling**: posture is stand / sit only.
- **Absolute position**: no tracker gives where you are in the room, only
  orientation, so the avatar stays in its bar and leaning isn't detected.
