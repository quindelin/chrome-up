#if os(iOS)
import AVFoundation

/// Records one utterance as 16 kHz / 16-bit mono WAV, stopping by itself when
/// the learner goes quiet (SpeechEndpointer).
///
/// The audio session is the caller's (the app's AudioEngine): it switches the
/// route to the glasses' HFP microphone before a take and back to A2DP after,
/// because HFP drops the speakers to 8 kHz phone-call quality.
public final class AudioCapture: @unchecked Sendable {
    public struct Take: Sendable {
        public var wav: Data?
        public var decision: SpeechEndpointer.Decision
        public var seconds: Double
    }

    private var engine: AVAudioEngine?
    private let lock = NSLock()
    private var samples: [Float] = []
    private var endpointer = SpeechEndpointer()
    private var continuation: CheckedContinuation<Take, Error>?
    private var stopRequested = false

    public private(set) var isRecording = false

    public init() {}

    /// Records until the endpointer decides, `stop()` is called, or the task
    /// is cancelled. The session must already be active with an input route.
    public func record(endpointer: SpeechEndpointer = SpeechEndpointer(),
                       level: (@Sendable (Float) -> Void)? = nil) async throws -> Take {
        let engine = AVAudioEngine()
        let input = engine.inputNode
        let hwFormat = input.outputFormat(forBus: 0)
        guard hwFormat.sampleRate > 0, hwFormat.channelCount > 0 else {
            throw NSError(domain: "LinguaLens", code: 1,
                          userInfo: [NSLocalizedDescriptionKey: "No microphone input available."])
        }
        guard let target = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: Double(WAV.sampleRate),
                                         channels: 1, interleaved: false),
              let converter = AVAudioConverter(from: hwFormat, to: target) else {
            throw NSError(domain: "LinguaLens", code: 2,
                          userInfo: [NSLocalizedDescriptionKey: "Cannot convert \(hwFormat) to 16 kHz."])
        }

        lock.withLock {
            samples = []
            samples.reserveCapacity(WAV.sampleRate * 12)
            self.endpointer = endpointer
            stopRequested = false
        }

        input.installTap(onBus: 0, bufferSize: 2048, format: hwFormat) { [weak self] buffer, _ in
            guard let self else { return }
            let block = Self.convert(buffer, with: converter, to: target)
            let db = WAV.rmsDB(block)
            level?(db)
            let duration = Double(buffer.frameLength) / hwFormat.sampleRate
            self.lock.lock()
            self.samples.append(contentsOf: block)
            var decision = self.endpointer.feed(levelDB: db, duration: duration)
            if self.stopRequested { decision = self.endpointer.heardSpeech ? .finished : .noSpeech }
            self.lock.unlock()
            if decision != .listening { self.finish(decision) }
        }

        engine.prepare()
        try engine.start()
        self.engine = engine
        isRecording = true

        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { cont in
                lock.withLock { continuation = cont }
            }
        } onCancel: {
            self.finish(.noSpeech)
        }
    }

    /// Ends the take now (push-to-talk release, or a "next" from the glasses).
    public func stop() {
        lock.withLock { stopRequested = true }
    }

    private func finish(_ decision: SpeechEndpointer.Decision) {
        lock.lock()
        guard let cont = continuation else { lock.unlock(); return }
        continuation = nil
        let pcm = samples
        let seconds = endpointer.elapsed
        lock.unlock()

        DispatchQueue.main.async { [weak self] in
            self?.engine?.inputNode.removeTap(onBus: 0)
            self?.engine?.stop()
            self?.engine = nil
            self?.isRecording = false
        }
        let wav = decision == .finished ? WAV.encode(pcm: WAV.pcm16(pcm)) : nil
        cont.resume(returning: Take(wav: wav, decision: decision, seconds: seconds))
    }

    private static func convert(_ buffer: AVAudioPCMBuffer, with converter: AVAudioConverter,
                                to format: AVAudioFormat) -> [Float] {
        let ratio = format.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio + 32)
        guard let out = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: capacity) else { return [] }
        var fed = false
        var error: NSError?
        converter.convert(to: out, error: &error) { _, status in
            if fed { status.pointee = .noDataNow; return nil }
            fed = true
            status.pointee = .haveData
            return buffer
        }
        guard error == nil, let ch = out.floatChannelData else { return [] }
        return Array(UnsafeBufferPointer(start: ch[0], count: Int(out.frameLength)))
    }
}
#endif
