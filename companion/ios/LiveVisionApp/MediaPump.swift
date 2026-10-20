import AVFoundation
import CoreMedia
import os
import VideoToolbox

/// Puts the glasses' frames on the phone's clock (docs/AUDIO_VIDEO_SYNC.md ①).
///
/// DAT stamps video and glasses audio on the glasses' clock; the phone mic and
/// HaishinKit's audio timeline run on the host clock. Each video frame gives a
/// (glasses PTS, host arrival) pair; once a second one is kept, and a
/// least-squares line over the last 30 maps glasses time to host time - the
/// offset absorbs the Bluetooth delay, the slope the tens-of-ppm drift
/// between the two quartz clocks. A jump of more than a second (the glasses
/// restarted their stream) starts the fit over.
final class ClockMapper: @unchecked Sendable {
    private let lock = NSLock()
    private var samples: [(x: Double, y: Double)] = []
    private var lastSampleAt = -Double.infinity
    private var a = 1.0, b = 0.0
    private var ready = false
    private var lastVideo = -Double.infinity

    /// A video frame: feeds the fit and returns its host time (strictly increasing).
    func mapVideo(_ pts: Double, arrival: Double) -> Double {
        lock.lock(); defer { lock.unlock() }
        if !ready || abs(a * pts + b - arrival) > 1 {
            samples.removeAll()
            a = 1; b = arrival - pts
            ready = true
            lastSampleAt = -.infinity
        }
        if arrival - lastSampleAt >= 1 {
            lastSampleAt = arrival
            samples.append((pts, arrival))
            if samples.count > 30 { samples.removeFirst() }
            fit()
        }
        let t = max(a * pts + b, lastVideo + 0.001)
        lastVideo = t
        return t
    }

    /// Glasses audio: same clock as their video. nil until video has started.
    func mapAudio(_ pts: Double) -> Double? {
        lock.lock(); defer { lock.unlock() }
        return ready ? a * pts + b : nil
    }

    func reset() {
        lock.lock(); defer { lock.unlock() }
        samples.removeAll()
        ready = false
        lastVideo = -.infinity
    }

    private func fit() {
        guard samples.count >= 5, let first = samples.first, let last = samples.last,
              last.x - first.x >= 5 else { return }
        let n = Double(samples.count)
        let mx = samples.map(\.x).reduce(0, +) / n
        let my = samples.map(\.y).reduce(0, +) / n
        var sxy = 0.0, sxx = 0.0
        for s in samples { sxy += (s.x - mx) * (s.y - my); sxx += (s.x - mx) * (s.x - mx) }
        guard sxx > 0 else { return }
        // real crystals are within ~100 ppm; anything wider is jitter, not drift
        a = min(max(sxy / sxx, 0.999), 1.001)
        b = my - a * mx
    }
}

/// Frames from DAT's callbacks to the uplink, in order and off the main actor.
///
/// DAT calls its listeners on its own threads. Each frame is re-stamped there
/// (cheap) and queued; one consumer per medium appends to the encoder in
/// order. A backed-up video queue drops its oldest frame and counts it.
final class MediaPump: @unchecked Sendable {
    /// received: frames DAT handed us; framesIn: frames queued for the encoder.
    struct Counters { var received = 0; var framesIn = 0; var dropped = 0 }

    let clock = ClockMapper()
    private let counters = OSAllocatedUnfairLock(initialState: Counters())
    private var video: AsyncStream<CMSampleBuffer>.Continuation?
    private var audio: AsyncStream<(AVAudioPCMBuffer, AVAudioTime)>.Continuation?
    private var consumers: [Task<Void, Never>] = []

    func start(into uplink: Uplink) {
        stop()
        let (v, vc) = AsyncStream.makeStream(of: CMSampleBuffer.self, bufferingPolicy: .bufferingNewest(15))
        let (a, ac) = AsyncStream.makeStream(of: (AVAudioPCMBuffer, AVAudioTime).self, bufferingPolicy: .bufferingNewest(100))
        video = vc
        audio = ac
        clock.reset()
        counters.withLock { _ in sawFrame = false }
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
            if let pixels = decoder.decode(sb) { enqueue(pixels, timing: &timing) }
            else if first { log.error("first frame has no pixels and does not decode") }
            return
        }
        var out: CMSampleBuffer?
        guard CMSampleBufferCreateCopyWithNewTiming(allocator: nil, sampleBuffer: sb, sampleTimingEntryCount: 1,
                                                    sampleTimingArray: &timing, sampleBufferOut: &out) == noErr,
              let out else { return }
        enqueue(out)
    }

    private let decoder = FrameDecoder()
    private var sawFrame = false

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
        counters.withLock { c in
            c.framesIn += 1
            if case .dropped = r { c.dropped += 1 }
        }
    }

    /// Glasses mic audio from DAT (same clock as its video).
    func pushGlassesAudio(_ buffer: AVAudioPCMBuffer, pts: CMTime) {
        guard let host = clock.mapAudio(pts.seconds) else { return }
        audio?.yield((buffer, AVAudioTime(hostTime: AVAudioTime.hostTime(forSeconds: host))))
    }

    /// Phone mic audio: already on the host clock.
    func pushPhoneAudio(_ buffer: AVAudioPCMBuffer, hostTime: UInt64) {
        audio?.yield((buffer, AVAudioTime(hostTime: hostTime)))
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

/// The phone's own microphone. Also what keeps the app running with the
/// screen off: an active recording session is iOS's licence for the "audio"
/// background mode, so the stream survives the phone going in a pocket.
final class PhoneMic {
    private let engine = AVAudioEngine()
    private(set) var running = false

    /// `forward` false keeps the session alive but sends nothing (glasses mic in use).
    func start(forward: Bool, into pump: MediaPump) throws {
        guard !running else { return }
        let session = AVAudioSession.sharedInstance()
        // No .allowBluetooth (HFP): that would turn the glasses into a phone
        // headset and squeeze their camera link. A2DP output is harmless.
        try session.setCategory(.playAndRecord, mode: .videoRecording,
                                options: [.mixWithOthers, .allowBluetoothA2DP, .defaultToSpeaker])
        try session.setPreferredSampleRate(48_000)
        try session.setActive(true)
        let input = engine.inputNode
        let format = input.outputFormat(forBus: 0)
        guard format.sampleRate > 0 else { throw PhoneMicError.noInput }
        input.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak pump] buffer, time in
            guard forward, let pump, time.isHostTimeValid, let copy = buffer.copy() as? AVAudioPCMBuffer else { return }
            pump.pushPhoneAudio(copy, hostTime: time.hostTime)
        }
        engine.prepare()
        try engine.start()
        running = true
    }

    func stop() {
        guard running else { return }
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        running = false
    }
}

enum PhoneMicError: LocalizedError {
    case noInput
    var errorDescription: String? { "No microphone available." }
}
