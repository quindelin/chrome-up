import AVFoundation
import CoreMedia
import HaishinKit
import RTMPHaishinKit
import SRTHaishinKit

/// Phone -> VM: encodes the glasses frames and the mic and publishes them to
/// MediaMTX at live/<STREAM_KEY> (docs/PHONE_APP.md).
///
/// HaishinKit 2.2 does the H.264/AAC encoding (VideoToolbox / AudioConverter)
/// and both transports: RTMP (rtmp://<ip>:1935, the default and the tested
/// path) and SRT (srt://<ip>:8890, encrypted, retransmits lost packets -
/// better on cellular, but MediaMTX currently drops HaishinKit's SRT publish
/// after a few seconds, see Settings.transport). It is MIT, maintained (2.2.5, March 2026)
/// and takes raw CMSampleBuffers / AVAudioPCMBuffers, which is exactly what
/// DAT and AVAudioEngine hand us; the commercial alternatives (Larix SDK) and
/// the abandoned ones (LFLiveKit, VideoCore) are not.
///
/// A supervisor loop keeps the publish alive: it reconnects with backoff when
/// the socket drops (tunnel, cell handover) and builds a fresh connection each
/// time, since MediaMTX accepts a new publish on the same path.
actor Uplink {
    enum State: Equatable {
        case idle
        case connecting
        case live
        case reconnecting(attempt: Int, why: String)
    }

    struct Stats: Equatable {
        var kbpsOut = 0
        /// SRT: packets the sender gave up on (too late to be useful).
        var droppedPackets = 0
        var rttMs: Double?
    }

    struct Config {
        var transport: Settings.Transport
        var host: String
        var streamKey: String
        var srtPassphrase: String
        /// Encoded size; DAT's "high" is 720x1280 portrait.
        var videoSize = CGSize(width: 720, height: 1280)
        var videoBitRate = 3_000_000
        var audioBitRate = 96_000
        var frameRate = 30.0

        /// The publish URL, without secrets when `redacted`.
        func url(redacted: Bool = false) -> URL? {
            let key = redacted ? "…" : streamKey
            switch transport {
            case .srt:
                // MediaMTX: streamid "publish:<path>", AES passphrase on that path.
                // HaishinKit splits the query on & and = without percent-decoding,
                // so neither value may contain those (setup.sh makes them hex).
                // latency (ms): how long SRT keeps retrying a lost packet.
                var s = "srt://\(host):8890?streamid=publish:live/\(key)&latency=400"
                if !srtPassphrase.isEmpty { s += "&passphrase=\(redacted ? "…" : srtPassphrase)" }
                return URL(string: s)
            case .rtmp:
                return URL(string: "rtmp://\(host):1935/live/\(key)")
            }
        }
    }

    enum Event: Sendable {
        case state(State)
        case stats(Stats)
    }

    /// State and stats, for the UI.
    nonisolated let events: AsyncStream<Event>
    private let emit: AsyncStream<Event>.Continuation

    private var config: Config?
    private var supervisor: Task<Void, Never>?
    private var srt: SRTConnection?
    private var rtmp: RTMPConnection?
    private var stream: (any StreamConvertible)?
    private var bytesOutPerSecond = 0

    init() {
        (events, emit) = AsyncStream.makeStream(bufferingPolicy: .bufferingNewest(16))
    }

    var isPublishing: Bool { stream != nil }

    func start(_ config: Config) {
        self.config = config
        guard supervisor == nil else { return }
        supervisor = Task { await supervise() }
    }

    /// The VM came back on a new address: the supervisor's next reconnect
    /// publishes there (the old address has nothing listening any more).
    func retarget(host: String) {
        guard config != nil, config?.host != host else { return }
        config?.host = host
    }

    func stop() async {
        supervisor?.cancel()
        supervisor = nil
        await teardown()
        emit.yield(.state(.idle))
    }

    /// One video frame, already on the host clock: pixels for the H.264
    /// encoder, or (passthrough) the glasses' HEVC, which RTMPStream sends as
    /// is over enhanced RTMP (sequence header from its hvcC, then the frames).
    func append(video sampleBuffer: CMSampleBuffer) async {
        await stream?.append(sampleBuffer)
    }

    /// PCM; `when` carries a host time.
    func append(audio buffer: AVAudioPCMBuffer, when: AVAudioTime) async {
        await stream?.append(buffer, when: when)
    }

    fileprivate func report(_ bytesPerSecond: Int) {
        bytesOutPerSecond = bytesPerSecond
    }

    // MARK: - connection

    private func supervise() async {
        var attempt = 0
        while !Task.isCancelled, let config {
            emit.yield(.state(attempt == 0 ? .connecting : .reconnecting(attempt: attempt, why: lastError ?? "connection lost")))
            do {
                try await connect(config)
                attempt = 0
                lastError = nil
                emit.yield(.state(.live))
                // watch it: the sockets flip `connected` when the peer goes away
                while !Task.isCancelled, await isConnected() {
                    try? await Task.sleep(for: .seconds(1))
                    emit.yield(.stats(await stats()))
                }
                if !Task.isCancelled { lastError = "connection lost" }
            } catch {
                lastError = Self.describe(error)
            }
            await teardown()
            guard !Task.isCancelled else { return }
            attempt += 1
            emit.yield(.state(.reconnecting(attempt: attempt, why: lastError ?? "connection lost")))
            // 1, 2, 4, 5, 5 … s: back within ~5 s of the network returning
            try? await Task.sleep(for: .seconds(min(pow(2, Double(attempt - 1)), 5)))
        }
    }

    private var lastError: String?

    private func connect(_ c: Config) async throws {
        guard let url = c.url() else { throw UplinkError.badURL }
        var video = VideoCodecSettings(
            videoSize: c.videoSize,
            bitRate: c.videoBitRate,
            profileLevel: kVTProfileLevel_H264_Main_AutoLevel as String,
            // DAT's bandwidth ladder can drop to 504x896 mid-stream; keep the
            // encoded size (and so the stream's format) fixed and scale.
            scalingMode: .letterbox,
            maxKeyFrameIntervalDuration: 2,     // the VM's segmenter cuts on these
            allowFrameReordering: false,        // no B-frames: lower latency, simpler PTS
            expectedFrameRate: c.frameRate)
        video.frameInterval = 0
        let audio = AudioCodecSettings(bitRate: c.audioBitRate)
        let tap = StatsTap(uplink: self)

        switch c.transport {
        case .srt:
            let connection = SRTConnection()
            let s = SRTStream(connection: connection)
            try await s.setVideoSettings(video)
            try await s.setAudioSettings(audio)
            await s.setBitRateStrategy(tap)
            srt = connection
            try await connection.connect(url)
            await s.publish()
            stream = s
        case .rtmp:
            let connection = RTMPConnection()
            let s = RTMPStream(connection: connection, fcPublishName: c.streamKey)
            try await s.setVideoSettings(video)
            try await s.setAudioSettings(audio)
            await s.setBitRateStrategy(tap)
            rtmp = connection
            _ = try await connection.connect("rtmp://\(c.host):1935/live")
            _ = try await s.publish(c.streamKey)
            stream = s
        }
    }

    private func isConnected() async -> Bool {
        if let srt { return await srt.connected }
        if let rtmp { return await rtmp.connected }
        return false
    }

    private func stats() async -> Stats {
        var s = Stats(kbpsOut: bytesOutPerSecond * 8 / 1000)
        if let p = await srt?.performanceData {
            s.droppedPackets = Int(p.pktSndDropTotal)
            s.rttMs = p.msRTT
            if s.kbpsOut == 0 { s.kbpsOut = Int(p.mbpsSendRate * 1000) }
        }
        return s
    }

    private func teardown() async {
        stream = nil
        bytesOutPerSecond = 0
        if let srt { await srt.close() }
        if let rtmp { try? await rtmp.close() }
        srt = nil
        rtmp = nil
    }

    private static func describe(_ error: any Error) -> String {
        if let e = error as? SRTConnection.Error {
            switch e {
            case .failedToConnect(let reason): return "SRT refused: \(reason) (wrong key or passphrase?)"
            default: return "SRT: \(e)"
            }
        }
        if let e = error as? UplinkError { return e.localizedDescription }
        return String(describing: error)
    }
}

enum UplinkError: LocalizedError {
    case badURL
    var errorDescription: String? { "Set the VPS host and stream key in Settings." }
}

/// HaishinKit hands network reports to a bit-rate strategy; this one only
/// reads them (we keep a fixed 3 Mb/s, SRT absorbs the jitter).
private struct StatsTap: StreamBitRateStrategy {
    let mamimumVideoBitRate = 0
    let mamimumAudioBitRate = 0
    let uplink: Uplink

    func adjustBitrate(_ event: NetworkMonitorEvent, stream: some StreamConvertible) async {
        switch event {
        case .status(let r), .publishInsufficientBWOccured(let r):
            await uplink.report(r.currentBytesOutPerSecond)
        case .reset:
            break
        }
    }
}
