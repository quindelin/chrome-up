import CoreVideo
import Foundation
import MWDATCore
import MWDATMotion
import Observation
import simd

/// Your body, for the HUD's avatar (server/body.py, docs/BODY_TRACKING.md):
///
///   head      glasses DAT Motion, source .glasses       -> {"head": {"q": [w,x,y,z]}}
///   one wrist Neural Band, same Motion stream, .neuralBand -> body.wrists.<band side>
///   punches   Neural Band accelerometer here, the Watch's own detector -> body.punch, sent at once
///   hands     Vision on the glasses' POV frames (HandTracker) -> body.hands
///   other wrist + heart rate  the LiveVision Watch app (WatchLink)
///   posture   phone gravity in your pocket (SensorBridge.postureOn)
///
/// Everything rides SensorBridge's socket to /ws/phone at ~10 Hz. Motion
/// attaches to the glasses session the camera already holds (the glasses
/// allow one session), and re-attaches after reconnects like the
/// teleprompter's Display. DAT Motion is a beta capability: it needs the
/// development / beta channel (Developer Mode), as the glasses mic does.
@MainActor
@Observable
final class BodyTracker {
    enum MotionLink: Equatable { case off, waiting, starting, streaming, failed(String) }

    // what the user turned on (Control tab)
    var headOn = true { didSet { save(); refresh() } }
    var handsOn = true { didSet { save(); refresh() } }
    var watchOn = true { didSet { save(); refresh() } }

    private(set) var motion: MotionLink = .off
    private(set) var headSamples = 0
    private(set) var bandSamples = 0
    private(set) var punches = 0
    private(set) var hands: [String: HandTracker.Hand] = [:]
    private(set) var handsSeenAt: Date?
    private(set) var sent = 0

    @ObservationIgnored private weak var glasses: GlassesStreamer?
    @ObservationIgnored private weak var sensors: SensorBridge?
    @ObservationIgnored private var watch: WatchLink?
    @ObservationIgnored private var cap: Motion?
    @ObservationIgnored private weak var attachedTo: DeviceSession?
    @ObservationIgnored private var sampleTask: Task<Void, Never>?
    @ObservationIgnored private var tokens = ListenerTokenBag()
    @ObservationIgnored private var sendLoop: Task<Void, Never>?
    @ObservationIgnored private let handTracker = HandTracker()
    @ObservationIgnored private var head: (q: [Double], at: Date)?
    @ObservationIgnored private var band: (q: [Double], at: Date)?
    @ObservationIgnored private var bandPunch = PunchDetector()   // band axes unknown: no forearm
    @ObservationIgnored private var bandGravity: SIMD3<Double>?    // slow average of the raw accelerometer, m/s^2
    @ObservationIgnored private static let defaults = UserDefaults.standard

    init() {
        let d = Self.defaults
        if d.object(forKey: "body.headOn") != nil { headOn = d.bool(forKey: "body.headOn") }
        if d.object(forKey: "body.handsOn") != nil { handsOn = d.bool(forKey: "body.handsOn") }
        if d.object(forKey: "body.watchOn") != nil { watchOn = d.bool(forKey: "body.watchOn") }
        handTracker.onHands = { [weak self] found in self?.handsFound(found) }
    }

    private func save() {
        Self.defaults.set(headOn, forKey: "body.headOn")
        Self.defaults.set(handsOn, forKey: "body.handsOn")
        Self.defaults.set(watchOn, forKey: "body.watchOn")
    }

    /// Once at launch.
    func start(glasses: GlassesStreamer, sensors: SensorBridge, watch: WatchLink) {
        self.glasses = glasses
        self.sensors = sensors
        self.watch = watch
        watch.activate()
        watch.onPunch = { [weak self] p in self?.sendPunch(p) }
        refresh()
        sendLoop?.cancel()
        sendLoop = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(100))
                self?.tick()
            }
        }
    }

    /// Call when the glasses link changes (connect, pause, reconnect).
    func sessionChanged(_ glasses: GlassesStreamer) {
        self.glasses = glasses
        refresh()
    }

    private func refresh() {
        guard let glasses else { return }
        // hand tracking: frames only flow while the camera streams
        if handsOn {
            let t = handTracker
            glasses.setFrameTap { pixels in t.push(pixels) }
        } else {
            glasses.setFrameTap(nil)
            hands = [:]
        }
        // DAT Motion on the open session
        guard headOn else { detach(); motion = .off; return }
        guard glasses.link == .connected, let session = glasses.deviceSession else {
            if attachedTo != nil, glasses.deviceSession == nil { detach() }
            motion = .waiting
            return
        }
        if session === attachedTo, cap != nil { return }
        attach(to: session)
    }

    private func attach(to session: DeviceSession) {
        detach()
        motion = .starting
        attachedTo = session
        let m: Motion
        do {
            // 60 Hz: a jab's acceleration spike lasts ~30-50 ms, which 30 Hz
            // samples once at best and often misses; head turns get smoother too
            guard let added = try session.addMotion(configuration: MotionConfiguration(samplingRate: .hz60)) else {
                motion = .waiting          // session not started yet; the next link change retries
                attachedTo = nil
                return
            }
            m = added
        } catch {
            motion = .failed("Motion: \(error.localizedDescription). It needs Developer Mode (DAT beta).")
            log.error("addMotion: \(String(describing: error))")
            attachedTo = nil
            return
        }
        cap = m
        // samples don't replay: listen before start()
        let stream = m.samples
        sampleTask = Task { [weak self] in
            for await sample in stream { self?.handle(sample) }
        }
        m.statePublisher.listen { [weak self] state in
            Task { @MainActor in self?.motionStateChanged(state) }
        }.store(in: tokens)
        m.errorPublisher.listen { [weak self] error in
            log.error("motion: \(String(describing: error))")
            Task { @MainActor in self?.motion = .failed("Motion: \(error.localizedDescription)") }
        }.store(in: tokens)
        m.start()
    }

    private func detach() {
        sampleTask?.cancel(); sampleTask = nil
        cap?.stop()
        if cap != nil { try? attachedTo?.removeMotion() }
        cap = nil
        attachedTo = nil
        let old = tokens
        tokens = ListenerTokenBag()
        Task { await old.cancelAll() }
    }

    private func motionStateChanged(_ state: MotionState) {
        switch state {
        case .started: motion = .streaming
        case .starting: motion = .starting
        case .stopped:
            // no sample within 10 s (iOS), or the session went away: let the
            // next link change / toggle re-attach
            if cap != nil, motion != .off { motion = .waiting; cap = nil; attachedTo = nil }
        case .stopping: break
        }
    }

    private func handle(_ sample: MotionSample) {
        guard let o = sample.orientation else { return }
        let q = [Double(o.w), Double(o.x), Double(o.y), Double(o.z)]
        switch sample.source {
        case .glasses: head = (q, Date()); headSamples += 1
        case .neuralBand: band = (q, Date()); bandSamples += 1; bandPunches(sample)
        case .unknown: break
        }
    }

    /// The band's accelerometer includes gravity (m/s^2): a slow average of it
    /// is gravity, the rest is the wrist's own acceleration. The average only
    /// follows while the wrist is calm, so a punch doesn't bend it.
    private func bandPunches(_ sample: MotionSample) {
        guard let acc = sample.accelerometer else { return }
        let raw = SIMD3<Double>(Double(acc.x), Double(acc.y), Double(acc.z))
        let g0 = 9.81
        guard var grav = bandGravity else { bandGravity = raw; return }
        let linear = (raw - grav) / g0
        if simd_length(linear) < 0.8 { grav += (raw - grav) * 0.04; bandGravity = grav }   // ~0.4 s at 60 Hz
        let rot = sample.gyroscope.map { SIMD3<Double>(Double($0.x), Double($0.y), Double($0.z)) }
        // an accelerometer at rest reads +1 g UP; the detector wants gravity pointing down
        guard let p = bandPunch.push(linear: linear, gravity: -grav, rotation: rot,
                                     at: Double(sample.timestampNs) / 1e9) else { return }
        sendPunch(["side": Settings.bandWrist, "kind": p.kind, "strength": p.strength, "source": "neural_band"])
    }

    /// Punches skip the ~10 Hz tick: the avatar throws as you do.
    private func sendPunch(_ punch: [String: Any]) {
        guard let sensors else { return }
        if !(punch["source"] as? String == "watch" ? watchOn : headOn) { return }
        sensors.sendJSON(["body": ["punch": punch]])
        punches += 1
    }

    private func handsFound(_ found: [String: HandTracker.Hand]) {
        hands = found
        if !found.isEmpty { handsSeenAt = Date() }
    }

    /// ~10 Hz: one head message and one body message, only with fresh parts.
    private func tick() {
        guard let sensors else { return }
        let now = Date()
        if headOn, let h = head, now.timeIntervalSince(h.at) < 0.3 {
            sensors.sendJSON(["head": ["q": h.q, "source": "glasses"]])
        }
        var body: [String: Any] = [:]
        if handsOn, let seen = handsSeenAt, now.timeIntervalSince(seen) < 0.3, !hands.isEmpty {
            body["hands"] = hands.mapValues { ["x": $0.x, "y": $0.y, "z": $0.z, "conf": $0.conf] }
        }
        var wrists: [String: Any] = [:]
        if headOn, let b = band, now.timeIntervalSince(b.at) < 0.5 {
            wrists[Settings.bandWrist] = ["q": b.q, "source": "neural_band"]
        }
        if watchOn, let watch, watch.fresh(), let q = watch.wrist {
            wrists[watch.side] = ["q": q, "source": "watch"]
        }
        if !wrists.isEmpty { body["wrists"] = wrists }
        if watchOn, let watch, watch.fresh(within: 10), let hr = watch.heartRate { body["heart_rate"] = hr }
        guard !body.isEmpty else { return }
        sensors.sendJSON(["body": body])
        sent += 1
    }
}
