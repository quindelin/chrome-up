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

    /// Posting answers in a second or two, but the VPS may be busy cutting a clip.
    private static let slowSession: URLSession = {
        let c = URLSessionConfiguration.ephemeral
        c.timeoutIntervalForRequest = 30
        return URLSession(configuration: c)
    }()

    private func send(_ url: URL, method: String = "GET", json: [String: Any]? = nil, auth: Bool = false,
                      slow: Bool = false) async throws -> Data {
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
        do { (data, resp) = try await (slow ? Self.slowSession : Self.session).data(for: r) } catch {
            throw StackError.unreachable(error.localizedDescription)
        }
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        if code == 401 { throw StackError.unauthorized }
        // autoclip says why it refused (FastAPI {"detail": "..."})
        if (400..<500).contains(code),
           let why = (try? JSONSerialization.jsonObject(with: data) as? [String: Any])?["detail"] as? String {
            throw StackError.refused(why)
        }
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

    // MARK: clips (autoclip, behind basic auth; docs/CLIP_POSTING.md)

    struct Clip: Decodable, Identifiable {
        var path: String
        var duration: Double?
        var decision: Decision?
        var ts: Double?
        var thumb: String?
        var id: String { path }
        var fileName: String { (path as NSString).lastPathComponent }
    }
    struct Decision: Decodable {
        var title: String?
        var caption: String?
        var hashtags: [String]?
        var score: Double?
    }

    /// One queued clip: what the agent wrote, your edits, and each platform's post.
    struct Pending: Decodable, Identifiable {
        var id: String
        var clip: Clip
        var platforms: [String]?
        var edits: Edits?
        var posts: [String: Post]?
        var status: String?
        var videoUrl: String?
        var thumbUrl: String?
        var created: Double?

        var title: String { edits?.title ?? clip.decision?.title ?? "" }
        var caption: String { edits?.caption ?? clip.decision?.caption ?? "" }
        var hashtags: [String] { edits?.hashtags ?? clip.decision?.hashtags ?? [] }
        var isPosting: Bool { status == "posting" }
        func post(_ platform: String) -> Post? { posts?[platform] }
    }
    struct Edits: Decodable {
        var title: String?
        var caption: String?
        var hashtags: [String]?
        var youtubePrivacy: String?
    }
    /// queued / uploading / posted / dry_run / failed; device: shared / cancelled
    struct Post: Decodable {
        var state: String
        var url: String?
        var message: String?
        var dryRun: Bool?
        var at: Double?

        var isBusy: Bool { state == "queued" || state == "uploading" }
        var isDone: Bool { ["posted", "dry_run", "shared"].contains(state) }
    }

    struct Platforms: Decodable {
        var mode: String
        var platforms: [Platform]
        var youtubePrivacy: String?
        var youtubePrivacyOptions: [String]?
        var isLive: Bool { mode == "live" }
    }
    struct Platform: Decodable, Identifiable {
        var name: String
        var path: String            // "server" (autoclip posts) or "device" (the phone shares)
        var configured: Bool
        var reason: String?
        var limits: Limits?
        var id: String { name }
        var onDevice: Bool { path == "device" }
    }
    struct Limits: Decodable {
        var title: Int?
        var caption: Int?
        var maxSeconds: Int?
    }

    private func clipsURL(_ path: String) -> URL { clipsBase.appending(path: "api/autoclip/" + path) }

    func pending() async throws -> [Pending] {
        struct R: Decodable { var pending: [Pending] }
        return try decode(R.self, try await send(clipsURL("pending"), auth: true)).pending
    }

    func posted() async throws -> [Pending] {
        struct R: Decodable { var posted: [Pending] }
        return try decode(R.self, try await send(clipsURL("posted"), auth: true)).posted
    }

    func clips() async throws -> [Clip] {
        struct R: Decodable { var clips: [Clip] }
        return try decode(R.self, try await send(clipsURL("clips"), auth: true)).clips
    }

    func platforms() async throws -> Platforms {
        try decode(Platforms.self, try await send(clipsURL("platforms"), auth: true))
    }

    func clip(_ id: String) async throws -> Pending {
        try decode(Pending.self, try await send(clipsURL("clips/\(id)"), auth: true))
    }

    private func editBody(title: String, caption: String, hashtags: [String], youtubePrivacy: String?) -> [String: Any] {
        var body: [String: Any] = ["title": title, "caption": caption, "hashtags": hashtags]
        if let youtubePrivacy { body["youtube_privacy"] = youtubePrivacy }
        return body
    }

    @discardableResult
    func edit(_ id: String, title: String, caption: String, hashtags: [String], youtubePrivacy: String?) async throws -> Pending {
        try decode(Pending.self, try await send(clipsURL("clips/\(id)"), method: "PATCH",
                                                 json: editBody(title: title, caption: caption, hashtags: hashtags,
                                                                youtubePrivacy: youtubePrivacy),
                                                 auth: true, slow: true))
    }

    /// Starts YouTube / Instagram on the VPS and answers right away (202):
    /// poll clip(id) for each platform's result.
    @discardableResult
    func post(_ id: String, platforms: [String], title: String, caption: String, hashtags: [String],
              youtubePrivacy: String?) async throws -> Pending {
        var body = editBody(title: title, caption: caption, hashtags: hashtags, youtubePrivacy: youtubePrivacy)
        body["platforms"] = platforms
        return try decode(Pending.self, try await send(clipsURL("clips/\(id)/post"), method: "POST",
                                                        json: body, auth: true, slow: true))
    }

    /// TikTok / X went through the phone: tell the queue how it went.
    @discardableResult
    func shared(_ id: String, platform: String, state: String, message: String = "") async throws -> Pending {
        try decode(Pending.self, try await send(clipsURL("clips/\(id)/shared"), method: "POST",
                                                 json: ["platform": platform, "state": state, "message": message],
                                                 auth: true))
    }

    func reject(_ id: String) async throws {
        _ = try await send(clipsURL("clips/\(id)/reject"), method: "POST", auth: true)
    }

    /// Rendered clips are public (Instagram fetches them), so AVPlayer needs no login.
    func videoURL(_ clip: Clip) -> URL { clipsBase.appending(path: "outbox/\(clip.fileName)") }
    func mediaURL(_ relative: String) -> URL { clipsBase.appending(path: relative) }
}
