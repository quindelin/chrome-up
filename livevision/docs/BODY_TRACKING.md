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

## Phone side (iOS companion) - to build

1. **Posture.** CoreMotion `deviceMotion.gravity`, already running for the
   `imu` stream: add `"body": {"gravity": [...]}` to the same message.
2. **Hands.** Run `VNDetectHumanHandPoseRequest` on the glasses frames the app
   already receives (GlassesStreamer), 5-10 Hz, on a background queue.
   - Wrist point → normalized image x/y.
   - Depth from apparent hand size: `z ≈ k / (wrist→middle-MCP distance in
     image)`, with `k` from one calibration (a hand at arm's length).
   - Camera to head-relative: the glasses camera looks forward from the
     wearer's eyes, so `x = (u - 0.5) * z * tan(hfov/2) * 2`,
     `y = -(v - 0.5) * z * tan(vfov/2) * 2`. Use the camera's real field of
     view; it isn't in the DAT docs, so measure it once.
   - Left vs right: Vision's `chirality`. It is relative to the image, so
     check it once against your real left hand.
3. **Head.** DAT Motion (beta channel) on the existing DeviceSession:
   `samples` with `source == .glasses`, forward `orientation` as `head.q`.
4. **Neural Band wrist.** Same Motion stream, `source == .neuralBand` →
   `body.wrists.<side>.q`, with `source: "neural_band"` (your band's wrist).

## Apple Watch - to build

A small watchOS target in the LiveVision project:

- `HKWorkoutSession` + `HKLiveWorkoutBuilder` (activity type "other").
  Keeps the app and its sensors running with your wrist down, and delivers
  live heart rate. Needs HealthKit entitlements and the user's permission.
- `CMMotionManager.startDeviceMotionUpdates` at ~25 Hz → `attitude.quaternion`.
- `WCSession.sendMessage` to the iPhone at ~10 Hz:
  `{"wrist": {"q": [w,x,y,z]}, "heart_rate": 96}`. watchOS limits most apps'
  own network sockets, so relay through the phone; the companion merges it
  into `body.wrists.<watch wrist>` and `body.heart_rate`.
- Which wrist: a setting (default left), since the band is on the other.

## Not covered (yet)

- **Hands behind you or at your sides**: no camera view, so they animate,
  except the Neural Band / Watch wrist turning the hand.
- **Lying down, crouching, kneeling**: posture is stand / sit only.
- **Absolute position**: no tracker gives where you are in the room, only
  orientation, so the avatar stays in its bar and leaning isn't detected.
