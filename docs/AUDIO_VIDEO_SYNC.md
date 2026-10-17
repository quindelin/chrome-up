# A/V sync — making sure the glasses' audio and video stay locked

This is the single most important engineering problem for the whole
product. If the captions are off by a second, viewers notice instantly
and the clip is dead. If voice commands arrive after the moment they
refer to, the HUD feels laggy and wrong.

There are three places A/V can drift apart. Each one is a contract the
phone app + the cloud pipeline have to honor.

```
[Glasses]   ──DAT frames──▶   [Phone]   ──RTMP──▶   [Cloud VM: autoclip]
   ① capture clock              ② publisher clock             ③ segmenter clock
```

## ① Capture clock (glasses → phone via DAT)

The Meta Wearables Device Access Toolkit exposes camera frames through
`videoFramePublisher` (iOS: `MWDATCamera`, Android:
`WearableCamera.getVideoFramePublisher`). Audio comes on a separate
logical stream. **Both have a PTS, but they're on different clocks.**

Rules for the phone bridge:

1. **Pick one clock to be the master.** The phone's monotonic clock at
   the moment the first DAT frame arrives is `t=0`. Convert every
   subsequent video PTS and audio PTS to "milliseconds since `t=0`".
   This is the only way to interleave them correctly.

2. **Buffer both streams and align by PTS, not by arrival time.**
   Bluetooth reorders packets. The phone's job is to look at the PTS
   on each video frame and each audio sample and decide which one
   comes "first" in the output stream. The publisher does **not** push
   frames as they arrive — it pushes them in PTS order.

3. **Drift correction.** Quartz clocks on the glasses and the phone
   differ by tens of ppm. Over a 5-minute window that accumulates to
   ~15 ms of drift, which is audible as echo or a slow lip-sync
   offset. Sample the video clock against the phone clock once per
   second, fit a linear drift model (`phone_t = a * glasses_t + b`),
   and apply it to every PTS before muxing.

   - iOS: use `CMClockGetHostTimeClock()` plus the
     `CMSampleBufferGetPresentationTimeStamp` of each frame. Compute
     the slope via least-squares over a 30-sample window.
   - Android: use `SystemClock.elapsedRealtime()` and
     `MediaCodec.outputBufferInfo.presentationTimeUs`. Same idea.

4. **Never re-encode on the phone.** The publisher's encoder
   (HaishinKit's `AVAssetWriter`, or `MediaCodec` h264 encoder)
   re-stamps PTS if you give it wrong input. Always pass the
   corrected PTS into the encoder's input, not the original.

The DAT SDK is your friend here: when you subscribe to
`videoFramePublisher`, the `CMSampleBuffer` / `MediaCodec` output
already has accurate PTS for the video. The audio stream from the
glasses needs the same treatment.

## ② Publisher clock (phone → cloud)

Once audio and video are interleaved correctly on the phone, the
RTMP publisher (HaishinKit on iOS, `rtmp-rtsp-stream-client-java` on
Android) sends them up.

Settings that matter:

| setting | value | why |
|---|---|---|
| `videotimestamppolicy` / video PTS | pass through | preserve DAT PTS, don't re-stamp |
| keyframe interval (`-g` equivalent) | **2 s** (60 frames at 30 fps) | forces the segmenter to cut every 30 s on a keyframe boundary; smaller = more keyframes = more bandwidth but tighter sync |
| audio sample rate | 48 kHz AAC | matches the glasses' mic; standard for RTMP |
| audio frame duration | 1024 samples (~21 ms) | AAC's natural frame size |
| video bitrate | 2.5 Mbps | enough for 1080p30, low enough for cellular |
| audio bitrate | 96 kbps | mono voice is fine at 64, but 96 leaves headroom |
| jitter buffer | **300 ms** on the phone | smooths cellular reordering before the encoder sees a frame |
| send buffer (TCP/RTMP) | 1 MB | RTMP sits on TCP; 1 MB absorbs ~3 s of 2.5 Mbps |

**Network smoothing (on the phone).** Cellular links re-order and
drop. Three layers of defense:

1. **Jitter buffer** in the RTMP publisher (300 ms default in
   HaishinKit; set `RTMPStream.videoSettings[.bufferTime]`).
2. **Local rolling buffer** on disk: keep the last **60 seconds** of
   encoded H.264/AAC in an MP4 fragment. When the network comes back
   after an outage, replay the missing tail at 1× to the RTMP
   publisher. (Most RTMP clients don't do this — it's a v2 feature for
   this app.)
3. **Reconnect logic**: if `RTMPConnection` disconnects, the phone
   re-establishes within 5 seconds and the cloud's MediaMTX accepts
   the new publish on the same key. There will be a gap in the
   timeline; **mark it** with a `PipelineEvent` of type
   `stream_gap` carrying `{start, end, seconds_lost}` so downstream
   consumers can skip or stretch.

**Why RTMP, not SRT or WebRTC?** RTMP is what every CDN, every
streaming app, and every phone-side library speaks natively. SRT
gives better recovery but the phone-side libraries are shakier.
WebRTC is best for sub-second latency but needs a signalling server
and a TURN relay. For our use case — *recording* a stream and
producing clips 30–60 s later — RTMP's 1–3 s latency is invisible.

## ③ Segmenter clock (cloud: ffmpeg `-c copy -f segment`)

The cloud pipeline currently runs:

```
ffmpeg -i rtmp://localhost:1935/live/$KEY \
       -c copy -f segment \
       -segment_time 30 -segment_format mpegts \
       -reset_timestamps 1 \
       -strftime 1 /data/incoming/seg_%Y%m%d_%H%M%S.ts
```

This is correct as long as the *input* is in sync. The rules:

1. **`-c copy`**: never re-encode. Re-encoding would re-stamp PTS
   from the segmenter's clock, which has no relation to the glasses'
   clock. Pass-through is the only safe mode.
2. **`-reset_timestamps 1`**: this resets the *output* container's
   timebase to zero, so each segment is independently playable. It
   does **not** affect the internal PTS within a segment.
3. **`-segment_time 30`**: this is a *target*, not a hard cut. The
   segmenter waits for the next keyframe after 30 s, which is why
   the phone must emit a keyframe at least every 2 s.
4. **`-vsync cfr` not set**: don't use it. The glasses' 30 fps is
   already CFR, and forcing CFR can drop audio.
5. **`-fflags +genpts+igndts` not set**: don't use it. We trust the
   incoming PTS.

**PTS reset warning.** If a publisher reconnects (network blip), the
new chunk's PTS starts at zero again. Downstream code must not assume
monotonic PTS across chunks — it must use the wall-clock
`start_wall` recorded when the chunk file appeared, which the
existing `autoclip.buffer.Segment` already does. The `events.jsonl`
log entries also carry `ts` (wall-clock) and `window_t` (seconds
into the current window) for the same reason.

## Verifying sync end-to-end

Drop a test signal that the pipeline can spot:

```bash
# generate a 30s clip with a visual tick + audible beep every second
ffmpeg -re -f lavfi -i "testsrc=size=1280x720:rate=30,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='%{pts\\:hms}':x=20:y=20:fontsize=60:box=1:boxcolor=black@0.6" \
       -f lavfi -i "sine=frequency=1000:beep_factor=4:duration=30" \
       -c:v libx264 -preset ultrafast -g 60 \
       -c:a aac -ar 48000 \
       -f flv rtmp://INGRESS:1935/live/KEY
```

The visual text shows PTS, the beep is at every 1 s. After a cycle,
open a clip and confirm the text says "00:00:00.000" when the beep
starts. If it's off by more than ~40 ms, drift correction is wrong.

## Operational knobs in `autoclip.yaml`

The pipeline exposes these as config (future work; right now the
defaults are good):

```yaml
sync:
  drift_correction: true          # on the phone, recommended
  jitter_buffer_ms: 300           # RTMP publish buffer on the phone
  local_replay_seconds: 60        # phone keeps last 60s on disk for replay
  phone_keyframe_interval: 60     # frames; 60 @ 30fps = 2s
```

The cloud side is intentionally minimal because `-c copy` does the
right thing if the input is right. Don't re-encode.

## Latency budget

| stage | latency |
|---|---|
| glasses capture → DAT frame on phone | 50–200 ms |
| phone drift correction buffer | 100 ms |
| phone encode + RTMP queue | 50 ms |
| cellular RTMP to MediaMTX | 50–500 ms (variable) |
| MediaMTX relay | 5 ms |
| ffmpeg segmenter `-c copy` | 0 ms |
| total glass-to-disk | **255 ms – 855 ms** |

For a 30 s segmenter window and a 30 s cycle period, the wall-clock
end-to-end delay from "word spoken" to "StreamEvent published" is:

```
~30 s segment latency  +  ~5–10 s whisper  +  ~5 s cycle  =  40–45 s
```

That's the current floor. Lowering it requires either:

- **Per-cycle incremental transcription** (re-transcribe only the new
  tail of audio). Whisper doesn't natively support this, but
  `faster-whisper` can be run with the prior decoded text as
  `prefix=` to skip already-decoded audio — this halves latency.
- **On-device command detection** (iOS `SpeechAnalyzer` / Android
  `SpeechRecognizer`) for the small set of trigger phrases, posted
  directly to `/api/autoclip/command`. Sub-second latency, but only
  works for the short-list commands.

For the first ship, the 40 s floor is fine. The HUD agent should
debounce or render "the command arrived, here's the thing it
referred to" rather than expect instant action.
