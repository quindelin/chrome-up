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
    var actionError: String?

    var interval: Duration = .seconds(5)
    private var loop: Task<Void, Never>?

    /// What the big status card says, from most to least "live".
    enum Headline: Equatable {
        case liveOn([String])        // restreaming to viewers
        case program                 // OBS program up, nobody watching yet
        case glassesOnly             // ingest up, OBS not publishing
        case idle                    // VM up, glasses not sending
        case offline(String)         // VM stopped / unreachable / bad login
        case loading
    }

    var headline: Headline {
        if case .error(let why) = reach, stack == nil || isStale { return .offline(why) }
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
        do {
            let s = try await StackClient.fromSettings().stack()
            stack = s
            updated = Date()
            reach = .ok
            let isLive = !s.liveOn.isEmpty
            if isLive != wasLive {    // went live / dropped: you feel it in your pocket
                UINotificationFeedbackGenerator().notificationOccurred(isLive ? .success : .warning)
            }
        } catch {
            reach = .error(error.localizedDescription)
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
