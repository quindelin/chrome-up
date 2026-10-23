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
    /// Hand positions from the glasses camera: off and no longer offered. It
    /// saw the hands now and then, at low confidence, and the avatar's arm
    /// jumped; the wrist sensors drive the arms now (server/arms.py)
    var handsOn = false { didSet { save(); refresh() } }
    var watchOn = true { didSet { save(); refresh() } }

    private(set) var motion: MotionLink = .off
    private(set) var headSamples = 0
    private(set) var bandSamples = 0
    private(set) var punches = 0
    private(set) var hands: [String: HandTracker.Hand] = [:]
    private(set) var handsSeenAt: Date?
    private(set) var sent = 0

    @ObservationIgnored private weak var glasses: GlassesStreamer?
    @ObservationIgnored private var calibrationLoop: Task<Void, Never>?
    /// What the lens should ask for: nil when the arms are fine
    private(set) var armPrompt: String?
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
    @ObservationIgnored private var bandAttitude = GyroAttitude()  // when the band sends no fused orientation
    /// The glasses' orientation [w, x, y, z], ~10 Hz: the lens compass turns
    /// with your head (RouteNavigator.headTurned)
    @ObservationIgnored var onHead: (@MainActor ([Double]) -> Void)?
    @ObservationIgnored private static let defaults = UserDefaults.standard

    init() {
        let d = Self.defaults
        if d.object(forKey: "body.headOn") != nil { headOn = d.bool(forKey: "body.headOn") }
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
        calibrationLoop?.cancel()
        calibrationLoop = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(5))
                await self?.checkCalibration()
            }
        }
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

    /// Every 5 s: does the HUD have a wrist sending without a calibration?
    /// Then the lens asks for one (or for a Watch app update, when the Watch
    /// sends no gravity), until it's done.
    private func checkCalibration() async {
        guard let glasses else { return }
        var prompt: String?
        if let arms = (try? await HUDClient.fromSettings().status())?.arms {
            if arms.values.contains(where: { $0.needs == "gravity" }) {
                prompt = "Update the LiveVision Watch app to track your arm"
            } else if arms.values.contains(where: { $0.needs == "calibration" || ($0.fresh == true && $0.calibrated == false) }) {
                prompt = "Calibrate arms in the LiveVision app"
            }
        }
        guard prompt != armPrompt else { return }
        armPrompt = prompt
        let lens = LensRouter.shared
        lens.notice = prompt
        if prompt != nil, glasses.link == .connected {
            lens.want(.notice, on: glasses)
        } else if prompt == nil {
            lens.release(.notice)
        }
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
        let fused = sample.orientation.map { [Double($0.w), Double($0.x), Double($0.y), Double($0.z)] }
        switch sample.source {
        case .glasses:
            guard let q = fused else { return }
            head = (q, Date()); headSamples += 1
        case .neuralBand:
            // DAT: "not every device produces" a fused orientation. Dropping
            // samples without one dropped the whole band, punches included;
            // without it, estimate one from the gyro and gravity
            bandSamples += 1
            bandPunches(sample)
            // our own estimate first: its frame is known (z up, device ->
            // world), which the arm direction needs; DAT's frame isn't documented
            if let q = bandAttitude.update(sample) ?? fused { band = (q, Date()) }
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
        if let h = head, now.timeIntervalSince(h.at) < 0.3 { onHead?(h.q) }
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
            var w: [String: Any] = ["q": q, "source": "watch"]
            if let g = watch.gravity { w["g"] = g }
            wrists[watch.side] = w
        }
        if !wrists.isEmpty { body["wrists"] = wrists }
        if watchOn, let watch, watch.fresh(within: 10), let hr = watch.heartRate { body["heart_rate"] = hr }
        guard !body.isEmpty else { return }
        sensors.sendJSON(["body": body])
        sent += 1
    }
}

/// Orientation from a gyro and an accelerometer (a complementary filter):
/// integrate the rotation rate, and pull the tilt slowly toward gravity so it
/// doesn't drift. Yaw drifts freely, which the server's wrist levelling
/// (body.wrist_level_s) absorbs. Returns [w, x, y, z] like DAT's orientation.
struct GyroAttitude {
    private var q = simd_quatd(ix: 0, iy: 0, iz: 0, r: 1)
    private var lastNs: Int64?
    var gain = 0.02            // per sample, toward gravity

    mutating func update(_ s: MotionSample) -> [Double]? {
        guard let g = s.gyroscope else { return nil }
        let t = s.timestampNs
        defer { lastNs = t }
        guard let last = lastNs, t > last else { return nil }
        let dt = min(0.1, Double(t - last) / 1e9)
        let w = SIMD3<Double>(Double(g.x), Double(g.y), Double(g.z))
        let angle = simd_length(w) * dt
        if angle > 1e-9 { q = simd_normalize(q * simd_quatd(angle: angle, axis: w / simd_length(w))) }
        if let a = s.accelerometer {
            // at rest the accelerometer reads +1 g up; rotate that into the
            // world frame and nudge it onto world up (+z)
            let up = SIMD3<Double>(Double(a.x), Double(a.y), Double(a.z))
            let n = simd_length(up)
            if abs(n - 9.81) < 3 {                    // only while not swinging
                let world = q.act(up / n)
                let target = SIMD3<Double>(0, 0, 1)
                let axis = simd_cross(world, target)
                let sinErr = simd_length(axis)
                if sinErr > 1e-6 {
                    let err = asin(min(1, sinErr))
                    q = simd_normalize(simd_quatd(angle: err * gain, axis: axis / sinErr) * q)
                }
            }
        }
        return [q.real, q.imag.x, q.imag.y, q.imag.z]
    }
}
