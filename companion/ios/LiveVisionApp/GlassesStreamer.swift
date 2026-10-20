import AVFoundation
import Foundation
import MWDATCamera
import MWDATCore
import Network
import Observation
import os

let log = GlassesLog()

/// os_log plus Documents/glasses.log, so a run on a real phone can be read
/// back without a Mac console: `xcrun devicectl device copy from --device <id>
/// --domain-type appDataContainer --domain-identifier com.chromeup.livevision
/// --source Documents/glasses.log --destination .`
struct GlassesLog: Sendable {
    private static let logger = Logger(subsystem: "com.chromeup.livevision", category: "glasses")
    private static let queue = DispatchQueue(label: "glasses.log")
    private static let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        .appending(path: "glasses.log")

    func notice(_ s: String) { Self.logger.notice("\(s, privacy: .public)"); Self.write(s) }
    func error(_ s: String) { Self.logger.error("\(s, privacy: .public)"); Self.write("ERROR " + s) }

    private static func write(_ s: String) {
        let line = "\(Date().formatted(.iso8601)) \(s)\n"
        queue.async {
            // keep it small: start over past 1 MB
            if let size = try? FileManager.default.attributesOfItem(atPath: url.path)[.size] as? Int, size > 1_000_000 {
                try? FileManager.default.removeItem(at: url)
            }
            if let h = try? FileHandle(forWritingTo: url) {
                h.seekToEndOfFile(); h.write(Data(line.utf8)); try? h.close()
            } else {
                try? Data(line.utf8).write(to: url)
            }
        }
    }
}

/// The phone half of the IRL stream: Meta Ray-Ban Display camera -> VM.
///
/// DAT (Wearables Device Access Toolkit 1.0.1, Developer Mode, same setup as
/// LinguaLens) gives a DeviceSession with the glasses; its Camera capability
/// streams raw 720x1280 frames at up to 30 fps over Bluetooth Classic. Those
/// go through MediaPump (onto the phone's clock) into Uplink (H.264/AAC over
/// SRT or RTMP to live/<STREAM_KEY>). The glasses' battery goes to the HUD's
/// magicka bar via POST /api/glasses.
///
/// Two buttons: Connect (register with the Meta AI app if needed, open a
/// session - battery shows from here) and Start streaming (camera + uplink).
@MainActor
@Observable
final class GlassesStreamer {
    enum Link: Equatable {
        case unavailable(String)    // DAT failed to configure
        case unregistered           // LiveVision not approved in the Meta AI app yet
        case registering
        case idle                   // registered, no session
        case connecting
        case connected
        case paused                 // a notification / call; DAT resumes it by itself
    }

    private(set) var link: Link = .unregistered
    private(set) var deviceName: String?
    /// DAT's camera stream state, while streaming.
    private(set) var camera: StreamState?
    private(set) var uplink: Uplink.State = .idle
    private(set) var stats = Uplink.Stats()
    private(set) var fpsIn = 0
    private(set) var droppedFrames = 0
    private(set) var startedAt: Date?
    private(set) var battery: Int?
    private(set) var charging = false
    private(set) var batterySent: Date?
    private(set) var isMock = false
    /// The user asked to stream (survives reconnects and session pauses).
    private(set) var wantsStream = false
    var lastError: String? {
        didSet { if let lastError, lastError != oldValue { log.error(lastError) } }
    }

    @ObservationIgnored private var configured = false
    @ObservationIgnored private var session: DeviceSession?
    @ObservationIgnored private var cam: Camera?
    /// One bag per camera attempt, so a retry starts with clean listeners.
    @ObservationIgnored private var tokens = ListenerTokenBag()
    /// Which rung of `cameraTiers` the next attach uses; a failed start steps down.
    @ObservationIgnored private var cameraTier = 0
    @ObservationIgnored private var cameraAttempts = 0
    @ObservationIgnored private var deviceToken: (any AnyListenerToken)?
    @ObservationIgnored private var watchedDevice: DeviceIdentifier?
    @ObservationIgnored private var deviceIds: [DeviceIdentifier] = []
    @ObservationIgnored private var tasks: [Task<Void, Never>] = []
    @ObservationIgnored private let up = Uplink()
    @ObservationIgnored private let pump = MediaPump()
    @ObservationIgnored private let mic = PhoneMic()
    @ObservationIgnored private var meter: Task<Void, Never>?
    @ObservationIgnored private var batteryLoop: Task<Void, Never>?
    @ObservationIgnored private var connectAfterRegistration = false

    var isStreaming: Bool { wantsStream }

    /// Once at launch.
    func configure() {
        guard !configured else { return }
        do {
            try Wearables.configure()
            configured = true
        } catch {
            link = .unavailable(error.localizedDescription)
            log.error("Wearables.configure: \(String(describing: error))")
            return
        }
        if Settings.mockGlasses { enableMock() }
        tasks.append(Task { [weak self] in
            for await state in Wearables.shared.registrationStateStream() {
                self?.registrationChanged(state)
            }
        })
        tasks.append(Task { [weak self] in
            for await devices in Wearables.shared.devicesStream() {
                self?.devicesChanged(devices)
            }
        })
        tasks.append(Task { [weak self] in
            guard let self else { return }
            for await event in self.up.events {
                switch event {
                case .state(let s):
                    self.uplink = s
                    if s == .live, self.startedAt == nil { self.startedAt = Date() }
                case .stats(let s): self.stats = s
                }
            }
        })
        batteryLoop = Task { [weak self] in
            // the HUD hides the bar once a reading is 2 minutes old
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(30))
                await self?.sendBattery()
            }
        }
    }

    // MARK: - registration and session

    /// The Meta AI app's callback (CFBundleURLTypes: livevision://).
    func handle(url: URL) {
        Task {
            do { _ = try await Wearables.shared.handleUrl(url) }
            catch { lastError = "Meta AI callback: \(error.localizedDescription)" }
        }
    }

    private func registrationChanged(_ state: RegistrationState) {
        switch state {
        case .registered:
            if link == .unregistered || link == .registering { link = .idle }
            if connectAfterRegistration { connectAfterRegistration = false; connect() }
        case .registering:
            link = .registering
        default:
            if session == nil { link = .unregistered }
        }
    }

    private func devicesChanged(_ devices: [DeviceIdentifier]) {
        deviceIds = devices
        guard let first = devices.first else { deviceName = nil; return }
        deviceName = Wearables.shared.deviceForIdentifier(first)?.nameOrId()
        watchBattery(first)
    }

    /// "Connect glasses": approve LiveVision in the Meta AI app the first
    /// time, then open a session with the first glasses DAT lists.
    func connect() {
        guard configured, session == nil else { return }
        lastError = nil
        if Wearables.shared.registrationState != .registered {
            connectAfterRegistration = true
            link = .registering
            Task {
                do { try await Wearables.shared.startRegistration() }
                catch {
                    connectAfterRegistration = false
                    link = .unregistered
                    lastError = "Registration: \(error.localizedDescription)"
                }
            }
            return
        }
        do {
            let selector: any DeviceSelector = deviceIds.first.map { SpecificDeviceSelector(device: $0) }
                ?? AutoDeviceSelector(wearables: Wearables.shared)
            let s = try Wearables.shared.createSession(deviceSelector: selector)
            log.notice("session created for \(String(describing: selector.activeDevice)) of \(self.deviceIds.count) devices")
            session = s
            link = .connecting
            // Subscribe before start(): the streams do not replay, and a quick
            // session (the mock) is already .started when a Task gets to run.
            let errors = s.errorStream(), states = s.stateStream()
            tasks.append(Task { [weak self] in
                for await error in errors {
                    self?.lastError = error.localizedDescription
                    log.error("session error: \(String(describing: error))")
                }
            })
            tasks.append(Task { [weak self] in
                for await state in states { self?.sessionChanged(state, s) }
            })
            try s.start()
            if s.state == .started { sessionChanged(.started, s) }
        } catch {
            lastError = noGlassesHint(error)
            session?.stop()
            session = nil
            link = .idle
        }
    }

    private func noGlassesHint(_ error: any Error) -> String {
        if case DeviceSessionError.noEligibleDevice = error {
            return "No glasses: wear them, open the Meta AI app once, and keep Bluetooth on."
        }
        return error.localizedDescription
    }

    private func sessionChanged(_ state: DeviceSessionState, _ s: DeviceSession) {
        guard s === session else { return }
        log.notice("session \(state.description)")
        switch state {
        case .started:
            link = .connected
            if let id = s.device?.identifier ?? deviceIds.first { watchBattery(id) }
            // a resume after a pause: the camera is still attached (DAT docs)
            if wantsStream, cam == nil { Task { await attachCamera() } }
        case .paused:
            link = .paused
        case .stopped:
            session = nil
            cam = nil
            camera = nil
            link = .idle
        case .starting:
            link = .connecting
        default:
            break
        }
    }

    func disconnect() {
        Task { await stopStreaming() }
        session?.stop()
        session = nil
        link = Wearables.shared.registrationState == .registered ? .idle : .unregistered
    }

    // MARK: - streaming

    /// "Start streaming": glasses camera + mic -> VM.
    func startStreaming() async {
        guard !wantsStream else { return }
        lastError = nil
        guard let host = Settings.ingestHost, !Settings.streamKey.isEmpty else {
            lastError = UplinkError.badURL.localizedDescription
            return
        }
        wantsStream = true
        startedAt = nil
        let useGlassesMic = Settings.audioSource == .glasses
        if !(await AVAudioApplication.requestRecordPermission()) {
            lastError = "Microphone access is off (Settings > LiveVision): streaming video only."
        }
        LocalNetworkProbe.shared.trigger()
        micForward = !useGlassesMic
        glassesAudioSeen = 0
        cameraStreamingSince = nil
        cameraTier = 0
        cameraAttempts = 0
        pump.start(into: up)
        await up.start(.init(transport: Settings.transport, host: host,
                             streamKey: Settings.streamKey, srtPassphrase: Settings.srtPassphrase))
        startMeter()
        if session == nil { connect() } else if link == .connected { await attachCamera() }
    }

    func stopStreaming() async {
        guard wantsStream else { return }
        wantsStream = false
        cam?.stream.stop()
        cam?.stop()
        cam = nil
        camera = nil
        await tokens.cancelAll()
        pump.stop()
        mic.stop()
        await up.stop()
        meter?.cancel()
        meter = nil
        fpsIn = 0
        droppedFrames = 0
        stats = .init()
        startedAt = nil
    }

    /// Resolution / fps to ask for, best first. DAT's own sample starts at low/24.
    private static let cameraTiers: [(StreamingResolution, UInt)] = [(.high, 30), (.medium, 24), (.low, 24)]
    @ObservationIgnored private var micForward = true
    @ObservationIgnored private var glassesAudioSeen = 0
    /// DAT 1.0.1 ends the whole camera stream with audioStreamingError when
    /// asked for the glasses mic (in-stream audio is beta-channel only), so
    /// after one failure this run streams video only, with the phone mic.
    @ObservationIgnored private var glassesAudioBroken = false

    private func glassesAudioFailed() async {
        guard wantsStream, !glassesAudioBroken else { return }
        glassesAudioBroken = true
        log.notice("glasses mic unavailable (audioStreamingError): camera without audio + phone mic")
        cam?.stop()
        cam = nil
        camera = nil
        let old = tokens
        tokens = ListenerTokenBag()
        await old.cancelAll()
        micForward = true
        mic.forward = true
        lastError = "Glasses mic isn't available yet (DAT beta) - using the phone mic. Mute speakers near the phone to avoid an echo."
        try? await Task.sleep(for: .seconds(1))
        if wantsStream, link == .connected { await attachCamera() }
    }
    @ObservationIgnored private var cameraStreamingSince: Date?

    /// The glasses mic rides in DAT's camera stream (beta in DAT 1.0). If none
    /// has arrived 6 s after the camera started, send the phone mic instead so
    /// the stream is not silent.
    private func checkGlassesMic() {
        guard wantsStream, !micForward, glassesAudioSeen == 0,
              let since = cameraStreamingSince, Date().timeIntervalSince(since) > 6 else { return }
        micForward = true
        mic.forward = true
        log.notice("no glasses audio after 6 s: falling back to the phone mic")
        lastError = "Glasses mic sent no audio - using the phone mic (it hears speakers nearby)."
    }

    /// The phone mic starts once the camera streams: claiming the audio
    /// session first is one suspect for the camera never reaching the glasses.
    private func startMicIfNeeded() {
        guard wantsStream, !mic.running else { return }
        do { try mic.start(forward: micForward, into: pump) }
        catch { lastError = "Mic: \(error.localizedDescription)" }
    }

    private func deviceSummary() -> String {
        guard let id = session?.device?.identifier ?? deviceIds.first,
              let d = Wearables.shared.deviceForIdentifier(id) else { return "no device" }
        return "\(d.nameOrId()) type \(d.deviceType()) link \(d.linkState) don \(d.donState) hinge \(d.hingeState) "
            + "thermal \(d.thermalLevel) battery \(d.batteryLevel.map(String.init) ?? "?") \(d.compatibility())"
    }

    /// The camera gave up (DAT waits ~30 s for the glasses' camera link).
    /// Try again one rung lower, a few times, while the user still wants to stream.
    private func cameraFailed(_ error: StreamError) async {
        guard wantsStream, cam != nil else { return }
        log.notice("camera failed: \(String(describing: error)); \(deviceSummary())")
        cam?.stop()
        cam = nil
        camera = nil
        let old = tokens
        tokens = ListenerTokenBag()
        await old.cancelAll()
        cameraAttempts += 1
        guard cameraAttempts < 6 else {
            lastError = "Camera: \(error.localizedDescription). Gave up after \(cameraAttempts) tries - take the glasses off and on, or restart them."
            return
        }
        cameraTier = min(cameraTier + 1, Self.cameraTiers.count - 1)
        lastError = "Camera: \(error.localizedDescription) - retrying (\(cameraAttempts))…"
        try? await Task.sleep(for: .seconds(3))
        if wantsStream, link == .connected { await attachCamera() }
    }

    private func attachCamera() async {
        guard let session, cam == nil, wantsStream else {
            log.notice("attachCamera skipped: session \(self.session != nil) cam \(self.cam != nil) wants \(self.wantsStream)")
            return
        }
        log.notice("attachCamera tier \(self.cameraTier) mock \(self.isMock): \(self.deviceSummary())")
        // Meta AI's camera grant for LiveVision; asking opens Meta AI.
        do {
            var status = try await Wearables.shared.checkPermissionStatus(.camera)
            log.notice("camera permission: \(String(describing: status))")
            if status != .granted {
                status = try await Wearables.shared.requestPermission(.camera)
                log.notice("camera permission after request: \(String(describing: status))")
            }
            guard status == .granted else {
                lastError = "Camera access for LiveVision is off in the Meta AI app (App connections)."
                return
            }
        } catch {
            log.error("camera permission check failed: \(String(describing: error))")
        }
        let glassesMic = Settings.audioSource == .glasses && !glassesAudioBroken
        let config = StreamConfiguration(
            // HEVC from the glasses, as in all of Meta's samples: with .raw a
            // Ray-Ban Display sat in waitingForDevice and timed out with
            // deviceNotConnected. MediaPump decodes it to pixels for the H.264
            // encoder (the mock only plays hvc1 anyway).
            videoCodec: .hvc1,
            audioCodec: glassesMic ? .pcm(sampleRate: .rate48000, numberOfChannels: 1) : nil,
            // 720x1280@30 first; DAT also steps down by itself on a weak link
            resolution: Self.cameraTiers[cameraTier].0,
            frameRate: Self.cameraTiers[cameraTier].1)
        do {
            guard let c = try session.addCamera(config: config) else {
                lastError = "These glasses have no camera stream."
                return
            }
            cam = c
            let pump = pump
            c.stream.statePublisher.listen { [weak self] state in
                Task { @MainActor in
                    log.notice("camera \(String(describing: state))")
                    self?.camera = state
                    if state == .streaming {
                        if self?.cameraStreamingSince == nil { self?.cameraStreamingSince = Date() }
                        self?.startMicIfNeeded()
                        if self?.isMock == true { MockRig.refeed() }
                    }
                }
            }.store(in: tokens)
            c.stream.errorPublisher.listen { [weak self] error in
                log.error("camera: \(String(describing: error))")
                Task { @MainActor in
                    switch error {
                    case .deviceNotConnected, .deviceNotFound, .timeout: await self?.cameraFailed(error)
                    case .audioStreamingError: await self?.glassesAudioFailed()
                    default: self?.lastError = "Camera: \(error.localizedDescription)"
                    }
                }
            }.store(in: tokens)
            c.stream.videoFramePublisher.listen { frame in
                pump.pushVideo(frame.sampleBuffer)
            }.store(in: tokens)
            if glassesMic {
                c.stream.audioFramePublisher.listen { frame in
                    pump.pushGlassesAudio(frame.pcmBuffer, pts: frame.presentationTimeStamp)
                }.store(in: tokens)
            }
            c.stream.start()
        } catch {
            lastError = "Camera: \(error.localizedDescription)"
            log.error("addCamera: \(String(describing: error))")
        }
    }

    /// Frames in / dropped, once a second.
    private func startMeter() {
        meter?.cancel()
        meter = Task { [weak self] in
            var tick = 0
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))
                guard let self else { return }
                let c = self.pump.takeCounters()
                self.fpsIn = c.framesIn
                self.droppedFrames += c.dropped
                tick += 1
                if tick % 5 == 0 {
                    self.glassesAudioSeen += c.glassesAudio
                self.checkGlassesMic()
                log.notice("meter rx \(c.received)/s queued \(c.framesIn)/s glasses-audio \(c.glassesAudio)/s dropped \(self.droppedFrames) camera \(self.camera.map { String(describing: $0) } ?? "nil") uplink \(String(describing: self.uplink)) link \(String(describing: self.link))")
                }
            }
        }
    }

    // MARK: - battery -> HUD magicka

    private func watchBattery(_ id: DeviceIdentifier) {
        guard id != watchedDevice, let device = Wearables.shared.deviceForIdentifier(id) else { return }
        watchedDevice = id
        deviceToken = device.addDeviceStateListener { [weak self] state in
            Task { @MainActor in
                self?.batteryChanged(state.batteryLevel, state.chargingState == .charging)
            }
        }
        batteryChanged(device.batteryLevel, device.chargingState == .charging)
    }

    private func batteryChanged(_ level: Int?, _ isCharging: Bool) {
        guard let level else { return }
        let changed = level != battery || isCharging != charging
        battery = level
        charging = isCharging
        if changed { Task { await sendBattery() } }
    }

    /// POST https://<host>/api/glasses {"battery", "charging"} (no auth).
    private func sendBattery() async {
        guard let battery, let base = Settings.hudURL else { return }
        var r = URLRequest(url: base.appending(path: "api/glasses"))
        r.httpMethod = "POST"
        r.timeoutInterval = 6
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        r.httpBody = try? JSONSerialization.data(withJSONObject: ["battery": battery, "charging": charging])
        if let (_, resp) = try? await URLSession.shared.data(for: r),
           (resp as? HTTPURLResponse)?.statusCode == 200 {
            batterySent = Date()
        }
    }

    // MARK: - mock glasses

    /// Settings > Mock glasses. Takes effect for the next Connect.
    func setMock(_ on: Bool) async {
        Settings.mockGlasses = on
        await stopStreaming()
        disconnect()
        if on { enableMock() } else { await MockRig.disable(); isMock = false }
    }

    private func enableMock() {
        do {
            try MockRig.enable()
            isMock = true
        } catch {
            lastError = "Mock glasses: \(error.localizedDescription)"
        }
    }
}

/// iOS asks for Local Network access only when an app actually browses the
/// LAN, and Meta's camera path on Ray-Ban Display goes over Wi-Fi to the
/// glasses. Browsing the Bonjour type DAT declares (NSBonjourServices) puts
/// the prompt up when streaming starts, and logs whether access is refused.
final class LocalNetworkProbe: @unchecked Sendable {
    static let shared = LocalNetworkProbe()
    private var browser: NWBrowser?

    func trigger() {
        guard browser == nil else { return }
        let b = NWBrowser(for: .bonjour(type: "_bonjour._tcp", domain: nil), using: .tcp)
        b.stateUpdateHandler = { state in
            switch state {
            case .failed(let e), .waiting(let e): log.notice("local network: \(String(describing: e)) (Settings > LiveVision > Local Network)")
            case .ready: log.notice("local network: browsing")
            default: break
            }
        }
        b.start(queue: .global(qos: .utility))
        browser = b
        // a short browse is enough to raise the prompt / learn the answer
        DispatchQueue.global().asyncAfter(deadline: .now() + 20) { [weak self] in
            self?.browser?.cancel(); self?.browser = nil
        }
    }
}
