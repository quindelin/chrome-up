import Foundation

/// GET /api/autoclip/stack on the VPS: the whole box in one poll.
/// Every field is optional so an older or partly-down server still decodes.
struct Stack: Decodable {
    var ts: Double?
    var ingest: Feed?
    var program: Feed?
    var restream: Restream?
    var autoclip: Autoclip?
    var host: Host?

    /// One MediaMTX path: the glasses feed, or OBS's composited program.
    struct Feed: Decodable {
        var ok: Bool?
        var live: Bool?
        var since: String?
        var bitrateKbps: Int?
        var tracks: [String]?
        var readers: Int?
        var error: String?

        var isLive: Bool { live ?? false }
        var sinceDate: Date? { since.flatMap(parseISO) }
    }

    struct Restream: Decodable {
        var enabled: Bool?
        var activeCount: Int?
        var targets: [Target]?
    }

    struct Target: Decodable, Identifiable {
        var name: String
        var enabled: Bool?
        var keySet: Bool?
        var active: Bool?
        var uptimeSeconds: Double?
        var lastError: String?
        var id: String { name }
    }

    struct Autoclip: Decodable {
        var publishMode: String?
        var pending: Int?
        var cycles: Int?
        var clips: Int?
        var lastCycleTs: Double?
        var lastNote: String?
    }

    struct Host: Decodable {
        var cpus: Int?
        var load: [Double]?
        var memTotal: Int64?
        var memAvailable: Int64?
        var uptimeSeconds: Double?
        var diskTotal: Int64?
        var diskFree: Int64?
        var error: String?
    }

    /// Platforms we are actually broadcasting to right now.
    var liveOn: [String] { (restream?.targets ?? []).filter { $0.active ?? false }.map(\.name) }
}

private func parseISO(_ s: String) -> Date? {
    let f = ISO8601DateFormatter()
    f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    if let d = f.date(from: s) { return d }
    f.formatOptions = [.withInternetDateTime]
    return f.date(from: s)
}

/// GET/POST /api/autoclip/live/title: the stream title and what each platform said.
struct TitleState: Decodable {
    var title: String?
    var results: [Result]?
    var platforms: [Platform]?

    struct Result: Decodable, Identifiable {
        var platform: String
        var ok: Bool
        var message: String?
        var id: String { platform }
    }

    struct Platform: Decodable {
        var name: String
        var supported: Bool?
        var configured: Bool?
    }

    /// "Twitch ✓ · YouTube: no OAuth client set · X: no title API"
    var summary: String {
        (results ?? []).map { r in
            let name = r.platform == "youtube" ? "YouTube" : r.platform.count <= 2 ? r.platform.uppercased() : r.platform.capitalized
            if r.ok { return "\(name) ✓" }
            let why = r.message ?? "failed"
            return "\(name): \(why.hasPrefix("not supported") ? "no title API" : why)"
        }.joined(separator: " · ")
    }
}

enum StackError: LocalizedError {
    case noHost, unauthorized, unreachable(String), server(Int), refused(String)

    var errorDescription: String? {
        switch self {
        case .noHost: "Set the VPS host in Settings."
        case .unauthorized: "Wrong user or password (AUTOCLIP_PASSWORD in the VM's .env)."
        case .unreachable(let why): "VPS unreachable — stopped, or no network. \(why)"
        case .server(let code): "VPS answered HTTP \(code)."
        case .refused(let why): "Refused: \(why)"
        }
    }
}

/// Talks to autoclip's REST API through Caddy (https://<host>/autoclip/...).
struct StackClient {
    var base: URL
    var user: String
    var password: String

    static func fromSettings() throws -> StackClient {
        guard let base = Settings.baseURL else { throw StackError.noHost }
        return StackClient(base: base, user: Settings.user, password: Settings.password)
    }

    private static let session: URLSession = {
        let c = URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest = 6
        c.waitsForConnectivity = false
        return URLSession(configuration: c)
    }()

    private func request(_ path: String, method: String = "GET") -> URLRequest {
        var r = URLRequest(url: base.appending(path: path))
        r.httpMethod = method
        let token = Data("\(user):\(password)".utf8).base64EncodedString()
        r.setValue("Basic \(token)", forHTTPHeaderField: "Authorization")
        r.setValue("application/json", forHTTPHeaderField: "Accept")
        return r
    }

    private func send(_ r: URLRequest) async throws -> Data {
        let data: Data, resp: URLResponse
        do {
            (data, resp) = try await Self.session.data(for: r)
        } catch {
            throw StackError.unreachable(error.localizedDescription)
        }
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        if code == 401 { throw StackError.unauthorized }
        // Caddy answers 502 when the VM is up but autoclip is not (yet)
        guard (200..<300).contains(code) else { throw StackError.server(code) }
        return data
    }

    func stack() async throws -> Stack {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return try d.decode(Stack.self, from: try await send(request("api/autoclip/stack")))
    }

    /// "go live on <name>" / "stop <name>", same as the voice commands.
    func restream(_ name: String, on: Bool) async throws {
        let data = try await send(request("api/autoclip/live/\(on ? "start" : "stop")/\(name)", method: "POST"))
        struct Result: Decodable { var ok: Bool?; var message: String? }
        let r = try? JSONDecoder().decode(Result.self, from: data)
        if r?.ok == false { throw StackError.refused(r?.message ?? "refused") }
    }

    func title() async throws -> TitleState {
        try Self.decoder.decode(TitleState.self, from: try await send(request("api/autoclip/live/title")))
    }

    /// Sets it on every restream platform with an API; the answer has one result each.
    func setTitle(_ title: String) async throws -> TitleState {
        var r = request("api/autoclip/live/title", method: "POST")
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        r.httpBody = try JSONEncoder().encode(["title": title])
        r.timeoutInterval = 30          // a few round trips to each platform
        return try Self.decoder.decode(TitleState.self, from: try await send(r))
    }

    private static let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }()

    /// The approval queue page (Safari asks for the same login).
    var approvalPage: URL { URL(string: base.absoluteString + "/") ?? base }
}
