import AVFoundation
import LinguaLensCore
import os

let log = Logger(subsystem: "com.lingualens.app", category: "player")

/// Everything that makes sound or listens.
///
/// * One `.playAndRecord` session for the whole lesson, with the `audio`
///   background mode, so model lines keep playing with the screen locked.
/// * Output goes over A2DP (or the speaker); the glasses' HFP microphone is
///   switched on only for the length of a take, because HFP drops the
///   glasses speakers to 8 kHz phone-call quality.
/// * A silent buffer loops on an output-only AVAudioEngine while a lesson is
///   playing. Between lines there is otherwise no audio at all (waiting for
///   the server, an info countdown), and iOS suspends a background app the
///   moment it goes quiet.
@MainActor
final class AudioEngine: NSObject, AVSpeechSynthesizerDelegate {
    private let synth = AVSpeechSynthesizer()
    private var pending: [ObjectIdentifier: CheckedContinuation<Void, Never>] = [:]

    private let engine = AVAudioEngine()
    private let silence = AVAudioPlayerNode()
    private let tones = AVAudioPlayerNode()
    private let format = AVAudioFormat(standardFormatWithSampleRate: 44_100, channels: 1)!
    private var keepingAlive = false

    let capture = AudioCapture()

    /// Prefer the glasses (HFP) microphone for takes when it is available.
    var preferGlassesMic = true

    private var voiceCursor = 0
    private var voiceCache: [String: [AVSpeechSynthesisVoice]] = [:]
    /// Shown in Settings, so it is obvious when only a compact voice is installed.
    private(set) var lastVoice = "—"

    static func qualityName(_ q: AVSpeechSynthesisVoiceQuality) -> String {
        switch q {
        case .premium: return "Premium"
        case .enhanced: return "Enhanced"
        default: return "Compact - robotic"
        }
    }

    override init() {
        super.init()
        synth.delegate = self
        synth.usesApplicationAudioSession = true
        // pick up Enhanced / Premium voices downloaded while the app runs
        NotificationCenter.default.addObserver(forName: AVSpeechSynthesizer.availableVoicesDidChangeNotification,
                                               object: nil, queue: .main) { [weak self] _ in
            MainActor.assumeIsolated { self?.voiceCache = [:] }
        }
        engine.attach(silence)
        engine.attach(tones)
        engine.connect(silence, to: engine.mainMixerNode, format: format)
        engine.connect(tones, to: engine.mainMixerNode, format: format)

        let nc = NotificationCenter.default
        nc.addObserver(forName: AVAudioSession.interruptionNotification, object: nil, queue: .main) { [weak self] note in
            let type = (note.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt)
                .flatMap(AVAudioSession.InterruptionType.init(rawValue:))
            if type == .ended { MainActor.assumeIsolated { self?.resumeAfterInterruption() } }
        }
        nc.addObserver(forName: .AVAudioEngineConfigurationChange, object: engine, queue: .main) { [weak self] _ in
            MainActor.assumeIsolated { self?.restartKeepAlive() }
        }
    }

    // MARK: session

    /// Playback route: speaker / A2DP glasses, no HFP.
    func activatePlayback() {
        let s = AVAudioSession.sharedInstance()
        do {
            try s.setCategory(.playAndRecord, mode: .default,
                              options: [.allowBluetoothA2DP, .defaultToSpeaker, .allowAirPlay])
            try s.setActive(true)
        } catch {
            log.error("audio session: \(error.localizedDescription, privacy: .public)")
        }
    }

    /// Back to A2DP after a take. Leaving HFP renegotiates the Bluetooth link;
    /// a line spoken during that half second comes out garbled or warbling.
    private func restorePlayback(afterHFP: Bool) async {
        let s = AVAudioSession.sharedInstance()
        if afterHFP { try? s.setPreferredInput(nil) }
        activatePlayback()
        restartKeepAlive()
        if afterHFP { try? await Task.sleep(nanoseconds: 600_000_000) }
    }

    /// Recording route: the glasses' HFP mic if paired, else the phone's.
    /// Returns whether HFP was switched on.
    @discardableResult
    private func activateRecording() -> Bool {
        let s = AVAudioSession.sharedInstance()
        do {
            var options: AVAudioSession.CategoryOptions = [.defaultToSpeaker]
            if preferGlassesMic { options.insert(.allowBluetoothHFP) }
            try s.setCategory(.playAndRecord, mode: .default, options: options)
            try s.setActive(true)
            if preferGlassesMic, let hfp = s.availableInputs?.first(where: { $0.portType == .bluetoothHFP }) {
                try? s.setPreferredInput(hfp)
                return true
            }
        } catch {
            log.error("record session: \(error.localizedDescription, privacy: .public)")
        }
        return false
    }

    var inputName: String {
        AVAudioSession.sharedInstance().currentRoute.inputs.first?.portName ?? "—"
    }

    // MARK: keep-alive

    func startKeepAlive() {
        keepingAlive = true
        activatePlayback()
        restartKeepAlive()
    }

    func stopKeepAlive() {
        keepingAlive = false
        silence.stop()
        engine.stop()
    }

    private func restartKeepAlive() {
        guard keepingAlive else { return }
        do {
            if !engine.isRunning { try engine.start() }
            if !silence.isPlaying {
                let buf = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: 44_100)!
                buf.frameLength = 44_100           // zeros: one second of silence
                silence.scheduleBuffer(buf, at: nil, options: .loops, completionHandler: nil)
                silence.play()
            }
        } catch {
            log.error("keep-alive: \(error.localizedDescription, privacy: .public)")
        }
    }

    private func resumeAfterInterruption() {
        activatePlayback()
        restartKeepAlive()
    }

    // MARK: earcons

    enum Tone { case listen, pass, fail }

    /// Short beeps: the only feedback a learner with the phone in a pocket gets.
    func play(_ tone: Tone) async {
        let notes: [(Double, Double)] = switch tone {
        case .listen: [(880, 0.09)]
        case .pass: [(660, 0.08), (990, 0.12)]
        case .fail: [(330, 0.16)]
        }
        guard engine.isRunning || ((try? engine.start()) != nil) else { return }
        for (freq, dur) in notes {
            let n = AVAudioFrameCount(44_100 * dur)
            let buf = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: n)!
            buf.frameLength = n
            let ch = buf.floatChannelData![0]
            for i in 0..<Int(n) {
                let env = min(1, min(Double(i), Double(Int(n) - i)) / 400)   // no clicks
                ch[i] = Float(sin(2 * .pi * freq * Double(i) / 44_100) * 0.25 * env)
            }
            tones.scheduleBuffer(buf, at: nil, options: [], completionHandler: nil)
        }
        tones.play()
        let total = notes.reduce(0) { $0 + $1.1 }
        try? await Task.sleep(nanoseconds: UInt64((total + 0.05) * 1e9))
    }

    // MARK: speech

    /// Voices for a language, best quality first. Several voices on purpose:
    /// a course that only plays one voice teaches you to understand one voice.
    private func voices(for language: String) -> [AVSpeechSynthesisVoice] {
        if let v = voiceCache[language] { return v }
        let prefix = language.split(separator: "-").first.map(String.init)?.lowercased() ?? language
        // Only natural voices. iOS also lists eight Eloquence character voices
        // per language (Grandma, Grandpa, Rocko, ...), which are deliberately
        // creaky and wobbly - a model line in Grandpa's voice teaches nothing.
        let natural = AVSpeechSynthesisVoice.speechVoices().filter {
            SpeechVoices.isNatural(identifier: $0.identifier, isNovelty: $0.voiceTraits.contains(.isNoveltyVoice))
        }
        let exact = natural.filter { $0.language == language }
        let loose = natural.filter { $0.language.lowercased().hasPrefix(prefix) }
        var found = (exact.isEmpty ? loose : exact).sorted { $0.quality.rawValue > $1.quality.rawValue }
        // a downloaded enhanced / premium voice beats the built-in compact one
        if let best = found.first?.quality { found = found.filter { $0.quality == best } }
        log.notice("voices \(language, privacy: .public): \(found.map(\.identifier).joined(separator: ", "), privacy: .public)")
        voiceCache[language] = found
        return found
    }

    /// Speaks one line and returns when it has finished (or was cancelled).
    func say(_ text: String, language: String, webRate: Double, varyPitch: Bool = true) async {
        let u = AVSpeechUtterance(string: text)
        let vs = voices(for: language)
        // round-robin, deterministic: repeating a line does not reroll the speaker
        if !vs.isEmpty {
            u.voice = vs[voiceCursor % vs.count]
            voiceCursor += 1
        } else {
            u.voice = AVSpeechSynthesisVoice(language: language)
        }
        u.rate = SpeechRate.avRate(fromWeb: webRate)
        // Pitch-shifting is how app.js makes one synth voice pass for several
        // speakers; on a single compact voice it mostly adds artefacts, so
        // only vary it when there really are several speakers to tell apart.
        if varyPitch && vs.count > 1 { u.pitchMultiplier = SpeechRate.pitch(cursor: voiceCursor) }
        // a beat of lead-in so a Bluetooth link waking up does not eat the
        // first syllable
        u.preUtteranceDelay = 0.15
        u.postUtteranceDelay = 0.05
        lastVoice = u.voice.map { "\($0.name) (\(Self.qualityName($0.quality)))" } ?? "system default"
        log.notice("say start [\(language, privacy: .public) \(webRate)] \(text, privacy: .public)")
        await withTaskCancellationHandler {
            await withCheckedContinuation { cont in
                pending[ObjectIdentifier(u)] = cont
                synth.speak(u)
            }
        } onCancel: {
            Task { @MainActor in self.synth.stopSpeaking(at: .immediate) }
        }
        // didFinish means synthesised, not heard: over Bluetooth the last
        // 150-300 ms is still in flight. Switching the route to the HFP mic
        // right now (the next cue is usually a take) would cut it off.
        if !Task.isCancelled {
            let tail = AVAudioSession.sharedInstance().outputLatency + 0.15
            try? await Task.sleep(nanoseconds: UInt64(min(0.6, tail) * 1e9))
        }
        log.notice("say end \(text, privacy: .public)")
    }

    func stopSpeaking() { synth.stopSpeaking(at: .immediate) }

    nonisolated func speechSynthesizer(_ s: AVSpeechSynthesizer, didFinish u: AVSpeechUtterance) {
        let id = ObjectIdentifier(u)
        Task { @MainActor in self.pending.removeValue(forKey: id)?.resume() }
    }

    nonisolated func speechSynthesizer(_ s: AVSpeechSynthesizer, didCancel u: AVSpeechUtterance) {
        let id = ObjectIdentifier(u)
        Task { @MainActor in self.pending.removeValue(forKey: id)?.resume() }
    }

    // MARK: recording

    /// One hands-free take on the HFP mic (when present), then back to A2DP.
    func record(level: (@Sendable (Float) -> Void)? = nil) async throws -> AudioCapture.Take {
        let usedHFP = activateRecording()
        let take: AudioCapture.Take
        do {
            await play(.listen)
            take = try await capture.record(level: level)
        } catch {
            await restorePlayback(afterHFP: usedHFP)
            throw error
        }
        await restorePlayback(afterHFP: usedHFP)
        return take
    }

    func stopRecording() { capture.stop() }

    static func requestMicrophone() async -> Bool {
        await AVAudioApplication.requestRecordPermission()
    }
}
