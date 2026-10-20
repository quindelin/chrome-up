import CoreLocation
import Foundation
import MapKit
import Observation

/// Apple Maps turn-by-turn for the HUD compass (and, optionally, the lens).
///
/// The Control tab's "Maps link or place name" is resolved here with MapKit
/// (an Apple Maps share link's coordinates, else MKLocalSearch near you), then
/// MKDirections gives the route. SensorBridge's GPS fixes are projected onto
/// the route to find the next maneuver, the distance to it along the route,
/// and what is left of the trip; more than `offRouteMeters` off the line for
/// two good fixes in a row asks MapKit for a new route from here.
///
/// The HUD server gets {"route": {...}} on the same /ws/phone socket (about
/// once a second while moving, every 4 s standing still); while that is fresh
/// the server's own OSRM route steps aside (server/navigation.py).
@MainActor
@Observable
final class RouteNavigator {
    enum Transport: String, CaseIterable, Identifiable {
        case walking, driving
        var id: String { rawValue }
        var label: String { self == .walking ? "Walking" : "Driving" }
        fileprivate var mapKit: MKDirectionsTransportType { self == .walking ? .walking : .automobile }
    }

    /// From the route's geometry, not the instruction text (MapKit localizes it).
    enum Maneuver: String {
        case straight, slightLeft = "slight_left", slightRight = "slight_right"
        case left, right, uturn, arrive
    }

    struct Progress: Equatable {
        var instruction: String       // what to do at the next maneuver
        var maneuver: Maneuver
        var lat: Double               // where it is
        var lon: Double
        var stepDistance: Double      // metres along the route to it
        var bearing: Double           // from here to it, degrees true
        var nextInstruction: String?  // the one after
        var remaining: Double         // metres left of the trip
        var eta: TimeInterval
        var offRoute: Double          // metres from the route line
    }

    private(set) var destinationName: String?
    private(set) var destination: CLLocationCoordinate2D?
    private(set) var progress: Progress?
    private(set) var status: String?
    private(set) var arrived = false
    private(set) var hasRoute = false
    /// Phone compass, degrees true: the lens compass turns with it.
    private(set) var heading: Double?

    var transport: Transport {
        didSet {
            guard transport != oldValue else { return }
            Self.defaults.set(transport.rawValue, forKey: "nav.transport")
            if destination != nil, !arrived { routing = false; calculate() }
        }
    }
    /// Directions on the Ray-Ban Display lens (shared with the teleprompter).
    var lensOn: Bool {
        didSet { Self.defaults.set(lensOn, forKey: "nav.lens"); syncLens() }
    }
    /// A small compass strip image on the lens; off = an arrow icon and text
    /// only (lighter on Bluetooth while the camera streams).
    var lensCompass: Bool {
        didSet { Self.defaults.set(lensCompass, forKey: "nav.lensCompass"); LensRouter.shared.refresh() }
    }

    var active: Bool { destination != nil }

    static let offRouteMeters = 40.0
    static let arriveMeters = 15.0

    @ObservationIgnored private static let defaults = UserDefaults.standard
    @ObservationIgnored private weak var sensors: SensorBridge?
    @ObservationIgnored private weak var glasses: GlassesStreamer?
    @ObservationIgnored private var route: MKRoute?
    @ObservationIgnored private var points: [CLLocationCoordinate2D] = []
    @ObservationIgnored private var cumulative: [Double] = []     // metres along, per point
    @ObservationIgnored private var turns: [Turn] = []
    @ObservationIgnored private var lastSegment = 0
    @ObservationIgnored private var offCount = 0
    @ObservationIgnored private var routing = false
    @ObservationIgnored private var lastRouted = Date.distantPast
    @ObservationIgnored private var lastPublish = Date.distantPast
    @ObservationIgnored private var lensHeading: Double?
    @ObservationIgnored private var fix: CLLocation?
    @ObservationIgnored private var generation = 0
    @ObservationIgnored private var heartbeat: Task<Void, Never>?

    private struct Turn {
        var index: Int                // into points
        var along: Double             // metres from the start
        var text: String
        var maneuver: Maneuver
    }

    init() {
        transport = Transport(rawValue: Self.defaults.string(forKey: "nav.transport") ?? "") ?? .walking
        lensOn = Self.defaults.bool(forKey: "nav.lens")
        lensCompass = Self.defaults.object(forKey: "nav.lensCompass") as? Bool ?? true
    }

    func start(sensors: SensorBridge, glasses: GlassesStreamer) {
        self.sensors = sensors
        self.glasses = glasses
        sensors.onFix = { [weak self] fix in self?.locationChanged(fix) }
        sensors.onHeading = { [weak self] deg in self?.headingChanged(deg) }
        LensRouter.shared.navigator = self
    }

    // MARK: - destination

    /// An Apple Maps (or any maps) share link, or a place name.
    func setDestination(_ text: String) async throws {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return }
        status = "Finding \(t.count > 30 ? "place" : t)…"
        do {
            let (coordinate, name) = try await Self.resolve(t, near: fix?.coordinate)
            begin(coordinate, name: name)
        } catch {
            status = nil
            throw error
        }
        // the server keeps it as its fallback objective (and for discoveries)
        try? await HUDClient.fromSettings().setDestination(lat: destination?.latitude ?? 0,
                                                           lon: destination?.longitude ?? 0,
                                                           name: destinationName ?? t)
    }

    func clear() {
        generation += 1
        let wasActive = destination != nil
        destination = nil
        destinationName = nil
        reset()
        status = nil
        arrived = false
        heartbeat?.cancel(); heartbeat = nil
        if wasActive { sensors?.sendJSON(["route": ["active": false]]) }
        syncLens()
    }

    private func begin(_ coordinate: CLLocationCoordinate2D, name: String) {
        generation += 1
        destination = coordinate
        destinationName = name
        arrived = false
        reset()
        status = "Finding a route…"
        routing = false               // a request for the old place is answered and ignored
        calculate()
        startHeartbeat()
        syncLens()
    }

    private func reset() {
        route = nil
        hasRoute = false
        points = []
        cumulative = []
        turns = []
        lastSegment = 0
        offCount = 0
        progress = nil
    }

    // MARK: - routing

    private func calculate() {
        guard let destination, !routing else { return }
        routing = true
        lastRouted = Date()
        let request = MKDirections.Request()
        request.source = fix.map { MKMapItem(placemark: MKPlacemark(coordinate: $0.coordinate)) }
            ?? MKMapItem.forCurrentLocation()
        request.destination = MKMapItem(placemark: MKPlacemark(coordinate: destination))
        request.transportType = transport.mapKit
        request.requestsAlternateRoutes = false
        let gen = generation
        Task {
            defer { if gen == self.generation { self.routing = false } }
            do {
                let response = try await MKDirections(request: request).calculate()
                guard gen == self.generation else { return }
                guard let route = response.routes.first else { self.status = "No route there"; return }
                self.load(route)
                self.status = nil
                if let fix = self.fix { self.locationChanged(fix) }
            } catch {
                guard gen == self.generation else { return }
                self.status = "No route: \(error.localizedDescription)"
                log.error("MKDirections: \(String(describing: error))")
            }
        }
    }

    /// The route as one polyline plus the turns along it. Each MKRoute.Step's
    /// instruction is the maneuver at the start of that step's polyline.
    private func load(_ route: MKRoute) {
        var pts: [CLLocationCoordinate2D] = []
        var found: [Turn] = []
        for step in route.steps {
            let c = step.polyline.coordinates
            guard !c.isEmpty else { continue }
            let start: Int
            if let last = pts.last, Self.meters(last, c[0]) < 1 {
                start = pts.count - 1
                pts.append(contentsOf: c.dropFirst())
            } else {
                start = pts.count
                pts.append(contentsOf: c)
            }
            let text = step.instructions.trimmingCharacters(in: .whitespacesAndNewlines)
            if !text.isEmpty { found.append(Turn(index: start, along: 0, text: text, maneuver: .straight)) }
        }
        guard pts.count >= 2 else { status = "That route has no path"; return }
        var cum = [0.0]
        for i in 1..<pts.count { cum.append(cum[i - 1] + Self.meters(pts[i - 1], pts[i])) }
        let total = cum[cum.count - 1]
        // the last instruction is the arrival ("The destination is on your left");
        // pin it to the end of the line, and drop turns that sit on top of it
        let arrival = found.last?.text ?? "Arrive"
        found = found.dropLast().filter { total - cum[$0.index] > 10 && $0.index > 0 }
        for i in found.indices {
            found[i].along = cum[found[i].index]
            found[i].maneuver = Self.classify(pts, at: found[i].index)
        }
        found.append(Turn(index: pts.count - 1, along: total, text: arrival, maneuver: .arrive))

        self.route = route
        points = pts
        cumulative = cum
        turns = found
        lastSegment = 0
        offCount = 0
        hasRoute = true
    }

    // MARK: - following

    private func headingChanged(_ deg: Double) {
        heading = deg
        guard destination != nil, LensRouter.shared.clients.contains(.nav) else { return }
        // the lens compass only needs a new picture when it would visibly move
        if lensHeading == nil || abs(Self.delta(lensHeading!, deg)) >= 3 {
            lensHeading = deg
            LensRouter.shared.refresh()
        }
    }

    private func locationChanged(_ fix: CLLocation) {
        self.fix = fix
        guard let destination, !arrived else { return }
        guard hasRoute, let route else {
            if !routing, Date().timeIntervalSince(lastRouted) > 10 { calculate() }
            return
        }
        let here = fix.coordinate
        let total = cumulative[cumulative.count - 1]
        let (along, off, segment) = project(here)
        lastSegment = segment

        let good = fix.horizontalAccuracy >= 0 && fix.horizontalAccuracy < 50
        offCount = off > Self.offRouteMeters && good ? offCount + 1 : 0
        if offCount >= 2, !routing, Date().timeIntervalSince(lastRouted) > 8 {
            status = "Rerouting…"
            calculate()
        }

        let remaining = max(0, total - along)
        if remaining < Self.arriveMeters
            || Self.meters(here, destination) < Self.arriveMeters {
            arrive()
            return
        }
        let i = turns.firstIndex { $0.along > along + 3 } ?? turns.count - 1
        let turn = turns[i]
        let at = points[turn.index]
        let next = i + 1 < turns.count ? turns[i + 1].text : nil
        progress = Progress(
            instruction: turn.text,
            maneuver: turn.maneuver,
            lat: at.latitude, lon: at.longitude,
            stepDistance: max(0, turn.along - along),
            bearing: Self.bearing(here, at),
            nextInstruction: next,
            remaining: remaining,
            eta: total > 0 ? route.expectedTravelTime * remaining / total : 0,
            offRoute: off)
        if status == "Rerouting…", !routing { status = nil }
        publish()
        LensRouter.shared.refresh()
    }

    /// Distance along the route of the closest point to `p`, how far off the
    /// line `p` is, and the segment. Searches forward from the last segment
    /// (a few back for GPS jitter); far-ahead segments must be clearly closer,
    /// so a route that doubles back on itself doesn't skip you ahead.
    private func project(_ p: CLLocationCoordinate2D) -> (Double, Double, Int) {
        let k = Double.pi / 180 * 6_371_008.8
        let kx = k * cos(p.latitude * .pi / 180)
        func xy(_ c: CLLocationCoordinate2D) -> (Double, Double) {
            ((c.longitude - p.longitude) * kx, (c.latitude - p.latitude) * k)
        }
        var best = (along: cumulative[min(lastSegment, cumulative.count - 1)], off: Double.infinity,
                    score: Double.infinity, segment: lastSegment)
        let from = max(0, lastSegment - 3)
        guard from < points.count - 1 else { return (best.along, 0, best.segment) }
        for i in from..<(points.count - 1) {
            let a = xy(points[i]), b = xy(points[i + 1])
            let dx = b.0 - a.0, dy = b.1 - a.1
            let len2 = dx * dx + dy * dy
            let t = len2 > 0 ? max(0, min(1, -(a.0 * dx + a.1 * dy) / len2)) : 0
            let qx = a.0 + t * dx, qy = a.1 + t * dy
            let d = (qx * qx + qy * qy).squareRoot()
            let ahead = cumulative[i] - cumulative[min(lastSegment, cumulative.count - 1)]
            let score = d + (ahead > 200 ? 25 : 0)
            if score < best.score {
                best = (cumulative[i] + t * (cumulative[i + 1] - cumulative[i]), d, score, i)
            }
        }
        return (best.along, best.off, best.segment)
    }

    private func arrive() {
        arrived = true
        progress = nil
        status = "Arrived at \(destinationName ?? "your destination")"
        heartbeat?.cancel(); heartbeat = nil
        var dest: [String: Any] = ["name": destinationName ?? ""]
        if let destination { dest["lat"] = destination.latitude; dest["lon"] = destination.longitude }
        sensors?.sendJSON(["route": ["active": false, "arrived": true, "remaining_m": 0,
                                     "destination": dest] as [String: Any]])
        LensRouter.shared.refresh()
        // the HUD shows its arrival line, then the objective goes away
        let gen = generation
        Task {
            try? await Task.sleep(for: .seconds(10))
            guard gen == self.generation, self.arrived else { return }
            self.clear()
            try? await HUDClient.fromSettings().clearDestination()
        }
    }

    // MARK: - HUD server

    private func startHeartbeat() {
        heartbeat?.cancel()
        heartbeat = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(4))
                self?.publish(force: true)
            }
        }
    }

    /// {"route": {...}} on /ws/phone; server/navigation.py set_phone_route().
    private func publish(force: Bool = false) {
        guard let sensors, let destination, let p = progress, !arrived else { return }
        guard force || Date().timeIntervalSince(lastPublish) >= 1 else { return }
        lastPublish = Date()
        let routeStatus = status ?? (p.offRoute > Self.offRouteMeters ? "off route" : "apple maps")
        sensors.sendJSON(["route": [
            "active": true,
            "instruction": p.instruction,
            "step_distance": p.stepDistance.rounded(),
            "maneuver": ["lat": p.lat, "lon": p.lon, "bearing": (p.bearing * 10).rounded() / 10,
                         "type": p.maneuver.rawValue] as [String: Any],
            "next_instruction": p.nextInstruction ?? "",
            "remaining_m": p.remaining.rounded(),
            "eta_s": p.eta.rounded(),
            "destination": ["name": destinationName ?? "", "lat": destination.latitude,
                            "lon": destination.longitude] as [String: Any],
            "transport": transport.rawValue,
            "status": routeStatus,
        ] as [String: Any]])
    }

    // MARK: - lens

    private func syncLens() {
        let router = LensRouter.shared
        router.navigator = self
        if lensOn, destination != nil, let glasses {
            if router.clients.contains(.nav) { router.refresh() } else { router.want(.nav, on: glasses) }
        } else {
            router.release(.nav)
        }
    }

    /// Bearing to the next maneuver relative to where the phone faces
    /// (-180…180, + = right), when there is a heading.
    var relativeBearing: Double? {
        guard let p = progress, let heading else { return nil }
        return Self.delta(heading, p.bearing)
    }

    // MARK: - resolving a place

    enum PlaceError: LocalizedError {
        case notFound(String)
        var errorDescription: String? {
            switch self { case .notFound(let q): return "Apple Maps couldn't find \(q)." }
        }
    }

    /// Coordinates straight out of a share link when it has them (Apple Maps:
    /// coordinate= / ll= / daddr=; Google: @lat,lon / q=lat,lon), short
    /// links (maps.apple/p/…, goo.gl) followed to where they redirect, and
    /// anything else searched by name with MKLocalSearch, near you.
    static func resolve(_ text: String, near: CLLocationCoordinate2D?) async throws -> (CLLocationCoordinate2D, String) {
        var query = text
        if let url = URL(string: text), let scheme = url.scheme?.lowercased(), scheme.hasPrefix("http") || scheme == "maps" {
            var link = parseLink(url)
            if link.coordinate == nil, link.query == nil, scheme.hasPrefix("http"),
               let fetched = try? await URLSession.shared.data(from: url), let final = fetched.1.url {
                link = parseLink(final)
            }
            if let c = link.coordinate { return (c, link.name ?? link.query ?? "Pinned place") }
            guard let q = link.name ?? link.query else { throw PlaceError.notFound("that link") }
            query = q
        }
        let request = MKLocalSearch.Request()
        request.naturalLanguageQuery = query
        if let near {
            request.region = MKCoordinateRegion(center: near, latitudinalMeters: 30_000, longitudinalMeters: 30_000)
        }
        let response = try await MKLocalSearch(request: request).start()
        guard let item = response.mapItems.first else { throw PlaceError.notFound(query) }
        return (item.placemark.coordinate, item.name ?? query)
    }

    nonisolated static func parseLink(_ url: URL) -> (coordinate: CLLocationCoordinate2D?, name: String?, query: String?) {
        let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems ?? []
        func value(_ key: String) -> String? {
            items.first { $0.name.lowercased() == key }?.value?.trimmingCharacters(in: .whitespaces)
        }
        var coordinate: CLLocationCoordinate2D?
        for key in ["coordinate", "daddr", "destination", "ll", "q"] {
            if let v = value(key), let c = coordinates(in: v) { coordinate = c; break }
        }
        if coordinate == nil {
            let whole = url.absoluteString.removingPercentEncoding ?? url.absoluteString
            if let at = whole.range(of: "@") { coordinate = coordinates(in: String(whole[at.upperBound...])) }
        }
        let name = value("name")
        var query: String?
        for key in ["q", "address", "daddr", "destination"] {
            if let v = value(key), !v.isEmpty, coordinates(in: v) == nil { query = v; break }
        }
        return (coordinate, name, query)
    }

    nonisolated static func coordinates(in text: String) -> CLLocationCoordinate2D? {
        let pattern = #"(-?\d{1,3}\.\d{3,})\s*,\s*(-?\d{1,3}\.\d{3,})"#
        guard let re = try? NSRegularExpression(pattern: pattern),
              let m = re.firstMatch(in: text, range: NSRange(text.startIndex..., in: text)),
              let r1 = Range(m.range(at: 1), in: text), let r2 = Range(m.range(at: 2), in: text),
              let lat = Double(text[r1]), let lon = Double(text[r2]),
              abs(lat) <= 90, abs(lon) <= 180 else { return nil }
        return CLLocationCoordinate2D(latitude: lat, longitude: lon)
    }

    // MARK: - geometry

    nonisolated static func meters(_ a: CLLocationCoordinate2D, _ b: CLLocationCoordinate2D) -> Double {
        CLLocation(latitude: a.latitude, longitude: a.longitude)
            .distance(from: CLLocation(latitude: b.latitude, longitude: b.longitude))
    }

    nonisolated static func bearing(_ a: CLLocationCoordinate2D, _ b: CLLocationCoordinate2D) -> Double {
        let lat1 = a.latitude * .pi / 180, lat2 = b.latitude * .pi / 180
        let dlon = (b.longitude - a.longitude) * .pi / 180
        let y = sin(dlon) * cos(lat2)
        let x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
        return (atan2(y, x) * 180 / .pi + 360).truncatingRemainder(dividingBy: 360)
    }

    /// Signed shortest turn from `from` to `to`, -180…180.
    nonisolated static func delta(_ from: Double, _ to: Double) -> Double {
        var d = (to - from).truncatingRemainder(dividingBy: 360)
        if d > 180 { d -= 360 }
        if d < -180 { d += 360 }
        return d
    }

    /// The turn at `i`: heading over ~20 m before it vs ~20 m after it.
    nonisolated static func classify(_ pts: [CLLocationCoordinate2D], at i: Int) -> Maneuver {
        guard i > 0, i < pts.count - 1 else { return .straight }
        var a = i - 1
        while a > 0, meters(pts[a], pts[i]) < 20 { a -= 1 }
        var b = i + 1
        while b < pts.count - 1, meters(pts[i], pts[b]) < 20 { b += 1 }
        let turn = delta(bearing(pts[a], pts[i]), bearing(pts[i], pts[b]))
        switch abs(turn) {
        case ..<20: return .straight
        case ..<60: return turn < 0 ? .slightLeft : .slightRight
        case ..<150: return turn < 0 ? .left : .right
        default: return .uturn
        }
    }
}

private extension MKPolyline {
    var coordinates: [CLLocationCoordinate2D] {
        var c = [CLLocationCoordinate2D](repeating: kCLLocationCoordinate2DInvalid, count: pointCount)
        getCoordinates(&c, range: NSRange(location: 0, length: pointCount))
        return c
    }
}
