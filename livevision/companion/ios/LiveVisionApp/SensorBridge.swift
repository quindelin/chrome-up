import CoreLocation
import CoreMotion
import Foundation
import Observation

/// Native replacement for the HUD's /phone Safari page: compass heading, GPS
/// and motion go to wss://<host>/ws/phone in the same JSON the page sent, so
/// the server needs no changes. Runs while the app is open (when-in-use).
@MainActor
@Observable
final class SensorBridge: NSObject, CLLocationManagerDelegate {
    // saved: these used to reset (motion and posture to off) on every launch,
    // so a rebuild silently stopped the phone IMU reaching the HUD
    var compassOn = SensorBridge.saved("sensors.compassOn") { didSet { save(); applyToggles() } }
    var gpsOn = SensorBridge.saved("sensors.gpsOn") { didSet { save(); applyToggles() } }
    var motionOn = SensorBridge.saved("sensors.motionOn") { didSet { save(); applyToggles() } }
    /// Posture for the avatar: the phone in a front pocket lies along your
    /// thigh, so its gravity vector says standing or sitting (server/body.py).
    var postureOn = SensorBridge.saved("sensors.postureOn") { didSet { save(); applyToggles() } }

    /// On unless you turned it off.
    private static func saved(_ key: String) -> Bool {
        UserDefaults.standard.object(forKey: key) == nil ? true : UserDefaults.standard.bool(forKey: key)
    }

    private func save() {
        let d = UserDefaults.standard
        d.set(compassOn, forKey: "sensors.compassOn")
        d.set(gpsOn, forKey: "sensors.gpsOn")
        d.set(motionOn, forKey: "sensors.motionOn")
        d.set(postureOn, forKey: "sensors.postureOn")
    }
    @ObservationIgnored private var motionTick = 0
    /// RouteNavigator follows the same fixes and heading (no second CLLocationManager).
    @ObservationIgnored var onFix: (@MainActor (CLLocation) -> Void)?
    @ObservationIgnored var onHeading: (@MainActor (Double) -> Void)?

    private(set) var running = false
    private(set) var connected = false
    private(set) var heading: Double?
    private(set) var headingAccuracy: Double?
    private(set) var location: CLLocationCoordinate2D?
    private(set) var sent = 0
    private(set) var lastError: String?
    private(set) var authorization: CLAuthorizationStatus = .notDetermined

    private let location_ = CLLocationManager()
    private let motion = CMMotionManager()
    private var socket: URLSessionWebSocketTask?
    private var reconnect: Task<Void, Never>?

    override init() {
        super.init()
        location_.delegate = self
        location_.headingFilter = 1                   // degrees
        location_.desiredAccuracy = kCLLocationAccuracyBest
        location_.distanceFilter = 3                  // metres
    }

    func start() {
        guard !running else { return }
        running = true
        if location_.authorizationStatus == .notDetermined { location_.requestWhenInUseAuthorization() }
        connect()
        applyToggles()
    }

    func stop() {
        running = false
        reconnect?.cancel()
        socket?.cancel(with: .goingAway, reason: nil)
        socket = nil
        connected = false
        location_.stopUpdatingHeading()
        location_.stopUpdatingLocation()
        motion.stopDeviceMotionUpdates()
    }

    /// tap / swipe_left / swipe_right / spread, like the /phone gesture pad
    func gesture(_ g: String) { send(["gesture": g]) }

    private func applyToggles() {
        guard running else { return }
        compassOn && CLLocationManager.headingAvailable() ? location_.startUpdatingHeading() : location_.stopUpdatingHeading()
        gpsOn ? location_.startUpdatingLocation() : location_.stopUpdatingLocation()
        if motionOn || postureOn, motion.isDeviceMotionAvailable, !motion.isDeviceMotionActive {
            motion.deviceMotionUpdateInterval = 1.0 / 25          // the page capped at ~25 Hz
            motion.startDeviceMotionUpdates(to: .main) { [weak self] m, _ in
                guard let self, let m else { return }
                self.motionTick += 1
                // ~8 Hz is plenty for sitting down / standing up
                if self.postureOn, self.motionTick % 3 == 0 {
                    self.send(["body": ["gravity": [m.gravity.x, m.gravity.y, m.gravity.z]]])
                }
                guard self.motionOn else { return }
                // the page sent accelerationIncludingGravity (m/s²) and rotationRate (deg/s)
                let g = 9.80665, r = 180.0 / .pi
                let a = (m.userAcceleration.x + m.gravity.x, m.userAcceleration.y + m.gravity.y,
                         m.userAcceleration.z + m.gravity.z)
                self.send(["imu": ["t": Date().timeIntervalSince1970 * 1000,
                                   "ax": a.0 * g, "ay": a.1 * g, "az": a.2 * g,
                                   "gx": m.rotationRate.z * r, "gy": m.rotationRate.x * r,
                                   "gz": m.rotationRate.y * r]])
            }
        } else if !motionOn && !postureOn {
            motion.stopDeviceMotionUpdates()
        }
    }

    // MARK: socket

    private func connect() {
        guard running, let url = try? HUDClient.fromSettings().phoneSocket else {
            lastError = StackError.noHost.localizedDescription
            return
        }
        let task = URLSession.shared.webSocketTask(with: url)
        socket = task
        task.resume()
        receive(task)
        connected = true          // optimistic; a failed send flips it and reconnects
        lastError = nil
    }

    /// The server never talks back on /ws/phone, but reading surfaces a dropped socket.
    private func receive(_ task: URLSessionWebSocketTask) {
        task.receive { [weak self] result in
            Task { @MainActor in
                guard let self, task === self.socket else { return }
                if case .failure(let e) = result { self.dropped(e) } else { self.receive(task) }
            }
        }
    }

    private func dropped(_ error: Error) {
        connected = false
        lastError = error.localizedDescription
        socket = nil
        reconnect?.cancel()
        reconnect = Task { [weak self] in
            try? await Task.sleep(for: .seconds(3))
            self?.connect()
        }
    }

    /// For BodyTracker: head pose, hands, wrists and heart rate share this socket.
    func sendJSON(_ obj: [String: Any]) { send(obj) }

    private func send(_ obj: [String: Any]) {
        guard let socket, let data = try? JSONSerialization.data(withJSONObject: obj),
              let text = String(data: data, encoding: .utf8) else { return }
        socket.send(.string(text)) { [weak self] err in
            Task { @MainActor in
                guard let self else { return }
                if let err { self.dropped(err) } else { self.sent += 1; self.connected = true }
            }
        }
    }

    // MARK: CLLocationManagerDelegate

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateHeading h: CLHeading) {
        let deg = h.trueHeading >= 0 ? h.trueHeading : h.magneticHeading
        let acc = h.headingAccuracy
        Task { @MainActor in
            self.heading = deg
            self.headingAccuracy = acc
            self.send(["heading": deg, "accuracy": max(0, acc), "source": "ios"])
            self.onHeading?(deg)
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locs: [CLLocation]) {
        guard let fix = locs.last else { return }
        let c = fix.coordinate
        Task { @MainActor in
            self.location = c
            self.send(["lat": c.latitude, "lon": c.longitude])
            self.onFix?(fix)
        }
    }

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        Task { @MainActor in
            self.authorization = status
            self.applyToggles()
        }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        Task { @MainActor in self.lastError = error.localizedDescription }
    }
}
