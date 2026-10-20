# Privacy blur — blur every face, toggled by voice

You are wearing a camera in public. The people you walk past did not agree to
be on your stream. This is the switch that fixes that.

```
glasses ──► OBS ──► autoclip ──► clips ──► YouTube / IG / X
                       │
                       └─ "blur faces" -> faces blurred on the way out
```

One boolean, two drivers, three ways to flip it.

---

## 1. Turn it on

```yaml
privacy:
  enabled: true          # master switch: nothing runs until this is true
  default_on: true       # boot state
  mode: clip             # clip | obs | both
```

`mode: clip` blurs faces in **every clip autoclip renders** — everything that
gets published. `mode: obs` (or `both`) also blurs faces on the **live OBS
program output**.

Then:

```bash
./run_autoclip.sh privacy            # is it on? what did the detector see?
./run_autoclip.sh privacy off
./run_autoclip.sh privacy toggle
```

---

## 2. Voice commands

| spoken | intent | effect |
|---|---|---|
| `blur faces` | `blur` | on |
| `blur everyone's faces` | `blur` | on |
| `hide the faces` | `blur` | on |
| `privacy mode on` | `blur` | on |
| `turn privacy on` | `blur` | on |
| `start blurring` | `blur` | on |
| `unblur faces` | `unblur` | off |
| `show faces` | `unblur` | off |
| `stop blurring` | `unblur` | off |
| `privacy off` | `unblur` | off |
| `toggle face blur` | `toggle` | flip |
| `toggle privacy` | `toggle` | flip |

The grammar lives in `autoclip/voice.py` (`DEFAULT_PATTERNS`, privacy block at
the top). Add your own phrasings there, or switch to `voice.name: llm` and let
the model read loose phrasing — `blur`/`unblur` are in its intent enum.

Every change publishes a `privacy_status` event on the bus:

```json
{"type":"privacy_status","intent":"privacy","target":"faces","value":"on",
 "extra":{"on":true,"mode":"clip","faces":2}}
```

---

## 3. How the blur actually happens

### 3a. Clips (`mode: clip`, default)

ffmpeg, no plugins, no re-encode of anything you did not already re-encode:

```
[0:v]scale/crop/fps,split=3[b][s0][s1];
[s0]crop=200:220:100:300,boxblur=20:2[p0];
[b][p0]overlay=100:300:enable='between(t,0.000,2.000)'[v0];
[s1]crop=180:200:400:900,boxblur=20:2[p1];
[v0][p1]overlay=400:900:enable='between(t,2.500,5.000)'[vout]
```

One patch per face per time window: crop the region out of a fresh copy of the
frame, blur it, overlay it back at the same coordinates.

Two details that matter:

* **Coordinates.** Faces are detected on frames decoded *through* the reframe
  chain, so the boxes are already in output pixels. A 16:9 source cropped to
  9:16 still gets boxes in the right place.
* **Tracking.** Raw detection jitters and looks like static, so boxes are
  matched frame to frame, smoothed with an EMA, held for `hold_seconds` after
  a missed detection (a blink must not un-blur someone), and collapsed into as
  few time windows as one static rectangle can cover.

Captions burn *after* the blur, so subtitles stay sharp.

### 3b. Live OBS output (`mode: obs`)

OBS has no "blur this rectangle" primitive, so we build one out of things it
does have:

```
Live scene
  ├─ Camera                 (your source, untouched)
  └─ PrivacyBlur            (scene autoclip creates)
       ├─ Camera  crop=face0  pos=face0      <- same source, cropped
       ├─ Camera  crop=face1  pos=face1
       └─ [filter] Blur
```

Every item in `PrivacyBlur` references the **same** source, so OBS renders it
N times off one decoder, and one blur pass covers them all. Toggling off hides
the single item in the live scene — instant, and reversible.

Requirements: OBS 28+ (scenes with filters), obs-websocket 5.x, and
`GetSourceScreenshot` for the frames we detect on. The driver creates the
scene, the items and the filter itself, and only ever touches what it created.

```yaml
privacy:
  mode: both
  obs:
    scene: ""               # "" = whatever scene is live
    source: ""              # "" = autodetect the video source
    patch_scene: "PrivacyBlur"
    update_hz: 3.0          # detection + patch update rate
    blur_type: box          # box | gaussian | bilateral
    blur_size: 25
```

Latency is roughly one detection interval (~0.3 s at 3 Hz): a face is blurred
a beat after it enters frame. That is the honest tradeoff for doing it without
re-encoding your whole program output.

**If OBS refuses any of it**, the driver says so in
`GET /api/autoclip/privacy` → `obs.error` and clips keep rendering. Nothing
raises.

---

## 4. Detector

| `detector` | what it needs | notes |
|---|---|---|
| `auto` (default) | YuNet model if present, else Haar, else fetch YuNet | pick this |
| `yunet` | `face_detection_yunet_2023mar.onnx` | DNN, best on profile/occluded faces |
| `haar` | `cv2.CascadeClassifier` | OpenCV 4.x only — OpenCV 5 removed it |

On a modern install (`opencv-python` 5.x) Haar cascades are gone, so `auto`
fetches the YuNet ONNX once (~230 KB) into `<workdir>/models/`. To keep
everything offline, download it yourself and point at it:

```yaml
privacy:
  auto_download_model: false
  yunet_model: /path/to/face_detection_yunet_2023mar.onnx
```

Without cv2 at all, `status()` reports `detector_available: false` and clips
render untouched. Nothing crashes.

---

## 5. Tuning

| key | default | what it does |
|---|---|---|
| `strength` | 20 | blur radius in px (clamped to half the box) |
| `padding` | 0.25 | grow each box by this fraction — covers hair and chin |
| `max_faces` | 4 | tracked faces at once |
| `min_face_px` | 24 | ignore anything smaller (distant crowd, noise) |
| `sample_fps` | 2.0 | clip scan rate |
| `scan_width` | 640 | clip scan resolution |
| `hold_seconds` | 0.8 | keep a patch after a missed frame |
| `persist` | true | remember on/off in `<workdir>/privacy.json` |

`padding` is the one to reach for first: faces detected tightly still show
hair, ears and jawline. `strength` above ~25 on a small box stops looking like
a blur and starts looking like a smudge.

---

## 6. Surfaces

```bash
# CLI
./run_autoclip.sh privacy [status|on|off|toggle]

# REST
curl -s localhost:8899/api/autoclip/privacy
curl -s -XPOST localhost:8899/api/autoclip/privacy -d '{"on":true}'
curl -s -XPOST localhost:8899/api/autoclip/privacy -d '{"toggle":true}'

# SSE (the overlay badge uses both)
GET /api/autoclip/events
```

MCP: `autoclip_privacy_status`, `autoclip_privacy_set`.

---

## 7. The overlay badge

An OBS browser source **cannot read the pixels underneath it** — there is no
API for that, in any browser. So the blur itself lives in autoclip (§3), and
the overlay shows you that it is on.

`overlay/index.html` ships a badge wired to autoclip's REST server:

```html
<div id="privacy" class="hidden" data-autoclip="http://127.0.0.1:8899">
```

It polls `/api/autoclip/privacy` every 5 s and subscribes to
`/api/autoclip/events` for instant updates. Two things to know:

* The overlay is served by the HUD server on a different port, so it is a
  cross-origin call. autoclip enables CORS by default (`server.cors: true`);
  turn it off and the badge goes dark.
* `EventSource` cannot send an `Authorization` header, so leave
  `server.api_token` empty if you want the badge and a token if you do not.
