import Foundation
import LinguaLensCore
import MWDATCore
import MWDATDisplay
import MWDATInputs
import Observation

/// Meta Ray-Ban Display over the Wearables Device Access Toolkit (DAT 1.0.1,
/// the same version as the Android wrapper).
///
/// The transport only: connecting, keeping the display alive through
/// interruptions, and drawing whatever screen GlassesMenu hands it. What the
/// screens are lives in GlassesMenu.
///
/// Optional in every way: with no glasses, no Meta AI app or no registration
/// the lesson plays through the phone exactly the same.
@MainActor
@Observable
final class GlassesLink {
    enum Command { case talk, next, repeatLine, pause, playPause }

    private(set) var status = "not connected"
    private(set) var registered = false
    private(set) var deviceName: String?
    /// A session with the glasses is running.
    private(set) var connected = false
    /// Something of ours is on the glasses display right now.
    private(set) var displayActive = false

    @ObservationIgnored var onCommand: ((Command) -> Void)?
    /// The display (re)started and needs the current screen.
    @ObservationIgnored var onDisplayReady: (() -> Void)?
    /// Called after a voice launch has put the lesson back on the glasses.
    @ObservationIgnored var onVoiceLaunch: (() -> Void)?

    @ObservationIgnored private var configured = false
    @ObservationIgnored private var session: DeviceSession?
    @ObservationIgnored private var display: Display?
    @ObservationIgnored private var displayReady = false
    @ObservationIgnored private var inputsAttached = false
    /// The raw-gesture subscription covers the touchpad and band (audio-only
    /// mode) rather than just the physical buttons (display mode).
    @ObservationIgnored private var inputsWide = false
    @ObservationIgnored private var wantDisplay = true
    @ObservationIgnored private var wasPaused = false
    @ObservationIgnored private var tasks: [Task<Void, Never>] = []
    @ObservationIgnored private var lastView: FlexBox?
    @ObservationIgnored private var keepAwake: Task<Void, Never>?
    // "Hey Meta, start LinguaLens"
    @ObservationIgnored private var voice: VoiceInvocationsStream?
    @ObservationIgnored private var voiceTokens: [any AnyListenerToken] = []
    private var deviceIds: [DeviceIdentifier] = []

    /// Why a device might not be eligible: link, compatibility, worn, type.
    var diagnostics: String {
        let rows = deviceIds.compactMap { id -> String? in
            guard let d = Wearables.shared.deviceForIdentifier(id) else { return nil }
            return "\(d.nameOrId()): \(d.deviceType().rawValue), link \(d.linkState), "
                + "\(d.compatibility()), \(d.donState), display \(d.supportsDisplay())"
        }
        return rows.isEmpty ? "DAT sees no devices" : rows.joined(separator: "\n")
    }

    /// Once at launch.
    func configure() {
        guard !configured else { return }
        do {
            try Wearables.configure()
            configured = true
        } catch {
            status = "DAT unavailable: \(error.localizedDescription)"
            log.error("Wearables.configure: \(String(describing: error), privacy: .public)")
            return
        }
        tasks.append(Task { [weak self] in
            for await state in Wearables.shared.registrationStateStream() {
                self?.registered = (state == .registered)
                if state == .registered, self?.session == nil { self?.status = "registered" }
            }
        })
        tasks.append(Task { [weak self] in
            for await devices in Wearables.shared.devicesStream() {
                guard let self else { return }
                self.deviceIds = devices
                if let first = devices.first { self.listenForVoice(on: first) }
                let names = devices.compactMap { Wearables.shared.deviceForIdentifier($0)?.nameOrId() }
                self.deviceName = names.first
                if self.registered && self.session == nil {
                    self.status = names.isEmpty ? "no glasses nearby" : "found \(names[0])"
                }
            }
        })
    }

    /// Opens the Meta AI app to approve LinguaLens; it calls back via the URL scheme.
    func register() async {
        guard configured else { return }
        do {
            try await Wearables.shared.startRegistration()
            status = "approve LinguaLens in the Meta AI app"
        } catch {
            status = "registration: \(error.localizedDescription)"
        }
    }

    /// The Meta AI app's callback (CFBundleURLTypes: lingualens://).
    func handle(url: URL) {
        Task {
            do { _ = try await Wearables.shared.handleUrl(url) }
            catch { status = "callback: \(error.localizedDescription)" }
        }
    }

    func connect(withDisplay: Bool) {
        guard configured, session == nil else { return }
        wantDisplay = withDisplay
        do {
            // Target the glasses DAT already listed; AutoDeviceSelector only
            // picks a device it considers active, and falls back to nothing.
            let selector: any DeviceSelector = deviceIds.first.map { SpecificDeviceSelector(device: $0) }
                ?? AutoDeviceSelector(wearables: Wearables.shared)
            let s = try Wearables.shared.createSession(deviceSelector: selector)
            session = s
            inputsAttached = false
            status = "connecting…"
            tasks.append(Task { [weak self] in
                for await error in s.errorStream() {
                    guard let self else { return }
                    self.status = "session: \(error.localizedDescription) — \(self.diagnostics)"
                    log.error("session error: \(String(describing: error), privacy: .public) \(self.diagnostics, privacy: .public)")
                }
            })
            tasks.append(Task { [weak self] in
                for await state in s.stateStream() {
                    self?.sessionChanged(state, s)
                }
            })
            try s.start()
        } catch {
            status = "session: \(error.localizedDescription) — \(diagnostics)"
            log.error("session: \(String(describing: error), privacy: .public) \(self.diagnostics, privacy: .public)")
            session?.stop()
            session = nil
        }
    }

    /// The session's lifecycle, including the interruptions that used to
    /// leave the display dead.
    ///
    /// A notification, a call, or a one-finger tap on the temple PAUSES the
    /// session (DAT session lifecycle). When it comes back to STARTED, iOS
    /// expects the app to put its capabilities back itself - but the display
    /// is still attached, so the old code's addDisplay() failed with
    /// capabilityAlreadyActive and nothing was ever drawn again. Now a resume
    /// restarts the existing display, or simply redraws the current screen.
    private func sessionChanged(_ state: DeviceSessionState, _ s: DeviceSession) {
        switch state {
        case .started:
            connected = true
            status = "connected" + (deviceName.map { " · \($0)" } ?? "")
            if !inputsAttached { attachInputs(to: s) }
            if wantDisplay {
                if let display {
                    if displayReady { redraw() } else { display.start() }
                } else {
                    attachDisplay(to: s)
                }
            }
            wasPaused = false
        case .paused:
            // Do not touch a paused session (DAT docs): it resumes on its own.
            wasPaused = true
            status = "paused - it comes back after the notification"
        case .stopped:
            connected = false
            status = "disconnected"
            keepAwake?.cancel()
            display = nil; displayReady = false; displayActive = false
            inputsAttached = false
            session = nil   // so Connect / Show on glasses starts afresh
        default:
            status = "\(state)"
        }
    }

    func disconnect() {
        keepAwake?.cancel()
        display?.stop()
        session?.stop()
        session = nil
        display = nil
        displayReady = false
        displayActive = false
        connected = false
        inputsAttached = false
        status = registered ? "registered" : "not connected"
    }

    /// Which raw gestures we take for ourselves.
    ///
    /// With our screens on the glasses, the touchpad and Neural Band belong to
    /// the display: a swipe moves between buttons and a select presses one.
    /// Subscribing to them as raw Inputs consumed exactly those gestures, so
    /// the menu ignored every swipe and tap ("Requesting only what you need
    /// avoids consuming interactions that the ... on-glasses display would
    /// otherwise handle" - DAT Inputs docs). So with the display on we take
    /// only the physical camera and action buttons, as Start / Stop. Without
    /// a display (audio only) the touchpad and band drive the lesson.
    private func inputsConfiguration() -> InputsConfiguration {
        wantDisplay
            ? InputsConfiguration(sources: [.captureButton, .actionButton], consumeBack: false)
            : InputsConfiguration()
    }

    private func attachInputs(to s: DeviceSession) {
        do {
            if let inputs = try s.addInputs(configuration: inputsConfiguration()) {
                inputsAttached = true
                inputsWide = !wantDisplay
                tasks.append(Task { [weak self] in
                    for await event in inputs.events { self?.route(event) }
                })
            }
        } catch {
            log.error("inputs: \(String(describing: error), privacy: .public)")
        }
    }

    private func attachDisplay(to s: DeviceSession) {
        do {
            let d = try s.addDisplay()
            display = d
            tasks.append(Task { [weak self] in
                for await state in Self.states(of: d) {
                    guard let self else { return }
                    self.displayReady = (state == .started)
                    self.displayActive = self.displayReady
                    if state == .started { self.drawCurrent() }
                    if state == .stopped { self.keepAwake?.cancel() }
                }
            })
            d.start()
        } catch {
            log.error("display: \(String(describing: error), privacy: .public)")
        }
    }

    /// Put LinguaLens on the glasses: connect if needed, restart a display
    /// that was closed (Back, or the system), or just redraw. This is the
    /// phone's "Connect glasses" / "Show on glasses" button and Play.
    func showOnGlasses() {
        guard configured else { return }
        wantDisplay = true
        guard let session else { connect(withDisplay: true); return }
        if inputsAttached && inputsWide {
            // started audio-only: hand the touchpad back to the display
            try? session.removeInputs()
            inputsAttached = false
            attachInputs(to: session)
        }
        if let display {
            if !displayReady { display.start() } else { drawCurrent() }
        } else {
            attachDisplay(to: session)
        }
    }

    /// "Hey Meta, start LinguaLens" brings the lesson back from the glasses,
    /// without taking the phone out. Needs the Voice Invocation permission
    /// for this app in the Wearables Developer Center; without it the stream
    /// starts and simply never fires.
    private func listenForVoice(on device: DeviceIdentifier) {
        guard voice == nil else { return }
        do {
            let stream = try VoiceInvocationsStream(wearables: Wearables.shared)
            voiceTokens.append(stream.invocationsPublisher.listen { [weak self] invocation in
                guard let launch = invocation as? LaunchApp else { return }
                Task { @MainActor in
                    self?.showOnGlasses()
                    self?.onVoiceLaunch?()
                    _ = await launch.responseHandle.sendSuccess(actionOutput: nil)
                }
            })
            voiceTokens.append(stream.errorPublisher.listen { error in
                log.notice("voice invocations: \(String(describing: error), privacy: .public)")
            })
            try stream.start(deviceIdentifier: device)
            voice = stream
        } catch {
            log.notice("voice invocations unavailable: \(String(describing: error), privacy: .public)")
        }
    }

    private static func states(of d: Display) -> AsyncStream<DisplayState> {
        AsyncStream { cont in
            let token = d.statePublisher.listen { cont.yield($0) }
            cont.onTermination = { _ in _ = token }
        }
    }

    private func route(_ event: InputEvent) {
        switch event {
        // audio-only mode: the touchpad and band drive the lesson
        case .select: if !displayReady { onCommand?(.talk) }
        case .nav(let dir, _, _):
            if !displayReady { onCommand?(dir == .left || dir == .up ? .repeatLine : .next) }
        case .back: onCommand?(.pause)
        // both modes: the camera or action button is Start / Stop
        case .capture(let press, _, _): if press == .shortPress { onCommand?(.playPause) }
        case .button: onCommand?(.playPause)
        default: break
        }
    }

    /// Ask the menu for the current screen, or repeat the last one.
    private func drawCurrent() {
        if let onDisplayReady { onDisplayReady() } else { redraw() }
    }

    /// Draw one screen. Each send replaces the whole display (DAT has no
    /// partial updates), so callers always pass the complete screen.
    func present(_ view: FlexBox) {
        lastView = view
        redraw()
    }

    /// The display dims after 20 s without activity and sleeps at 25 s (DAT
    /// docs), and a drill line can sit there longer than that while you
    /// answer. Re-sending the same view every 15 s keeps it lit.
    private func redraw() {
        guard let display, displayReady, let view = lastView else { return }
        Task { try? await display.send(view) }
        keepAwake?.cancel()
        keepAwake = Task { [weak self] in
            try? await Task.sleep(nanoseconds: 15_000_000_000)
            if !Task.isCancelled { self?.redraw() }
        }
    }
}
