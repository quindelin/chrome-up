import Foundation
import Observation
import WatchConnectivity

/// The iPhone end of the LiveVision Watch app (LiveVisionWatch target).
///
/// The Watch runs a workout session (so its sensors keep going wrist-down)
/// and sends ~10 messages a second over WatchConnectivity:
///     {"wrist": [w, x, y, z], "side": "left", "hr": 96}
/// watchOS keeps most apps off their own network sockets, so the phone relays
/// it to the HUD with the rest of the body data (BodyTracker).
@MainActor
@Observable
final class WatchLink: NSObject, WCSessionDelegate {
    private(set) var supported = WCSession.isSupported()
    private(set) var paired = false
    private(set) var installed = false
    private(set) var reachable = false
    private(set) var heartRate: Double?
    private(set) var wrist: [Double]?            // [w, x, y, z]
    private(set) var side: String = Settings.watchWrist
    private(set) var lastMessage: Date?
    private(set) var received = 0

    func activate() {
        guard supported else { return }
        let s = WCSession.default
        s.delegate = self
        s.activate()
    }

    /// Wrist / heart rate this recent count as live.
    func fresh(within seconds: Double = 2) -> Bool {
        guard let t = lastMessage else { return false }
        return Date().timeIntervalSince(t) < seconds
    }

    // MARK: WCSessionDelegate (called off the main thread)

    nonisolated func session(_ session: WCSession, activationDidCompleteWith state: WCSessionActivationState,
                             error: Error?) {
        let paired = session.isPaired, installed = session.isWatchAppInstalled, reach = session.isReachable
        Task { @MainActor in
            self.paired = paired; self.installed = installed; self.reachable = reach
            if let error { log.error("watch: activation \(error.localizedDescription)") }
        }
    }

    nonisolated func sessionReachabilityDidChange(_ session: WCSession) {
        let reach = session.isReachable
        Task { @MainActor in self.reachable = reach }
    }

    nonisolated func sessionWatchStateDidChange(_ session: WCSession) {
        let paired = session.isPaired, installed = session.isWatchAppInstalled
        Task { @MainActor in self.paired = paired; self.installed = installed }
    }

    nonisolated func session(_ session: WCSession, didReceiveMessage message: [String: Any]) {
        let q = (message["wrist"] as? [Double]).flatMap { $0.count == 4 ? $0 : nil }
        let hr = message["hr"] as? Double
        let side = message["side"] as? String
        Task { @MainActor in
            if let q { self.wrist = q }
            if let hr, hr > 0 { self.heartRate = hr }
            if let side, side == "left" || side == "right" { self.side = side; Settings.watchWrist = side }
            self.lastMessage = Date()
            self.received += 1
        }
    }

    // iOS only: a Watch switch re-activates the session
    nonisolated func sessionDidBecomeInactive(_ session: WCSession) {}
    nonisolated func sessionDidDeactivate(_ session: WCSession) { WCSession.default.activate() }
}
