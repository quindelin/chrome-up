# Phone app — what the cloud ingest needs from you

The cloud VM does all the heavy work. The phone app's only job is:

1. Subscribe to the glasses' camera stream via the **Meta Wearables Device
   Access Toolkit (DAT)** — specifically `mwdat-camera`'s `videoFramePublisher`.
2. Push those frames, encoded, to a single RTMP URL on your cloud VM.

No transcription, no clipping, no analysis, no rendering. Don't do that
on the phone — iOS will suspend your app, Android will thermal-throttle,
and both run out of battery in under two hours.

This doc is the **contract**: the surface the phone app must present, and
the minimum viable snippets to make it real on iOS and Android. It is not
a full app — that's a separate project.

---

## 1. Contract

The phone must be able to produce a single H.264/AAC RTMP stream and
publish it to:

```
rtmp://<HOST>:1935/live/<STREAM_KEY>
```

where `<HOST>` is a public IP/hostname the phone can reach and
`<STREAM_KEY>` is generated into `deploy/obs-vps/.env` on the server
(`./gcp.sh info` prints it). The
stream may be any resolution between 720p and 1080p, 24–30 fps, 1.5–4
Mbps video + 96–128 kbps AAC. Audio is **optional but recommended** — it
drives transcription and "loud audio" scoring on the server.

The app should also handle:

- **Bluetooth/Wi-Fi reconnection** to the glasses without dropping the
  upstream push.
- **Cellular sleep / background time** by reconnecting the RTMP publish
  on foreground entry.
- **Outage buffering**: when the network is gone, write a short local
  rolling buffer to disk and replay it when the link comes back. A
  60-second delay on a clip is acceptable; total loss is not.

---

## 2. Where to plug into Meta DAT

The relevant package is `com.meta.wearable.camera` on Android and
`MWDATCamera` on iOS. The stream API is `videoFramePublisher`.

```swift
// iOS — start a glasses stream
import MWDATCamera

let cfg = StreamConfig()
cfg.videoResolution = .hd_1080p
cfg.frameRate       = 30
cfg.audioEnabled    = true

let publisher = MWDeviceCamera.shared.videoFramePublisher
publisher.delegate = self
publisher.start(configuration: cfg)
```

```kotlin
// Android — start a glasses stream
import com.meta.wearable.camera.WearableCamera
import com.meta.wearable.camera.StreamConfig
import com.meta.wearable.camera.VideoFramePublisher

val cfg = StreamConfig().apply {
    videoResolution = StreamConfig.VideoResolution.HD_1080P
    frameRate       = 30
    audioEnabled    = true
}

val publisher = WearableCamera.getVideoFramePublisher(this)
publisher.setDelegate(object : VideoFramePublisher.Delegate { … })
publisher.start(cfg)
```

The `delegate` (iOS) / `Delegate` (Android) callbacks hand you encoded
CMSampleBuffers or MediaCodec output buffers ready to feed into an RTMP
publisher. You don't decode.

---

## 3. Publishing RTMP from the phone

### iOS — HaishinKit

`HaishinKit` (Swift, MIT) is the canonical RTMP publisher for iOS.

```swift
import HaishinKit
import AVFoundation

// 1. set up the RTMP connection
let rtmp = RTMPConnection()
rtmp.url = "rtmp://INGRESS_HOST:1935/live"
rtmp.connect("STREAM_KEY")

// 2. attach a stream
let stream = RTMPStream(connection: rtmp)
stream.videoSettings = [
    .width: 1280, .height: 720, .bitrate: 2_500_000
]
stream.audioSettings = [.bitrate: 96_000]

// 3. attach the glasses' CMSampleBuffer output to the stream
//    (in the VideoFramePublisher.delegate callback):
func videoFramePublisher(_ p: VideoFramePublisher,
                         didOutput sampleBuffer: CMSampleBuffer) {
    if stream.hasAudio {
        stream.append(sampleBuffer)   // auto-routes video vs. audio
    } else {
        stream.append(sampleBuffer)
    }
}

stream.publish("STREAM_KEY")
```

### Android — rtmp-rtsp-stream-client-java

```kotlin
import net.ossrs.rtmp.RtmpPublisher   // github.com/pedroSG94/rtmp-rtsp-stream-client-java

val pub = RtmpPublisher(context)
pub.setVideoParams(1280, 720, 30, 2_500_000)
pub.setAudioParams(96_000, 44_100, true)
pub.prepare()

// From the WearableCamera.Delegate callback:
override fun onFrame(sampleBuffer: ByteBuffer, info: FrameInfo) {
    if (info.isVideo) pub.queueVideoFrame(sampleBuffer, info)
    else              pub.queueAudioFrame(sampleBuffer, info)
}

pub.start("rtmp://INGRESS_HOST:1935/live", "STREAM_KEY")
```

---

## 4. Configuration: where do `INGRESS_HOST` and `STREAM_KEY` come from?

The phone app ships with a single settings screen that asks for these two
strings. Persist them in:

- iOS: `Keychain` (not `UserDefaults` — a stream key is a secret).
- Android: `EncryptedSharedPreferences`.

A reasonable onboarding flow:

1. User downloads the app.
2. App shows a screen: "Server URL" and "Stream key". Both pre-fillable
   from a deep link `autoclip://configure?host=…&key=…` so you can email
   or QR-code the credentials to a friend.
3. App requests Meta DAT pairing permission for the glasses.
4. User taps "Start streaming". RTMP publish starts; the loop is alive.

---

## 5. What NOT to do

These are the three things that look like a good idea and aren't:

| anti-pattern | why it fails |
|---|---|
| Run `ffmpeg` as a child process on the phone | iOS App Store rejects; Android suspends; battery dies in 30 min. |
| Transcribe audio on the phone | Whisper-base on phone CPU is 0.3× realtime, thermal-throttles in 20 min. Server has the bytes anyway. |
| Capture using `AVCaptureSession` (iOS) / `CameraX` (Android) directly | You'd be capturing the *phone's* camera, not the *glasses'* camera. The whole point of DAT is the glasses. |

---

## 6. Minimal end-to-end smoke test

Before wiring the phone app, prove the cloud side works with a laptop:

```bash
# 1. publish a fake stream to the cloud
ffmpeg -re -f lavfi -i testsrc=size=1280x720:rate=30 \
       -f lavfi -i sine=frequency=440 \
       -c:v libx264 -preset ultrafast -tune zerolatency \
       -c:a aac -f flv rtmp://INGRESS_HOST:1935/live/STREAM_KEY

# 2. confirm the server is consuming
ssh user@INGRESS_HOST
docker compose logs -f autoclip
# expect: "ffmpeg ... -i rtmp://localhost:1935/live/... " plus incoming/seg_*.ts
```

Once that's green, point the phone app at the same URL and key. If the
phone is pushing, the server will start seeing `.ts` chunks within 2–3
seconds.

---

## 7. A/V sync + network smoothing

This is the part that decides whether the captions look right. The
detailed clock model is in
[`docs/AUDIO_VIDEO_SYNC.md`](AUDIO_VIDEO_SYNC.md). The phone-side
checklist:

1. **Master the phone's monotonic clock at the first DAT frame.** Tag
   every video and audio frame with PTS = monotonic ms - t0. Bluetooth
   reorders packets; never interleave by arrival time.
2. **Drift correction.** Compute a linear model
   `phone_t = a * glasses_t + b` over a 30-sample window, apply to
   every PTS. PPM differences between the two clocks accumulate to
   ~15 ms over 5 minutes — visible in captions.
3. **Jitter buffer (300 ms)** in the RTMP publisher. HaishinKit
   exposes this as `RTMPStream.videoSettings[.bufferTime]`.
4. **Local rolling buffer (60 s).** When cellular drops, replay the
   missing tail on reconnect instead of leaving a gap.
5. **Keyframe every 2 s** (`x264 -g 60` at 30 fps). The cloud
   segmenter cuts on keyframe boundaries; without frequent
   keyframes your "30 s segments" become 30–35 s.
6. **AAC at 48 kHz, 96 kbps.** Anything else drifts against the
   glasses' clock.

The simplest phone-side pipeline (iOS) is:

```
DAT videoFramePublisher ─┐
                         ├─▶ PTS-align + drift correct ─▶ HaishinKit encoder
DAT audio stream       ─┘                                              │
                                                                        ▼
                                                          rtmp://HOST/live/KEY
```

If you don't have a custom audio path (DAT audio is experimental),
synthesize audio from the glasses' mic input or skip audio entirely
— `autoclip` will run without it, just with worse "loud audio" scoring
and no captions.

## 8. Voice command hint

If you also want sub-second voice command latency, add a sidecar
`POST /api/autoclip/command` connection from the phone:

```swift
// iOS: lightweight on-device ASR
import Speech

let recognizer = SFSpeechRecognizer(locale: .current)
recognizer?.supportsOnDeviceRecognition = true

// when "show <thing>" is heard, fire:
let url = URL(string: "http://AUTOCLIP_HOST:8899/api/autoclip/command")!
var req = URLRequest(url: url)
req.httpMethod = "POST"
req.setValue("application/json", forHTTPHeaderField: "Content-Type")
req.httpBody = try JSONSerialization.data(withJSONObject: [
    "text": spoken,
    "intent": "show",
    "target": target,
    "source": "phone",
])
URLSession.shared.dataTask(with: req).resume()
```

This bypasses the cloud's whisper latency (~5 s) and gives the HUD
agent a sub-second response. The full contract for what the HUD
agent does with the event is in
[`docs/VOICE_COMMANDS.md`](VOICE_COMMANDS.md).

---

## 7. Where this code lives (suggested)

```
phone-app/                separate repo / Xcode project
├── ios/                  SwiftUI + HaishinKit
│   ├── AutoclipGlasses/
│   │   ├── ContentView.swift
│   │   ├── StreamConfigView.swift
│   │   ├── DATCameraBridge.swift
│   │   └── RTMPPublisher.swift
│   └── AutoclipGlasses.xcodeproj
└── android/              Kotlin + RTMP-client
    └── app/src/main/java/com/autoclip/glasses/
        ├── MainActivity.kt
        ├── DATCameraBridge.kt
        ├── RTMPPublisher.kt
        └── KeyStore.kt
```

The bridge file on each platform is the only piece that's specific to the
glasses; everything else is generic RTMP plumbing you can lift from any
of a dozen open-source projects.
