import Foundation
import Observation
import UIKit

/// Polls the VPS while the app is in front and keeps the last good snapshot,
/// so a dropped poll on cellular shows as "stale" instead of blanking out.
@MainActor
@Observable
final class StackStore {
    enum Reach: Equatable {
        case unknown, ok, error(String)
    }

    private(set) var stack: Stack?
    private(set) var reach: Reach = .unknown
    private(set) var updated: Date?
    private(set) var busyTargets: Set<String> = []
    /// The stream title on the VPS and the last per-platform answers
    private(set) var title: TitleState?
    private(set) var titleBusy = false
    var actionError: String?
    /// The VM itself, from the start/stop function (nil if not configured)
    private(set) var vm: VMClient.State?
    /// "start" / "stop" while we're waiting for one we asked for to finish
    private(set) var vmAction: String?
    var vmControlAvailable: Bool { VMClient.fromSettings() != nil }
    private var polls = 0

    var interval: Duration = .seconds(5)
    private var loop: Task<Void, Never>?

    /// What the big status card says, from most to least "live".
    enum Headline: Equatable {
        case liveOn([String])        // restreaming to viewers
        case program                 // OBS program up, nobody watching yet
        case glassesOnly             // ingest up, OBS not publishing
        case idle                    // VM up, glasses not sending
        case vmStopped               // VM is off: nothing billing but the disk
        case vmChanging(String)      // starting or stopping
        case offline(String)         // unreachable / bad login
        case loading
    }

    var headline: Headline {
        if case .error(let why) = reach, stack == nil || isStale {
            if let vm {
                if vm.isStopped && vmAction != "start" { return .vmStopped }
                if vm.isStarting || (vmAction == "start" && !vm.isStopping) {
                    return .vmChanging("Starting the VPS… about a minute")
                }
                if vm.isStopping || vmAction == "stop" { return .vmChanging("Stopping the VPS…") }
            }
            return .offline(why)
        }
        if vmAction == "stop" { return .vmChanging("Stopping the VPS…") }
        guard let s = stack else { return .loading }
        if !s.liveOn.isEmpty { return .liveOn(s.liveOn) }
        if s.program?.isLive == true { return .program }
        if s.ingest?.isLive == true { return .glassesOnly }
        return .idle
    }

    /// No good answer for three polls: don't pretend we still know.
    var isStale: Bool {
        guard let u = updated else { return true }
        return Date().timeIntervalSince(u) > 3 * interval.seconds + 2
    }

    func start() {
        guard loop == nil else { return }
        loop = Task { [weak self] in
            while !Task.isCancelled {
                await self?.refresh()
                try? await Task.sleep(for: self?.interval ?? .seconds(5))
            }
        }
    }

    func stop() {
        loop?.cancel()
        loop = nil
    }

    func refresh() async {
        let wasLive = !(stack?.liveOn.isEmpty ?? true)
        polls += 1
        do {
            let s = try await StackClient.fromSettings().stack()
            stack = s
            updated = Date()
            reach = .ok
            if vmAction == "start" { vmAction = nil }      // it's up and serving
            if polls % 12 == 1 { await refreshVM() }       // the Stop button's state, now and then
            if title == nil || polls % 12 == 1, !titleBusy { // voice or another device may change it
                title = (try? await StackClient.fromSettings().title()) ?? title
            }
            let isLive = !s.liveOn.isEmpty
            if isLive != wasLive {    // went live / dropped: you feel it in your pocket
                UINotificationFeedbackGenerator().notificationOccurred(isLive ? .success : .warning)
            }
        } catch {
            reach = .error(error.localizedDescription)
            await refreshVM()                              // stopped, or just unreachable?
        }
    }

    func refreshVM() async {
        guard let c = VMClient.fromSettings() else { return }
        if let state = try? await c.status() {
            vm = state
            follow(state)
            if vmAction == "stop", state.isStopped { vmAction = nil; stack = nil }
        }
    }

    /// The VM gets a new external IP on every start (unless `gcp.sh static-ip`),
    /// and the build only knew the old one: every call then went to a dead
    /// address until a rebuild. Follow the running VM's IP instead. Only an
    /// sslip.io host follows: a real domain you typed in stays.
    private func follow(_ state: VMClient.State) {
        guard state.isRunning, let ip = state.ip, !ip.isEmpty else { return }
        let host = ip.replacingOccurrences(of: ".", with: "-") + ".sslip.io"
        let current = Settings.bareHost ?? ""
        guard current != host, current.isEmpty || current.hasSuffix(".sslip.io") else { return }
        Settings.host = host
        log.notice("VM is at \(ip) now: host \(host)")
        NotificationCenter.default.post(name: Settings.hostChanged, object: host)
        Task { await refresh() }
    }

    func startVM() async { await vmCall("start") { try await $0.start() } }
    func stopVM() async { await vmCall("stop") { try await $0.stop() } }

    private func vmCall(_ action: String, _ call: (VMClient) async throws -> VMClient.State) async {
        guard let c = VMClient.fromSettings() else { return }
        vmAction = action
        do {
            let state = try await call(c)
            vm = state
            follow(state)
        } catch {
            vmAction = nil
            actionError = error.localizedDescription
        }
    }

    func saveTitle(_ text: String) async {
        titleBusy = true
        defer { titleBusy = false }
        do {
            title = try await StackClient.fromSettings().setTitle(text)
            let ok = title?.results?.contains { $0.ok } ?? false
            UINotificationFeedbackGenerator().notificationOccurred(ok ? .success : .warning)
        } catch {
            actionError = error.localizedDescription
        }
    }

    func setRestream(_ name: String, on: Bool) async {
        busyTargets.insert(name)
        defer { busyTargets.remove(name) }
        do {
            try await StackClient.fromSettings().restream(name, on: on)
        } catch {
            actionError = error.localizedDescription
        }
        await refresh()
    }
}

private extension Duration {
    var seconds: Double { Double(components.seconds) + Double(components.attoseconds) / 1e18 }
}
