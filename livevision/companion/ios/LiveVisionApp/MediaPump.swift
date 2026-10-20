import AVFoundation
import CoreMedia
import os
import VideoToolbox

/// Puts the glasses' frames on the phone's clock (docs/AUDIO_VIDEO_SYNC.md ①).
///
/// DAT stamps video and glasses audio on the glasses' clock; HaishinKit's
/// encoders run on the host clock, sample-accurate and
/// gap-free. Each frame gives `arrival - pts` = clock offset + Bluetooth delay.
/// The delay only ever adds, so the smallest value over the last ~10 s is the
/// best estimate of the offset (and follows the slow drift between the two
/// crystals). Late frames - a Bluetooth stall delivers a second of frames in a
/// burst - therefore never move the timeline. The first version re-based on
/// any frame more than 1 s off, which pushed video ~0.9 s ahead of audio after
/// a stall; OBS then kept restarting the source's audio ("audio is lagging at
/// max audio buffering"), heard as static. Only a real discontinuity (the
/// glasses' pts going backwards or jumping by seconds, i.e. their stream
/// restarted) starts over.
final class ClockMapper: @unchecked Sendable {
    private let lock = NSLock()
    /// (arrival, arrival - pts), oldest first
    private var window: [(t: Double, off: Double)] = []
    private var offset: Double?
    private var lastPts = -Double.infinity
    private var lastArrival = -Double.infinity
    private var lastVideo = -Double.infinity
    private let span = 10.0

    /// A video frame: returns its host time (strictly increasing).
    func mapVideo(_ pts: Double, arrival: Double) -> Double {
        lock.lock(); defer { lock.unlock() }
        let off = arrival - pts
        // glasses stream restarted: pts went back, or leapt far past wall time
        let ptsStep = pts - lastPts, wallStep = arrival - lastArrival
        if offset == nil || ptsStep < 0 || abs(ptsStep - wallStep) > 5 {
            window.removeAll()
            offset = off
        }
        lastPts = pts
        lastArrival = arrival
        window.append((arrival, off))
        while let first = window.first, arrival - first.t > span { window.removeFirst() }
        offset = window.map(\.off).min() ?? off
        let t = max(pts + (offset ?? off), lastVideo + 0.001)
        lastVideo = t
        return t
    }

    /// Glasses audio: same clock as their video. nil until video has started.
    func mapAudio(_ pts: Double) -> Double? {
        lock.lock(); defer { lock.unlock() }
        return offset.map { pts + $0 }
    }

    func reset() {
        lock.lock(); defer { lock.unlock() }
        window.removeAll()
        offset = nil
        lastPts = -.infinity
        lastArrival = -.infinity
        lastVideo = -.infinity
    }
}

/// Frames from DAT's callbacks to the uplink, in order and off the main actor.
///
/// DAT calls its listeners on its own threads. Each frame is re-stamped there
/// (cheap) and queued; one consumer per medium appends to the encoder in
/// order. A backed-up video queue drops its oldest frame and counts it.
final class MediaPump: @unchecked Sendable {
    /// received: frames DAT handed us; framesIn: frames queued for the encoder;
    /// glassesAudio: DAT audio buffers (glasses mic) handed us.
    struct Counters { var received = 0; var framesIn = 0; var dropped = 0; var glassesAudio = 0 }

    let clock = ClockMapper()
    /// Decoded glasses frames for hand tracking (BodyTracker). Called on DAT's
    /// frame thread: keep it cheap, the tracker drops frames it can't use.
    var onPixels: (@Sendable (CVPixelBuffer) -> Void)?
    private let counters = OSAllocatedUnfairLock(initialState: Counters())
    private var video: AsyncStream<CMSampleBuffer>.Continuation?
    private var audio: AsyncStream<(AVAudioPCMBuffer, AVAudioTime)>.Continuation?
    private var consumers: [Task<Void, Never>] = []

    /// Passthrough: the glasses' HEVC goes out as is (no phone encoder, so it
    /// keeps going with the screen locked). Decided on the first frame and
    /// kept for the whole publish: the stream's codec must not change midway.
    func start(into uplink: Uplink, passthrough: Bool = false) {
        stop()
        counters.withLock { _ in
            wantPassthrough = passthrough
            mode = .undecided
            awaitKeyframe = false
        }
        let (v, vc) = AsyncStream.makeStream(of: CMSampleBuffer.self, bufferingPolicy: .bufferingNewest(15))
        let (a, ac) = AsyncStream.makeStream(of: (AVAudioPCMBuffer, AVAudioTime).self, bufferingPolicy: .bufferingNewest(100))
        video = vc
        audio = ac
        clock.reset()
        counters.withLock { _ in sawFrame = false; videoFlowing = false }
        consumers = [
            Task.detached(priority: .userInitiated) { for await f in v { await uplink.append(video: f) } },
            Task.detached(priority: .userInitiated) { for await (b, t) in a { await uplink.append(audio: b, when: t) } },
        ]
    }

    func stop() {
        video?.finish(); audio?.finish()
        video = nil; audio = nil
        consumers.forEach { $0.cancel() }
        consumers = []
    }

    /// Frames received and dropped since the last call.
    func takeCounters() -> Counters {
        counters.withLock { c in defer { c = Counters() }; return c }
    }

    /// A DAT video frame on the glasses' clock: raw pixels from real glasses,
    /// HEVC from the mock (it passes its video file's samples through).
    func pushVideo(_ sb: CMSampleBuffer) {
        let first = counters.withLock { c in c.received += 1; defer { sawFrame = true }; return !sawFrame }
        if first {
            log.notice("first frame: image \(sb.imageBuffer != nil) data \(sb.dataBuffer != nil) samples \(sb.numSamples) pts \(sb.presentationTimeStamp.seconds) format \(String(describing: sb.formatDescription))")
        }
        let arrival = CMClockGetTime(CMClockGetHostTimeClock()).seconds
        let pts = sb.presentationTimeStamp
        let host = pts.isValid ? clock.mapVideo(pts.seconds, arrival: arrival) : arrival
        var timing = CMSampleTimingInfo(duration: sb.duration,
                                        presentationTimeStamp: CMTime(seconds: host, preferredTimescale: 1_000_000_000),
                                        decodeTimeStamp: .invalid)
        if sb.imageBuffer == nil, sb.formatDescription?.mediaType == .video {
            if passthroughFrame(sb) {
                // hand tracking still wants pixels; VideoToolbox refuses to
                // decode while locked, and then the tracker just goes quiet
                if let tap = onPixels, let pixels = decoder.decode(sb) { tap(pixels) }
                var out: CMSampleBuffer?
                guard CMSampleBufferCreateCopyWithNewTiming(allocator: nil, sampleBuffer: sb, sampleTimingEntryCount: 1,
                                                            sampleTimingArray: &timing, sampleBufferOut: &out) == noErr,
                      let out else { return }
                enqueueCompressed(out)
                return
            }
            if let pixels = decoder.decode(sb) { onPixels?(pixels); enqueue(pixels, timing: &timing) }
            else if first { log.error("first frame has no pixels and does not decode") }
            return
        }
        if let pixels = sb.imageBuffer { onPixels?(pixels) }
        var out: CMSampleBuffer?
        guard CMSampleBufferCreateCopyWithNewTiming(allocator: nil, sampleBuffer: sb, sampleTimingEntryCount: 1,
                                                    sampleTimingArray: &timing, sampleBufferOut: &out) == noErr,
              let out else { return }
        enqueue(out)
    }

    private let decoder = FrameDecoder()
    private var sawFrame = false
    private enum Mode { case undecided, passthrough, encode }
    private var wantPassthrough = false
    private var mode = Mode.undecided
    /// a compressed frame was dropped: skip to the next keyframe (frames
    /// after a gap reference what's missing and would smear until then)
    private var awaitKeyframe = false

    /// Pass this frame through untouched? Only HEVC that carries its hvcC
    /// (RTMPStream builds the sequence header from it); decided once.
    private func passthroughFrame(_ sb: CMSampleBuffer) -> Bool {
        if mode == .undecided {
            var ok = false
            if wantPassthrough, let fd = sb.formatDescription,
               CMFormatDescriptionGetMediaSubType(fd) == kCMVideoCodecType_HEVC {
                let atoms = CMFormatDescriptionGetExtension(
                    fd, extensionKey: kCMFormatDescriptionExtension_SampleDescriptionExtensionAtoms) as? [String: Any]
                ok = atoms?["hvcC"] != nil
                if !ok { log.error("passthrough: HEVC without hvcC, re-encoding instead") }
            }
            mode = ok ? .passthrough : .encode
            log.notice("video: \(ok ? "HEVC passthrough" : "H.264 encode")")
        }
        return mode == .passthrough
    }

    private func enqueueCompressed(_ frame: CMSampleBuffer) {
        guard let video else { return }
        if awaitKeyframe {
            guard Self.isKeyframe(frame) else {
                counters.withLock { $0.dropped += 1 }
                return
            }
            awaitKeyframe = false
        }
        let r = video.yield(frame)
        videoFlowing = true
        counters.withLock { c in
            c.framesIn += 1
            if case .dropped = r { c.dropped += 1 }
        }
        if case .dropped = r { awaitKeyframe = true }
    }

    private static func isKeyframe(_ sb: CMSampleBuffer) -> Bool {
        guard let atts = CMSampleBufferGetSampleAttachmentsArray(sb, createIfNecessary: false) as? [[CFString: Any]],
              let first = atts.first else { return true }
        return !((first[kCMSampleAttachmentKey_NotSync] as? Bool) ?? false)
    }
    /// No audio until video flows: MediaMTX sets up the path's tracks from the
    /// first packets, and an audio-only start made it drop the publish
    /// ("received a video packet, but track is not set up") on the first frame.
    private var videoFlowing = false

    private func enqueue(_ pixels: CVPixelBuffer, timing: inout CMSampleTimingInfo) {
        var format: CMVideoFormatDescription?
        var out: CMSampleBuffer?
        guard CMVideoFormatDescriptionCreateForImageBuffer(allocator: nil, imageBuffer: pixels,
                                                           formatDescriptionOut: &format) == noErr, let format,
              CMSampleBufferCreateReadyWithImageBuffer(allocator: nil, imageBuffer: pixels, formatDescription: format,
                                                       sampleTiming: &timing, sampleBufferOut: &out) == noErr,
              let out else { return }
        enqueue(out)
    }

    private func enqueue(_ frame: CMSampleBuffer) {
        guard let video else { return }
        let r = video.yield(frame)
        videoFlowing = true
        counters.withLock { c in
            c.framesIn += 1
            if case .dropped = r { c.dropped += 1 }
        }
    }

    /// Glasses mic audio from DAT (same clock as its video).
    func pushGlassesAudio(_ buffer: AVAudioPCMBuffer, pts: CMTime) {
        counters.withLock { $0.glassesAudio += 1 }
        guard videoFlowing, let host = clock.mapAudio(pts.seconds) else { return }
        audio?.yield((buffer, AVAudioTime(hostTime: AVAudioTime.hostTime(forSeconds: host))))
    }
}

/// Compressed frames (the mock's HEVC) -> pixel buffers, so the mock goes
/// through the same H.264 encoder as real glasses' raw frames.
final class FrameDecoder: @unchecked Sendable {
    private var session: VTDecompressionSession?
    private var format: CMFormatDescription?

    func decode(_ sb: CMSampleBuffer) -> CVPixelBuffer? {
        guard let fd = sb.formatDescription else { return nil }
        if session == nil || format.map({ !CMFormatDescriptionEqual($0, otherFormatDescription: fd) }) ?? true {
            if let session { VTDecompressionSessionInvalidate(session) }
            session = nil
            let attrs = [kCVPixelBufferPixelFormatTypeKey: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,
                         kCVPixelBufferIOSurfacePropertiesKey: [:]] as CFDictionary
            VTDecompressionSessionCreate(allocator: nil, formatDescription: fd, decoderSpecification: nil,
                                         imageBufferAttributes: attrs, outputCallback: nil, decompressionSessionOut: &session)
            format = fd
        }
        guard let session else { return nil }
        // synchronous: the handler runs before this returns
        var result: CVPixelBuffer?
        VTDecompressionSessionDecodeFrame(session, sampleBuffer: sb, flags: [], infoFlagsOut: nil) { status, _, image, _, _ in
            if status == noErr { result = image }
        }
        return result
    }
}

/// Keeps the app running with the screen off: iOS only grants the "audio"
/// background mode to an app with an active audio session, so this plays
/// silence (mixed with others, no microphone) while streaming.
final class BackgroundAudio {
    private let engine = AVAudioEngine()
    private let player = AVAudioPlayerNode()
    private(set) var running = false

    func start() {
        guard !running else { return }
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playback, options: [.mixWithOthers])
            try session.setActive(true)
            let format = AVAudioFormat(standardFormatWithSampleRate: 44_100, channels: 1)!
            engine.attach(player)
            engine.connect(player, to: engine.mainMixerNode, format: format)
            let silence = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 44_100)!
            silence.frameLength = silence.frameCapacity   // zero-filled
            player.scheduleBuffer(silence, at: nil, options: .loops)
            try engine.start()
            player.play()
            running = true
        } catch {
            log.error("background audio: \(String(describing: error))")
        }
    }

    func stop() {
        guard running else { return }
        player.stop()
        engine.stop()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        running = false
    }
}
