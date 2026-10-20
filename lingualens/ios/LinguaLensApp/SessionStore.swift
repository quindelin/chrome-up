import Foundation
import LinguaLensCore
import MediaPlayer
import Observation
import UIKit

/// The headless lesson player.
///
/// State snapshots come in over the websocket; intents (attempt, next, start
/// a lesson) go out over HTTP and the answer comes back as the next snapshot.
/// For each snapshot StepPlanner says what to do - speak, wait, record,
/// advance - and this runs it. A new step (or a new attempt count) cancels
/// whatever was running for the old one, so the phone, the glasses and the
/// web page can all drive the same session without stepping on each other.
@MainActor
@Observable
final class SessionStore {
    enum Phase: String { case idle, speaking, listening, grading, waiting, paused }

    private(set) var state: LessonState?
    private(set) var connection = "not connected"
    private(set) var phase: Phase = .paused
    private(set) var lastMessage = ""
    private(set) var level: Float = -120
    private(set) var isPlaying = false {
        didSet { if isPlaying != oldValue { menu?.update() } }
    }
    var handsFree = Settings.handsFree {
        didSet { Settings.handsFree = handsFree; planner.handsFree = handsFree; replan(force: true) }
    }

    let audio = AudioEngine()
    let glasses = GlassesLink()
    /// The screens on the glasses (home, lessons, course, the lesson itself).
    @ObservationIgnored private(set) var menu: GlassesMenu!

    @ObservationIgnored private(set) var client: LessonClient?
    @ObservationIgnored private var socket: StateSocket?
    @ObservationIgnored private var socketTask: Task<Void, Never>?
    @ObservationIgnored private var planTask: Task<Void, Never>?
    @ObservationIgnored private var planKey = ""
    @ObservationIgnored private var planner = StepPlanner(handsFree: Settings.handsFree)
    @ObservationIgnored private var lastScoreSeen: Score?
    @ObservationIgnored private var askedForMic = false

    init() {
        menu = GlassesMenu(store: self)
        glasses.onCommand = { [weak self] in self?.handle($0) }
        // the display (re)started - after Connect, Back, or an interruption
        glasses.onDisplayReady = { [weak self] in self?.menu.render() }
        // "Hey Meta, start LinguaLens": back on the glasses, and carry on
        glasses.onVoiceLaunch = { [weak self] in self?.play() }
        RemoteControls.install(self)
    }

    // MARK: connection

    func connect() {
        socketTask?.cancel()
        socket?.stop()
        guard let config = Settings.config else {
            connection = "set the server in Settings"
            return
        }
        let client = LessonClient(config: config)
        let socket = StateSocket(config: config)
        self.client = client
        self.socket = socket
        connection = "connecting to \(config.baseURL.host ?? "")…"
        socketTask = Task { [weak self] in
            for await event in socket.events() {
                guard let self else { return }
                switch event {
                case .connected:
                    self.connection = "connected · \(config.clientId)"
                    log.notice("ws connected \(config.baseURL.absoluteString, privacy: .public)")
                case .state(let s):
                    self.apply(s)
                case .disconnected(let why):
                    self.connection = "reconnecting… (\(why))"
                    log.notice("ws closed: \(why, privacy: .public)")
                }
            }
        }
    }

    private func apply(_ s: LessonState) {
        let previous = state
        state = s
        log.notice("state \(StepPlanner.key(for: s), privacy: .public)")
        if let score = s.lastScore, score != lastScoreSeen, previous != nil {
            Task { await audio.play(score.passed ? .pass : .fail) }
            UINotificationFeedbackGenerator().notificationOccurred(score.passed ? .success : .error)
        }
        lastScoreSeen = s.lastScore
        if let m = s.message, !m.isEmpty { lastMessage = m }
        menu.update()
        RemoteControls.update(s, playing: isPlaying)
        replan()
    }

    // MARK: transport

    func play() {
        // Pressing play is the explicit "I'm back" that DAT asks for before
        // the display is taken: put the lesson on the glasses if it was closed.
        if Settings.glassesDisplay && glasses.registered && !glasses.displayActive {
            glasses.showOnGlasses()
        }
        menu.showLesson()
        guard !isPlaying else { return }
        isPlaying = true
        if !askedForMic {
            askedForMic = true
            Task { _ = await AudioEngine.requestMicrophone() }
        }
        audio.startKeepAlive()
        RemoteControls.update(state, playing: true)
        replan(force: true)
    }

    func pause() {
        isPlaying = false
        planTask?.cancel()
        planTask = nil
        planKey = ""
        audio.stopSpeaking()
        audio.stopRecording()
        audio.stopKeepAlive()
        phase = .paused
        RemoteControls.update(state, playing: false)
    }

    /// "Next": end a take that is running, move past a step you do not speak,
    /// or (on a graded step, which the server will not skip) hear it again.
    func next() {
        if phase == .listening { audio.stopRecording(); return }
        guard let s = state, let step = s.step else { return }
        if step.isSpoken { replan(force: true); return }
        planTask?.cancel()
        audio.stopSpeaking()
        Task { try? await client?.next(at: s.position.index) }
    }

    func repeatLine() { replan(force: true) }

    /// Push to talk, or stop the take that is running.
    func talk() {
        if phase == .listening { audio.stopRecording(); return }
        guard state?.step?.isSpoken == true else { next(); return }
        planTask?.cancel()
        audio.stopSpeaking()
        planKey = state.map(StepPlanner.key(for:)) ?? ""
        planTask = Task { await self.takeAndGrade() }
    }

    private func handle(_ c: GlassesLink.Command) {
        switch c {
        case .talk: isPlaying ? talk() : play()
        case .next: next()
        case .repeatLine: repeatLine()
        case .pause: pause()
        case .playPause: isPlaying ? pause() : play()
        }
    }

    // MARK: intents

    func startLesson(_ id: Int) { send { try await $0.startLesson(id) } }
    func startReview() { send { try await $0.startReview() } }
    func startVocab(_ topic: String) { send { try await $0.startVocab(topic: topic) } }
    func selectCourse(_ id: String) { send { try await $0.selectCourse(id) } }

    private func send(_ op: @escaping (LessonClient) async throws -> Void) {
        guard let client else { return }
        Task {
            do { try await op(client) } catch { lastMessage = error.localizedDescription }
        }
    }

    // MARK: running a plan

    private func replan(force: Bool = false) {
        guard isPlaying, let s = state else { return }
        let plan = planner.plan(for: s)
        guard force || plan.key != planKey else { return }
        planTask?.cancel()
        audio.stopSpeaking()
        planKey = plan.key
        let index = s.position.index
        let vary = s.config.listeningVaryPitch
        planTask = Task { await self.run(plan, at: index, varyPitch: vary) }
    }

    private func run(_ plan: StepPlan, at index: Int, varyPitch: Bool) async {
        if plan.cues.isEmpty { phase = state?.step == nil ? .idle : .waiting; return }
        for cue in plan.cues {
            if Task.isCancelled { return }
            switch cue {
            case let .say(text, language, rate):
                phase = .speaking
                await audio.say(text, language: language, webRate: rate, varyPitch: varyPitch)
            case let .wait(seconds):
                phase = .waiting
                try? await Task.sleep(nanoseconds: UInt64(seconds * 1e9))
            case .record:
                await takeAndGrade()
            case .advance:
                phase = .waiting
                log.notice("advance at \(index)")
                do { try await client?.next(at: index) }
                catch { lastMessage = error.localizedDescription }
            }
        }
        if !Task.isCancelled && phase != .paused { phase = .waiting }
    }

    private func takeAndGrade() async {
        guard let client else { return }
        phase = .listening
        do {
            let take = try await audio.record { [weak self] db in
                Task { @MainActor in self?.level = db }
            }
            level = -120
            if Task.isCancelled { return }
            guard take.decision == .finished, let wav = take.wav else {
                // nothing said: stop rather than loop the same prompt forever
                lastMessage = "Didn't hear anything - press play (or tap the glasses) to try again."
                log.notice("take: no speech after \(take.seconds)s")
                isPlaying = false
                audio.stopKeepAlive()
                phase = .paused
                RemoteControls.update(state, playing: false)
                return
            }
            phase = .grading
            log.notice("take: \(take.seconds)s, uploading \(wav.count) bytes")
            let result = try await client.attempt(wav: wav)
            if let r = result.reasons.first { lastMessage = r }
        } catch {
            lastMessage = error.localizedDescription
            phase = .waiting
        }
    }
}

/// Lock screen / AirPods / car controls: play-pause, next, previous (= repeat).
@MainActor
enum RemoteControls {
    static func install(_ store: SessionStore) {
        let c = MPRemoteCommandCenter.shared()
        c.playCommand.addTarget { _ in store.play(); return .success }
        c.pauseCommand.addTarget { _ in store.pause(); return .success }
        c.togglePlayPauseCommand.addTarget { _ in
            store.isPlaying ? store.pause() : store.play(); return .success
        }
        c.nextTrackCommand.addTarget { _ in store.next(); return .success }
        c.previousTrackCommand.addTarget { _ in store.repeatLine(); return .success }
    }

    static func update(_ s: LessonState?, playing: Bool) {
        var info: [String: Any] = [:]
        let step = s?.step
        let line = step?.kind == "hear" ? "Listen…" : (step?.text.isEmpty == false ? step!.text : (step?.en ?? "LinguaLens"))
        info[MPMediaItemPropertyTitle] = line
        info[MPMediaItemPropertyArtist] = s?.title ?? "LinguaLens"
        info[MPMediaItemPropertyAlbumTitle] = s.map { "\($0.position.index + 1)/\($0.position.total)" } ?? ""
        info[MPNowPlayingInfoPropertyPlaybackRate] = playing ? 1.0 : 0.0
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
        MPNowPlayingInfoCenter.default().playbackState = playing ? .playing : .paused
    }
}
