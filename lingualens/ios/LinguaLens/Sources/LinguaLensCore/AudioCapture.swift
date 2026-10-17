import AVFoundation

/// Records one utterance as 16 kHz / 16-bit mono PCM WAV - what Azure Speech
/// and iFlytek ISE both expect.
///
/// With Ray-Ban Display paired, setting the audio session to a Bluetooth HFP
/// input routes this to the glasses microphone array, so the learner never has
/// to reach for the phone.
public final class AudioCapture {
    public static let sampleRate: Double = 16000

    private let engine = AVAudioEngine()
    private var pcm = Data()
    private let lock = NSLock()

    public var isRecording = false

    public init() {}

    /// Call once before the first recording (also routes to the glasses mic).
    public func configureSession(preferGlassesMic: Bool = true) throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playAndRecord, mode: .default, options: [.defaultToSpeaker, .allowBluetooth])
        if preferGlassesMic {
            // HFP input = the glasses microphone array when the glasses are paired
            let hfp = session.availableInputs?.first { $0.portType == .bluetoothHFP }
            if let hfp { try? session.setPreferredInput(hfp) }
        }
        try session.setActive(true)
    }

    public func start() throws {
        guard !isRecording else { return }
        pcm = Data()
        let input = engine.inputNode
        let format = AVAudioFormat(commonFormat: .pcmFormatInt16,
                                   sampleRate: Self.sampleRate,
                                   channels: 1,
                                   interleaved: true)!
        // convert from the hardware rate if the device is not natively 16 kHz
        input.installTap(onBus: 0, bufferSize: 4096, format: input.outputFormat(forBus: 0)) { [weak self] buffer, _ in
            guard let self else { return }
            guard let converted = self.convert(buffer, to: format) else { return }
            let bytes = Data(bytes: converted.int16ChannelData!.pointee,
                             count: Int(converted.frameLength) * 2)
            self.lock.lock(); self.pcm.append(bytes); self.lock.unlock()
        }
        engine.prepare()
        try engine.start()
        isRecording = true
    }

    public func stop() -> Data? {
        guard isRecording else { return nil }
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        isRecording = false
        lock.lock(); let data = pcm; lock.unlock()
        return data.isEmpty ? nil : Self.wav(from: data, sampleRate: Int(Self.sampleRate))
    }

    private func convert(_ buffer: AVAudioPCMBuffer, to format: AVAudioFormat) -> AVAudioPCMBuffer? {
        if buffer.format.sampleRate == format.sampleRate { return buffer }
        guard let converter = AVAudioConverter(from: buffer.format, to: format) else { return nil }
        let ratio = format.sampleRate / buffer.format.sampleRate
        guard let out = AVAudioPCMBuffer(pcmFormat: format,
                                         frameCapacity: AVAudioFrameCount(Double(buffer.frameLength) * ratio)) else { return nil }
        var error: NSError?
        converter.convert(to: out, error: &error) { _, status in
            status.pointee = .haveData
            return buffer
        }
        return error == nil ? out : nil
    }

    /// Wraps raw 16-bit PCM in a RIFF/WAVE header.
    public static func wav(from pcm: Data, sampleRate: Int) -> Data {
        var data = Data()
        func ascii(_ s: String) { data.append(s.data(using: .ascii)!) }
        func le(_ value: UInt32) {
            var v = value.littleEndian
            data.append(Data(bytes: &v, count: 4))
        }
        func le16(_ value: UInt16) {
            var v = value.littleEndian
            data.append(Data(bytes: &v, count: 2))
        }
        let byteRate = UInt32(sampleRate) * 2
        ascii("RIFF"); le(UInt32(36 + pcm.count)); ascii("WAVE")
        ascii("fmt "); le(16); le16(1); le16(1)
        le(UInt32(sampleRate)); le(byteRate); le16(2); le16(16)
        ascii("data"); le(UInt32(pcm.count))
        data.append(pcm)
        return data
    }
}
