import Foundation

/// 16 kHz / 16-bit mono PCM WAV - what Azure Speech and iFlytek ISE expect,
/// and what server/main.py's read_wav() takes.
public enum WAV {
    public static let sampleRate = 16_000

    /// Wraps raw little-endian 16-bit PCM in a RIFF/WAVE header.
    public static func encode(pcm: Data, sampleRate: Int = WAV.sampleRate, channels: Int = 1) -> Data {
        var data = Data(capacity: 44 + pcm.count)
        func ascii(_ s: String) { data.append(Data(s.utf8)) }
        func le32(_ v: UInt32) { withUnsafeBytes(of: v.littleEndian) { data.append(contentsOf: $0) } }
        func le16(_ v: UInt16) { withUnsafeBytes(of: v.littleEndian) { data.append(contentsOf: $0) } }
        let blockAlign = UInt16(channels * 2)
        ascii("RIFF"); le32(UInt32(36 + pcm.count)); ascii("WAVE")
        ascii("fmt "); le32(16); le16(1); le16(UInt16(channels))
        le32(UInt32(sampleRate)); le32(UInt32(sampleRate) * UInt32(blockAlign)); le16(blockAlign); le16(16)
        ascii("data"); le32(UInt32(pcm.count))
        data.append(pcm)
        return data
    }

    /// Float samples in -1...1 to 16-bit PCM, clipped.
    public static func pcm16(_ samples: [Float]) -> Data {
        var out = Data(capacity: samples.count * 2)
        for x in samples {
            let c = max(-1, min(1, x))
            let v = Int16(c < 0 ? c * 32768 : c * 32767)
            withUnsafeBytes(of: v.littleEndian) { out.append(contentsOf: $0) }
        }
        return out
    }

    /// Linear-interpolation resample (what app.js toWav16k does).
    public static func resample(_ samples: [Float], from rate: Double, to target: Double = Double(WAV.sampleRate)) -> [Float] {
        guard rate != target, !samples.isEmpty else { return samples }
        let ratio = rate / target
        let n = max(1, Int(Double(samples.count) / ratio))
        var out = [Float](repeating: 0, count: n)
        for i in 0..<n {
            let p = Double(i) * ratio
            let i0 = Int(p)
            let i1 = min(samples.count - 1, i0 + 1)
            let f = Float(p - Double(i0))
            out[i] = samples[min(i0, samples.count - 1)] * (1 - f) + samples[i1] * f
        }
        return out
    }

    /// RMS level in dBFS of a block of float samples (-120 for silence).
    public static func rmsDB(_ samples: [Float]) -> Float {
        guard !samples.isEmpty else { return -120 }
        var sum: Float = 0
        for x in samples { sum += x * x }
        let rms = (sum / Float(samples.count)).squareRoot()
        return rms > 0 ? max(-120, 20 * log10(rms)) : -120
    }
}

/// Hands-free end-of-utterance detection: wait for speech, then stop after a
/// stretch of silence. Fed one level per audio block, so it is testable
/// without a microphone.
public struct SpeechEndpointer: Sendable {
    public enum Decision: Equatable, Sendable {
        case listening
        /// spoke, then went quiet (or hit the cap): grade it
        case finished
        /// never started talking: nothing worth uploading
        case noSpeech
    }

    public var speechThresholdDB: Float
    public var silenceToStop: Double
    public var noSpeechTimeout: Double
    public var maxDuration: Double

    public private(set) var elapsed: Double = 0
    public private(set) var spoken: Double = 0
    private var quiet: Double = 0

    public init(speechThresholdDB: Float = -38, silenceToStop: Double = 1.1,
                noSpeechTimeout: Double = 7, maxDuration: Double = 12) {
        self.speechThresholdDB = speechThresholdDB
        self.silenceToStop = silenceToStop
        self.noSpeechTimeout = noSpeechTimeout
        self.maxDuration = maxDuration
    }

    public var heardSpeech: Bool { spoken >= 0.15 }

    public mutating func feed(levelDB: Float, duration: Double) -> Decision {
        elapsed += duration
        if levelDB >= speechThresholdDB {
            spoken += duration
            quiet = 0
        } else {
            quiet += duration
        }
        if elapsed >= maxDuration { return heardSpeech ? .finished : .noSpeech }
        if heardSpeech { return quiet >= silenceToStop ? .finished : .listening }
        return elapsed >= noSpeechTimeout ? .noSpeech : .listening
    }
}
