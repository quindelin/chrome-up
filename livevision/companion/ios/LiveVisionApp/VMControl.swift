import Foundation

/// Start / stop / status for the streaming VM via the Cloud Run function
/// deployed by `deploy/obs-vps/gcp.sh control-deploy`. Unlike the VPS itself,
/// it answers while the VM is stopped, which is the point.
struct VMClient {
    var base: URL
    var token: String

    struct State: Decodable, Equatable {
        var status: String          // RUNNING, TERMINATED, STAGING, PROVISIONING, STOPPING, ...
        var ip: String?
        var machineType: String?

        var isRunning: Bool { status == "RUNNING" }
        var isStopped: Bool { status == "TERMINATED" || status == "STOPPED" || status == "SUSPENDED" }
        var isStarting: Bool { status == "PROVISIONING" || status == "STAGING" }
        var isStopping: Bool { status == "STOPPING" || status == "SUSPENDING" }
    }

    /// nil until `gcp.sh control-deploy` + `gcp.sh companion` filled in the build.
    static func fromSettings() -> VMClient? {
        let host = Settings.controlHost, token = Settings.controlToken
        guard !host.isEmpty, !token.isEmpty, let url = URL(string: "https://\(host)") else { return nil }
        return VMClient(base: url, token: token)
    }

    private static let session: URLSession = {
        let c = URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest = 15        // a cold Cloud Run start takes a few seconds
        return URLSession(configuration: c)
    }()

    private func call(_ path: String, method: String = "GET") async throws -> State {
        var r = URLRequest(url: base.appending(path: path))
        r.httpMethod = method
        r.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let data: Data, resp: URLResponse
        do { (data, resp) = try await Self.session.data(for: r) } catch {
            throw StackError.unreachable(error.localizedDescription)
        }
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        if code == 401 { throw StackError.refused("VM control token rejected (re-run gcp.sh companion)") }
        guard (200..<300).contains(code) else { throw StackError.server(code) }
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return try d.decode(State.self, from: data)
    }

    func status() async throws -> State { try await call("") }
    func start() async throws -> State { try await call("start", method: "POST") }
    func stop() async throws -> State { try await call("stop", method: "POST") }
}
