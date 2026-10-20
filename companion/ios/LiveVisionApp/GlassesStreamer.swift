import AVFoundation
import Foundation
import MWDATCamera
import MWDATCore
import Observation
import os

let log = Logger(subsystem: "com.chromeup.livevision", category: "glasses")

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
    var lastError: String?

    @ObservationIgnored private var configured = false
    @ObservationIgnored private var session: DeviceSession?
    @ObservationIgnored private var cam: Camera?
    @ObservationIgnored private let tokens = ListenerTokenBag()
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
            log.error("Wearables.configure: \(String(describing: error), privacy: .public)")
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
            log.notice("session created for \(String(describing: selector.activeDevice), privacy: .public) of \(self.deviceIds.count) devices")
            session = s
            link = .connecting
            // Subscribe before start(): the streams do not replay, and a quick
            // session (the mock) is already .started when a Task gets to run.
            let errors = s.errorStream(), states = s.stateStream()
            tasks.append(Task { [weak self] in
                for await error in errors {
                    self?.lastError = error.localizedDescription
                    log.error("session error: \(String(describing: error), privacy: .public)")
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
        log.notice("session \(state.description, privacy: .public)")
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
        do {
            try mic.start(forward: !useGlassesMic, into: pump)
        } catch {
            lastError = "Mic: \(error.localizedDescription)"
        }
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

    private func attachCamera() async {
        guard let session, cam == nil, wantsStream else { return }
        do {
            if try await Wearables.shared.checkPermissionStatus(.camera) != .granted,
               try await Wearables.shared.requestPermission(.camera) != .granted {
                lastError = "Camera access for LiveVision is off in the Meta AI app."
                return
            }
        } catch {
            log.notice("camera permission: \(String(describing: error), privacy: .public)")
        }
        let glassesMic = Settings.audioSource == .glasses
        let config = StreamConfiguration(
            // Real glasses: decoded frames for our H.264 encoder. The mock only
            // plays its file as HEVC (Meta's samples all use hvc1 with it);
            // MediaPump decodes that back to pixels so it takes the same path.
            videoCodec: isMock ? .hvc1 : .raw,
            audioCodec: glassesMic ? .pcm(sampleRate: .rate48000, numberOfChannels: 1) : nil,
            resolution: .high,      // 720x1280; DAT steps down by itself on a weak link
            frameRate: 30)
        do {
            guard let c = try session.addCamera(config: config) else {
                lastError = "These glasses have no camera stream."
                return
            }
            cam = c
            let pump = pump
            c.stream.statePublisher.listen { [weak self] state in
                Task { @MainActor in
                    log.notice("camera \(String(describing: state), privacy: .public)")
                    self?.camera = state
                    if state == .streaming, self?.isMock == true { MockRig.refeed() }
                }
            }.store(in: tokens)
            c.stream.errorPublisher.listen { [weak self] error in
                log.error("camera: \(String(describing: error), privacy: .public)")
                Task { @MainActor in self?.lastError = "Camera: \(error.localizedDescription)" }
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
            log.error("addCamera: \(String(describing: error), privacy: .public)")
        }
    }

    /// Frames in / dropped, once a second.
    private func startMeter() {
        meter?.cancel()
        meter = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(1))
                guard let self else { return }
                let c = self.pump.takeCounters()
                self.fpsIn = c.framesIn
                self.droppedFrames += c.dropped
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
