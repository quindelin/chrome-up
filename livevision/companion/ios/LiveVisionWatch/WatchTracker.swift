import CoreMotion
import Foundation
import HealthKit
import Observation
import WatchConnectivity

// file-level: read from HealthKit's delegate callbacks, off the main actor
private let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
private let beatsPerMinute = HKUnit.count().unitDivided(by: .minute())

/// The Watch half of LiveVision's body tracking: your wrist's orientation, your
/// heart rate and your punches, relayed to the iPhone app, which sends them to
/// the HUD (docs/BODY_TRACKING.md). Punches go the moment they land
/// (PunchDetector on 100 Hz device motion), not on the ~10 Hz tick.
///
/// A workout session is what keeps a watchOS app running, and its motion
/// sensors live, with your wrist down; it also gives live heart rate. The
/// workout is discarded when you stop, so nothing lands in the Health app.
@MainActor
@Observable
final class WatchTracker: NSObject {
    private(set) var running = false
    private(set) var heartRate: Double?
    private(set) var phoneReachable = false
    private(set) var sent = 0
    private(set) var punches = 0
    private(set) var error: String?
    var side: String = UserDefaults.standard.string(forKey: "wrist") ?? "left" {
        didSet { UserDefaults.standard.set(side, forKey: "wrist") }
    }

    @ObservationIgnored private let health = HKHealthStore()
    @ObservationIgnored private var workout: HKWorkoutSession?
    @ObservationIgnored private var builder: HKLiveWorkoutBuilder?
    @ObservationIgnored private let motion = CMMotionManager()
    @ObservationIgnored private var attitude: [Double]?        // [w, x, y, z]
    // Watch x runs along the forearm (crown toward the hand) on either wrist
    @ObservationIgnored private var detector = PunchDetector(forearm: SIMD3(1, 0, 0))
    @ObservationIgnored private var loop: Task<Void, Never>?

    func activate() {
        guard WCSession.isSupported() else { return }
        WCSession.default.delegate = self
        WCSession.default.activate()
    }

    func start() async {
        guard !running else { return }
        error = nil
        guard HKHealthStore.isHealthDataAvailable() else { error = "Health data isn't available"; return }
        do {
            try await health.requestAuthorization(toShare: [HKObjectType.workoutType()],
                                                  read: [heartRateType])
            let config = HKWorkoutConfiguration()
            config.activityType = .other
            config.locationType = .unknown
            let session = try HKWorkoutSession(healthStore: health, configuration: config)
            let b = session.associatedWorkoutBuilder()
            b.dataSource = HKLiveWorkoutDataSource(healthStore: health, workoutConfiguration: config)
            session.delegate = self
            b.delegate = self
            workout = session
            builder = b
            let now = Date()
            session.startActivity(with: now)
            try await b.beginCollection(at: now)
        } catch {
            self.error = "Workout: \(error.localizedDescription)"
            return
        }
        running = true
        startMotion()
        loop = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .milliseconds(100))   // ~10 Hz to the phone
                self?.sendToPhone()
            }
        }
    }

    func stop() {
        guard running else { return }
        running = false
        loop?.cancel(); loop = nil
        motion.stopDeviceMotionUpdates()
        attitude = nil
        workout?.end()
        let b = builder
        Task {
            // keep Health clean: this was only a way to stay awake
            try? await b?.endCollection(at: Date())
            b?.discardWorkout()
        }
        workout = nil
        builder = nil
    }

    private func startMotion() {
        guard motion.isDeviceMotionAvailable else { error = "No motion sensors"; return }
        // 100 Hz: a jab's spike lasts ~30-50 ms; attitude still goes out at ~10 Hz
        motion.deviceMotionUpdateInterval = 1.0 / 100
        detector = PunchDetector(forearm: SIMD3(1, 0, 0))
        motion.startDeviceMotionUpdates(to: .main) { [weak self] m, _ in
            guard let m else { return }
            MainActor.assumeIsolated { self?.motionSample(m) }
        }
    }

    private func motionSample(_ m: CMDeviceMotion) {
        let q = m.attitude.quaternion
        attitude = [q.w, q.x, q.y, q.z]
        let a = m.userAcceleration, g = m.gravity, r = m.rotationRate
        guard let p = detector.push(linear: SIMD3(a.x, a.y, a.z), gravity: SIMD3(g.x, g.y, g.z),
                                    rotation: SIMD3(r.x, r.y, r.z), at: m.timestamp) else { return }
        punches += 1
        let s = WCSession.default
        guard s.activationState == .activated, s.isReachable else { return }
        let punch: [String: Any] = ["side": side, "kind": p.kind, "strength": p.strength, "source": "watch"]
        s.sendMessage(["side": side, "punch": punch], replyHandler: nil) { err in
            Task { @MainActor in self.error = err.localizedDescription }
        }
    }

    private func sendToPhone() {
        let s = WCSession.default
        guard s.activationState == .activated, s.isReachable else { phoneReachable = false; return }
        phoneReachable = true
        var msg: [String: Any] = ["side": side]
        if let attitude { msg["wrist"] = attitude }
        if let heartRate { msg["hr"] = heartRate }
        s.sendMessage(msg, replyHandler: nil) { err in
            Task { @MainActor in self.error = err.localizedDescription }
        }
        sent += 1
    }

    fileprivate func gotHeartRate(_ value: Double) { heartRate = value }
    fileprivate func workoutEnded() { if running { stop() } }
}

extension WatchTracker: HKWorkoutSessionDelegate, HKLiveWorkoutBuilderDelegate {
    nonisolated func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState,
                                    from fromState: HKWorkoutSessionState, date: Date) {
        if toState == .ended || toState == .stopped {
            Task { @MainActor in self.workoutEnded() }
        }
    }

    nonisolated func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {
        let text = error.localizedDescription
        Task { @MainActor in self.error = "Workout: \(text)"; self.workoutEnded() }
    }

    nonisolated func workoutBuilder(_ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>) {
        guard collectedTypes.contains(heartRateType),
              let v = workoutBuilder.statistics(for: heartRateType)?.mostRecentQuantity()?.doubleValue(for: beatsPerMinute)
        else { return }
        Task { @MainActor in self.gotHeartRate(v) }
    }

    nonisolated func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {}
}

extension WatchTracker: WCSessionDelegate {
    nonisolated func session(_ session: WCSession, activationDidCompleteWith state: WCSessionActivationState,
                             error: Error?) {
        let reach = session.isReachable
        Task { @MainActor in self.phoneReachable = reach }
    }

    nonisolated func sessionReachabilityDidChange(_ session: WCSession) {
        let reach = session.isReachable
        Task { @MainActor in self.phoneReachable = reach }
    }
}
