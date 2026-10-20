import Foundation
import MWDATCore
import MWDATDisplay
import MWDATInputs
import UIKit

/// The one Display on the Ray-Ban Display lens, shared by the teleprompter
/// and Apple Maps directions.
///
/// The glasses allow one DAT session, and a session takes one Display: the
/// camera stream, the teleprompter and the directions all ride
/// GlassesStreamer.deviceSession. So nobody else calls addDisplay(); clients
/// ask for the lens here and the router composes one screen from whoever
/// wants it (every send replaces the whole view):
///   - prompter only: the script page, as before
///   - directions only: compass strip with the quest marker on the next
///     maneuver, the instruction, and the trip
///   - both: a one-line "next turn" strip above the script page
///
/// Sends are coalesced to one in flight and at most every 0.4 s (Bluetooth
/// is shared with the camera stream), and the screen is re-sent every 12 s:
/// the lens dims after 20 s without a send and sleeps at 25 s.
///
/// No SwiftUI here: MWDATDisplay's Text/Image would clash with SwiftUI's.
@MainActor
@Observable
final class LensRouter {
    static let shared = LensRouter()

    enum Client: Hashable { case prompter, nav }

    enum State: Equatable {
        case off
        case waiting        // asked to show, no glasses session yet
        case starting
        case showing
        case failed(String)
    }

    private(set) var state: State = .off
    private(set) var clients: Set<Client> = []
    /// The last input the glasses reported, for the status line.
    private(set) var lastInput: String?

    @ObservationIgnored weak var prompter: Teleprompter?
    @ObservationIgnored weak var navigator: RouteNavigator?

    @ObservationIgnored private var display: Display?
    @ObservationIgnored private var inputs: Inputs?
    @ObservationIgnored private weak var attachedTo: DeviceSession?
    @ObservationIgnored private var tokens = ListenerTokenBag()
    @ObservationIgnored private var inputTask: Task<Void, Never>?
    @ObservationIgnored private var keepAwake: Task<Void, Never>?
    @ObservationIgnored private var flushTask: Task<Void, Never>?
    @ObservationIgnored private var sending = false
    @ObservationIgnored private var pending = false
    @ObservationIgnored private var lastSend = Date.distantPast

    private static let minInterval: TimeInterval = 0.4

    // MARK: - clients

    /// Attaches once the glasses session is up (connecting it if needed) and
    /// keeps re-attaching after reconnects until every client has released.
    func want(_ client: Client, on glasses: GlassesStreamer) {
        clients.insert(client)
        if state == .off || state.isFailure { state = .waiting }
        if glasses.link == .idle || glasses.link == .unregistered { glasses.connect() }
        sessionChanged(glasses)
        refresh()
    }

    func release(_ client: Client) {
        guard clients.remove(client) != nil else { return }
        if clients.isEmpty {
            state = .off
            detach()
        } else {
            refresh()
        }
    }

    /// Call when the glasses link changes (connect, pause, reconnect).
    func sessionChanged(_ glasses: GlassesStreamer) {
        guard !clients.isEmpty else { return }
        guard glasses.link == .connected, let session = glasses.deviceSession else {
            if glasses.deviceSession == nil, attachedTo != nil { detach(); state = .waiting }
            return
        }
        if session === attachedTo, display != nil { return }
        attach(to: session)
    }

    // MARK: - the Display

    private func attach(to session: DeviceSession) {
        detach()
        state = .starting
        attachedTo = session
        let d: Display
        do {
            d = try session.addDisplay()
        } catch {
            state = .failed("No lens: \(error.localizedDescription). This needs Meta Ray-Ban Display glasses.")
            log.error("addDisplay: \(String(describing: error))")
            return
        }
        display = d
        d.statePublisher.listen { [weak self] state in
            Task { @MainActor in self?.displayChanged(state) }
        }.store(in: tokens)
        d.start()
        if d.state == .started { displayChanged(.started) }

        // Neural Band / temple swipes. Experimental in DAT: without it the
        // lens tap, the phone and auto-scroll still work.
        do {
            if let i = try session.addInputs() {
                inputs = i
                inputTask = Task { [weak self] in
                    for await event in i.events { self?.handle(event) }
                }
            }
        } catch {
            log.notice("inputs unavailable: \(String(describing: error))")
        }
    }

    private func detach() {
        keepAwake?.cancel(); keepAwake = nil
        inputTask?.cancel(); inputTask = nil
        flushTask?.cancel(); flushTask = nil
        pending = false
        display?.stop()
        display = nil
        if inputs != nil { try? attachedTo?.removeInputs() }
        inputs = nil
        attachedTo = nil
        let old = tokens
        tokens = ListenerTokenBag()
        Task { await old.cancelAll() }
    }

    private func displayChanged(_ new: DisplayState) {
        switch new {
        case .started:
            state = .showing
            refresh()
            startKeepAwake()
        case .stopped:
            // the wearer ended it (two-finger tap) or the session went away
            keepAwake?.cancel(); keepAwake = nil
            display = nil
            if state == .showing || state == .starting { state = .waiting }
        case .starting, .stopping:
            break
        }
    }

    private func handle(_ event: InputEvent) {
        switch event {
        case .nav(let dir, let source, _): lastInput = "\(dir) · \(source)"
        case .select(let source, _): lastInput = "select · \(source)"
        case .back(let source, _): lastInput = "back · \(source)"
        default: break
        }
        // swipes turn script pages; directions need no input
        if clients.contains(.prompter) { prompter?.lensInput(event) }
    }

    private func startKeepAwake() {
        keepAwake?.cancel()
        keepAwake = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(12))
                self?.refresh()
            }
        }
    }

    // MARK: - sending

    /// Something on the lens changed: send the composed screen soon.
    func refresh() {
        guard display != nil, state == .showing else { return }
        pending = true
        guard !sending, flushTask == nil else { return }
        let wait = Self.minInterval - Date().timeIntervalSince(lastSend)
        if wait > 0 {
            flushTask = Task { [weak self] in
                try? await Task.sleep(for: .seconds(wait))
                guard !Task.isCancelled else { return }
                self?.flushTask = nil
                self?.flush()
            }
        } else {
            flush()
        }
    }

    private func flush() {
        guard pending, let display, state == .showing else { pending = false; return }
        pending = false
        sending = true
        lastSend = Date()
        let view = compose()
        Task { [weak self] in
            do { try await display.send(view) }
            catch { log.error("display send: \(String(describing: error))") }
            guard let self else { return }
            self.sending = false
            if self.pending { self.refresh() }
        }
    }

    private func compose() -> FlexBox {
        let nav = clients.contains(.nav) ? navigator : nil
        if clients.contains(.prompter), let prompter {
            return FlexBox(direction: .column, spacing: 10, padding: EdgeInsets(all: 12)) {
                if let nav { NavLens.strip(nav) }
                prompter.lensBody()
            }
            .onTap { [weak self] in Task { @MainActor in self?.prompter?.next() } }
        }
        if let nav { return NavLens.full(nav) }
        return FlexBox(direction: .column, padding: EdgeInsets(all: 12)) {
            Text("LiveVision", style: .meta, color: .secondary)
        }
    }
}

private extension LensRouter.State {
    var isFailure: Bool { if case .failed = self { return true } else { return false } }
}

// MARK: - directions on the lens

/// Apple Maps directions as lens components.
@MainActor
enum NavLens {
    /// The whole screen: compass strip (or arrow), the instruction, the trip.
    static func full(_ nav: RouteNavigator) -> FlexBox {
        let p = nav.progress
        let image = p != nil && nav.lensCompass ? CompassStrip.render(nav) : nil
        return FlexBox(direction: .column, spacing: 10, crossAlignment: .center, padding: EdgeInsets(all: 12)) {
            if let image {
                Image(image: image, sizePreset: .fill)
            } else if let p {
                FlexBox(direction: .row, spacing: 10, crossAlignment: .center) {
                    Icon(name: arrow(nav))
                    Text(distance(p.stepDistance), style: .heading)
                }
            }
            if let p {
                Text(p.instruction, style: .heading)
                Text(trip(nav, p), style: .meta, color: .secondary)
            } else {
                Text(nav.status ?? "Finding a route…", style: .body)
                if let name = nav.destinationName { Text(name, style: .meta, color: .secondary) }
            }
        }
    }

    /// One line above the teleprompter's page.
    static func strip(_ nav: RouteNavigator) -> FlexBox {
        FlexBox(direction: .row, spacing: 8, crossAlignment: .center) {
            if let p = nav.progress {
                Icon(name: icon(p.maneuver))
                Text("\(distance(p.stepDistance)) · \(p.instruction)", style: .meta)
            } else {
                Text(nav.status ?? "Finding a route…", style: .meta, color: .secondary)
            }
        }
    }

    /// Which way to go from where you face; without a heading, the turn itself.
    static func arrow(_ nav: RouteNavigator) -> IconName {
        guard let rel = nav.relativeBearing else { return icon(nav.progress?.maneuver ?? .straight) }
        switch rel {
        case -35...35: return .caretUp
        case 35...150: return .arrowRight
        case -150 ... -35: return .arrowLeft
        default: return .arrowULeft
        }
    }

    static func icon(_ m: RouteNavigator.Maneuver) -> IconName {
        switch m {
        case .left, .slightLeft: return .arrowLeft
        case .right, .slightRight: return .arrowRight
        case .uturn: return .arrowULeft
        case .arrive: return .house
        case .straight: return .caretUp
        }
    }

    static func distance(_ m: Double) -> String {
        if m >= 1000 { return String(format: "%.1f km", m / 1000) }
        if m >= 100 { return "\(Int((m / 10).rounded()) * 10) m" }
        return "\(Int(m.rounded())) m"
    }

    static func trip(_ nav: RouteNavigator, _ p: RouteNavigator.Progress) -> String {
        let mins = max(1, Int((p.eta / 60).rounded()))
        let time = mins < 60 ? "\(mins) min" : "\(mins / 60) h \(String(format: "%02d", mins % 60)) min"
        let name = nav.destinationName.map { "\($0) · " } ?? ""
        return "\(name)\(distance(p.remaining)) · \(time)"
    }
}

/// The HUD's compass band, small, for the lens: cardinals turning with the
/// phone's heading and the gold quest marker on the next maneuver with its
/// distance. Black is transparent on the additive display, so it's line art
/// on black, ~600x130 at 1x (a few KB as PNG).
@MainActor
enum CompassStrip {
    static let size = CGSize(width: 600, height: 130)
    static let span = 180.0       // degrees across, as on the HUD

    static func render(_ nav: RouteNavigator) -> UIImage? {
        guard let p = nav.progress, let heading = nav.heading else { return nil }
        let format = UIGraphicsImageRendererFormat()
        format.scale = 1
        format.opaque = true
        let w = size.width, inner = w - 60, ppd = inner / span
        let top = 34.0, bandH = 44.0, mid = top + bandH / 2
        return UIGraphicsImageRenderer(size: size, format: format).image { ctx in
            let g = ctx.cgContext
            UIColor.black.setFill()
            g.fill(CGRect(origin: .zero, size: size))

            // band edges
            g.setStrokeColor(UIColor(white: 0.7, alpha: 1).cgColor)
            g.setLineWidth(2)
            for y in [top, top + bandH] {
                g.move(to: CGPoint(x: 30, y: y)); g.addLine(to: CGPoint(x: w - 30, y: y))
            }
            g.strokePath()

            // cardinals, intercardinals and 15° ticks
            let labels = [0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"]
            for deg in stride(from: 0, to: 360, by: 15) {
                let rel = RouteNavigator.delta(heading, Double(deg))
                guard abs(rel) <= span / 2 - 4 else { continue }
                let x = w / 2 + rel * ppd
                if let label = labels[deg] {
                    let cardinal = label.count == 1
                    draw(label, at: CGPoint(x: x, y: mid), size: cardinal ? 32 : 20,
                         color: UIColor(white: cardinal ? 1 : 0.75, alpha: 1))
                } else {
                    g.setStrokeColor(UIColor(white: 0.55, alpha: 1).cgColor)
                    g.setLineWidth(2)
                    g.move(to: CGPoint(x: x, y: top + bandH - 10)); g.addLine(to: CGPoint(x: x, y: top + bandH))
                    g.strokePath()
                }
            }

            // where you face
            g.setFillColor(UIColor(white: 0.85, alpha: 1).cgColor)
            g.move(to: CGPoint(x: w / 2 - 7, y: top - 12))
            g.addLine(to: CGPoint(x: w / 2 + 7, y: top - 12))
            g.addLine(to: CGPoint(x: w / 2, y: top - 3))
            g.closePath(); g.fillPath()

            // quest marker on the next maneuver; parked at the edge when behind you
            let rel = RouteNavigator.delta(heading, p.bearing)
            let clamped = max(-span / 2 + 8, min(span / 2 - 8, rel))
            let x = w / 2 + clamped * ppd
            let gold = UIColor(red: 0.95, green: 0.84, blue: 0.55, alpha: 1)
            g.setFillColor(gold.cgColor)
            g.move(to: CGPoint(x: x - 12, y: mid - 16))
            g.addLine(to: CGPoint(x: x, y: mid - 9))
            g.addLine(to: CGPoint(x: x + 12, y: mid - 16))
            g.addLine(to: CGPoint(x: x, y: mid + 14))
            g.closePath(); g.fillPath()
            draw(NavLens.distance(p.stepDistance), at: CGPoint(x: x, y: top + bandH + 22), size: 26, color: .white)
        }
    }

    private static func draw(_ text: String, at center: CGPoint, size: CGFloat, color: UIColor) {
        let font = UIFont(name: "Futura-CondensedMedium", size: size) ?? .systemFont(ofSize: size, weight: .medium)
        let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: color]
        let s = text as NSString
        let box = s.size(withAttributes: attrs)
        s.draw(at: CGPoint(x: center.x - box.width / 2, y: center.y - box.height / 2), withAttributes: attrs)
    }
}
