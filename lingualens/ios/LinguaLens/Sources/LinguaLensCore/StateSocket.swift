import Foundation

/// The server pushes a full state snapshot on connect and after every change
/// (App.broadcast in server/main.py). This keeps one websocket open, pings it
/// so Cloud Run and carrier NATs do not drop it, and reconnects on its own -
/// the same 1.5 s retry app.js uses.
public final class StateSocket: @unchecked Sendable {
    public enum Event: Sendable {
        case connected
        case state(LessonState)
        case disconnected(String)
    }

    public let config: ServerConfig
    private let session: URLSession
    private let lock = NSLock()
    private var task: URLSessionWebSocketTask?
    private var runner: Task<Void, Never>?

    public init(config: ServerConfig, session: URLSession = .shared) {
        self.config = config
        self.session = session
    }

    /// Events until `stop()`. Only one consumer.
    public func events() -> AsyncStream<Event> {
        AsyncStream { continuation in
            let runner = Task { [weak self] in
                while !Task.isCancelled, let self {
                    await self.runOnce(continuation)
                    if Task.isCancelled { break }
                    try? await Task.sleep(nanoseconds: 1_500_000_000)
                }
                continuation.finish()
            }
            lock.withLock { self.runner = runner }
            continuation.onTermination = { _ in runner.cancel() }
        }
    }

    public func stop() {
        lock.withLock {
            runner?.cancel()
            task?.cancel(with: .goingAway, reason: nil)
            task = nil
        }
    }

    private func runOnce(_ out: AsyncStream<Event>.Continuation) async {
        var request = URLRequest(url: config.socketURL)
        config.authorize(&request)
        let ws = session.webSocketTask(with: request)
        lock.withLock { task = ws }
        ws.resume()

        let pinger = Task {
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 25_000_000_000)
                ws.sendPing { _ in }
            }
        }
        defer { pinger.cancel() }

        var announced = false
        do {
            while !Task.isCancelled {
                let message = try await ws.receive()
                let data: Data
                switch message {
                case .string(let s): data = Data(s.utf8)
                case .data(let d): data = d
                @unknown default: continue
                }
                if !announced { out.yield(.connected); announced = true }
                if let state = try? JSONDecoder().decode(LessonState.self, from: data) {
                    out.yield(.state(state))
                }
            }
        } catch {
            let reason = ws.closeCode == URLSessionWebSocketTask.CloseCode(rawValue: 4401)
                ? "Server refused the key (4401)." : error.localizedDescription
            out.yield(.disconnected(reason))
        }
        ws.cancel(with: .goingAway, reason: nil)
    }
}
