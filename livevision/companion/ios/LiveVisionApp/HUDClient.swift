import Foundation

/// The HUD server (https://<host>/, no auth) and autoclip's clip queue
/// (https://<host>/autoclip/, basic auth): everything the old web control
/// panel, /phone page and approval page did, for the Control and Clips tabs.
struct HUDClient {
    var root: URL                 // https://<host>
    var clipsBase: URL            // https://<host>/autoclip
    var user: String
    var password: String

    static func fromSettings() throws -> HUDClient {
        guard let base = Settings.baseURL, let host = base.host() else { throw StackError.noHost }
        return HUDClient(root: URL(string: "https://\(host)")!, clipsBase: base,
                         user: Settings.user, password: Settings.password)
    }

    /// wss://<host>/ws/phone: heading, GPS, motion and gestures, as /phone sent them
    var phoneSocket: URL { URL(string: root.absoluteString.replacingOccurrences(of: "https://", with: "wss://") + "/ws/phone")! }

    private static let session: URLSession = {
        let c = URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest = 8
        return URLSession(configuration: c)
    }()

    private func send(_ url: URL, method: String = "GET", json: [String: Any]? = nil, auth: Bool = false) async throws -> Data {
        var r = URLRequest(url: url)
        r.httpMethod = method
        if let json {
            r.httpBody = try JSONSerialization.data(withJSONObject: json)
            r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if auth {
            let token = Data("\(user):\(password)".utf8).base64EncodedString()
            r.setValue("Basic \(token)", forHTTPHeaderField: "Authorization")
        }
        let data: Data, resp: URLResponse
        do { (data, resp) = try await Self.session.data(for: r) } catch {
            throw StackError.unreachable(error.localizedDescription)
        }
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        if code == 401 { throw StackError.unauthorized }
        guard (200..<300).contains(code) else { throw StackError.server(code) }
        return data
    }

    private func decode<T: Decodable>(_ type: T.Type, _ data: Data) throws -> T {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return try d.decode(T.self, from: data)
    }

    // MARK: HUD

    struct Status: Decodable {
        var skills: [String: Skill]?
        var playerLevel: Int?
        var nav: Nav?
        var phones: Int?
    }
    struct Skill: Decodable {
        var name: String?
        var level: Int
        var xp: Double?          // 0..1 toward the next level
        var active: Bool?
    }
    struct Nav: Decodable {
        var active: Bool?
        var status: String?
        var objective: Objective?
    }
    struct Objective: Decodable {
        var name: String?
        var step: String?
        var distance: Double?
    }

    func status() async throws -> Status {
        try decode(Status.self, try await send(root.appending(path: "api/status")))
    }

    /// tap / swipe_left / swipe_right / spread, same as the /phone pad
    func gesture(_ g: String) async throws {
        _ = try await send(root.appending(path: "api/gesture"), method: "POST", json: ["gesture": g])
    }

    func shout(_ word: String = "Fus Ro Dah") async throws {
        _ = try await send(root.appending(path: "api/shout"), method: "POST", json: ["word": word])
    }

    /// A maps share link (anything with coordinates) or a place name.
    func setDestination(_ text: String) async throws {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        let body: [String: Any] = t.contains("://") ? ["link": t] : ["query": t]
        struct R: Decodable { var ok: Bool?; var error: String? }
        let r = try decode(R.self, try await send(root.appending(path: "api/destination"), method: "POST", json: body))
        if r.ok == false { throw StackError.refused(r.error ?? "couldn't find that place") }
    }

    /// The place Apple Maps resolved on the phone: the server keeps it as its
    /// fallback objective while the phone's turn-by-turn route is fresh.
    func setDestination(lat: Double, lon: Double, name: String) async throws {
        _ = try await send(root.appending(path: "api/destination"), method: "POST",
                           json: ["lat": lat, "lon": lon, "name": name])
    }

    func clearDestination() async throws {
        _ = try await send(root.appending(path: "api/destination"), method: "POST", json: ["clear": true])
    }

    // MARK: clips (autoclip, behind basic auth)

    struct Clip: Decodable, Identifiable {
        var path: String
        var duration: Double?
        var decision: Decision?
        var ts: Double?
        var id: String { path }
        var fileName: String { (path as NSString).lastPathComponent }
    }
    struct Decision: Decodable {
        var title: String?
        var caption: String?
        var score: Double?
    }
    struct Pending: Decodable, Identifiable {
        var id: String
        var clip: Clip
        var platforms: [String]?
    }

    func pending() async throws -> [Pending] {
        struct R: Decodable { var pending: [Pending] }
        return try decode(R.self, try await send(clipsBase.appending(path: "api/autoclip/pending"), auth: true)).pending
    }

    func clips() async throws -> [Clip] {
        struct R: Decodable { var clips: [Clip] }
        return try decode(R.self, try await send(clipsBase.appending(path: "api/autoclip/clips"), auth: true)).clips
    }

    func approve(_ id: String) async throws {
        _ = try await send(clipsBase.appending(path: "api/autoclip/approve/\(id)"), method: "POST", auth: true)
    }

    func reject(_ id: String) async throws {
        _ = try await send(clipsBase.appending(path: "api/autoclip/reject/\(id)"), method: "POST", auth: true)
    }

    /// Rendered clips are public (Instagram fetches them), so AVPlayer needs no login.
    func videoURL(_ clip: Clip) -> URL { clipsBase.appending(path: "outbox/\(clip.fileName)") }
}
