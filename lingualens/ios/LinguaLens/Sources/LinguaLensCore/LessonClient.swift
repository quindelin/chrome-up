import Foundation

/// Where the server is and who we are. The key is the Cloud Run deployment's
/// LINGUALENS_KEY (server/access.py); it goes in the `X-LinguaLens-Key` header
/// on every request, including the websocket upgrade.
public struct ServerConfig: Equatable, Sendable {
    public var baseURL: URL
    public var key: String
    public var clientId: String

    public init(baseURL: URL, key: String, clientId: String = "me") {
        self.baseURL = baseURL
        self.key = key
        self.clientId = clientId
    }

    /// Accepts "host", "https://host", "https://host/" or a pasted phone link
    /// ("https://host/phone?key=…&client_id=me"), whose key and client_id are
    /// picked up when the other arguments are empty.
    public static func parse(_ raw: String, key: String = "", clientId: String = "") -> ServerConfig? {
        var text = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return nil }
        if !text.contains("://") { text = "https://" + text }
        guard let comps = URLComponents(string: text), let host = comps.host, !host.isEmpty else { return nil }
        let query = Dictionary((comps.queryItems ?? []).map { ($0.name, $0.value ?? "") }, uniquingKeysWith: { a, _ in a })
        var base = URLComponents()
        base.scheme = comps.scheme ?? "https"
        base.host = host
        base.port = comps.port
        guard let url = base.url else { return nil }
        let k = key.isEmpty ? (query["key"] ?? "") : key
        let id = clientId.isEmpty ? (query["client_id"] ?? "me") : clientId
        return ServerConfig(baseURL: url, key: k, clientId: id)
    }

    /// ws(s)://host/ws?client_id=…
    public var socketURL: URL {
        var c = URLComponents(url: baseURL, resolvingAgainstBaseURL: false)!
        c.scheme = (c.scheme == "http") ? "ws" : "wss"
        c.path = "/ws"
        c.queryItems = [URLQueryItem(name: "client_id", value: clientId)]
        return c.url!
    }

    public func authorize(_ request: inout URLRequest) {
        if !key.isEmpty { request.setValue(key, forHTTPHeaderField: "X-LinguaLens-Key") }
    }
}

public enum LessonClientError: Error, LocalizedError {
    case http(Int, String)
    public var errorDescription: String? {
        switch self {
        case let .http(code, body):
            return code == 401 ? "Server refused the key (401)." : "HTTP \(code): \(body.prefix(160))"
        }
    }
}

/// Thin client for the LinguaLens server. Every method maps 1:1 to a route in
/// server/main.py - the curriculum and the gate stay server-side. State comes
/// back over the websocket (StateSocket); these calls are intents.
public final class LessonClient: Sendable {
    public let config: ServerConfig
    private let session: URLSession

    public init(config: ServerConfig, session: URLSession = .shared) {
        self.config = config
        self.session = session
    }

    // MARK: reads

    public func state() async throws -> LessonState {
        try await get("/api/state", as: LessonState.self)
    }

    public func course(_ course: String = "") async throws -> CourseTree {
        try await get("/api/course", ["course": course], as: CourseTree.self)
    }

    public func library(_ course: String = "") async throws -> Library {
        try await get("/api/library", ["course": course], as: Library.self)
    }

    public func progress() async throws -> ProgressSummary {
        try await get("/api/progress", as: ProgressSummary.self)
    }

    public func words(query: String = "", limit: Int = 100, offset: Int = 0) async throws -> WordsPage {
        try await get("/api/progress/words",
                      ["q": query, "limit": String(limit), "offset": String(offset)],
                      as: WordsPage.self)
    }

    // MARK: intents

    /// Move past a step you do not speak. `at` is the step index we are
    /// looking at: the phone and the glasses share one session, so a second
    /// request for the same line is a no-op instead of a skip.
    public func next(at index: Int) async throws {
        try await form("/api/next", ["at": String(index)])
    }

    public func startLesson(_ id: Int) async throws {
        try await form("/api/lesson/start", ["lesson_id": String(id)])
    }

    public func startReview(limit: Int = 20) async throws {
        try await form("/api/review/start", ["limit": String(limit)])
    }

    public func startVocab(topic: String) async throws {
        try await form("/api/vocab/start", ["topic_id": topic])
    }

    public func startStory(_ id: String) async throws {
        try await form("/api/library/start", ["story_id": id])
    }

    public func selectCourse(_ id: String) async throws {
        try await form("/api/course/select", ["course": id])
    }

    /// Uploads one 16 kHz WAV take; the new state arrives on the websocket.
    public func attempt(wav: Data, recognized: String = "") async throws -> AttemptResult {
        var fields = ["client_id": config.clientId, "encoding": "wav"]
        if !recognized.isEmpty { fields["recognized"] = recognized }
        let (body, boundary) = Self.multipart(fields: fields, fileField: "file",
                                              filename: "attempt.wav", mime: "audio/wav", file: wav)
        var request = URLRequest(url: url("/api/attempt"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        config.authorize(&request)
        let (data, response) = try await session.upload(for: request, from: body)
        try Self.check(response, data)
        return try JSONDecoder().decode(AttemptResult.self, from: data)
    }

    // MARK: plumbing

    public static func multipart(fields: [String: String], fileField: String, filename: String,
                                 mime: String, file: Data,
                                 boundary: String = "LinguaLens-\(UUID().uuidString)") -> (Data, String) {
        var body = Data()
        func add(_ s: String) { body.append(Data(s.utf8)) }
        for (name, value) in fields.sorted(by: { $0.key < $1.key }) {
            add("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(name)\"\r\n\r\n\(value)\r\n")
        }
        add("--\(boundary)\r\nContent-Disposition: form-data; name=\"\(fileField)\"; filename=\"\(filename)\"\r\n")
        add("Content-Type: \(mime)\r\n\r\n")
        body.append(file)
        add("\r\n--\(boundary)--\r\n")
        return (body, boundary)
    }

    private func url(_ path: String, _ query: [String: String] = [:]) -> URL {
        var c = URLComponents(url: config.baseURL, resolvingAgainstBaseURL: false)!
        c.path = path
        var items = [URLQueryItem(name: "client_id", value: config.clientId)]
        for (k, v) in query.sorted(by: { $0.key < $1.key }) where !v.isEmpty {
            items.append(URLQueryItem(name: k, value: v))
        }
        c.queryItems = items
        return c.url!
    }

    private func get<T: Decodable>(_ path: String, _ query: [String: String] = [:], as: T.Type) async throws -> T {
        var request = URLRequest(url: url(path, query))
        config.authorize(&request)
        let (data, response) = try await session.data(for: request)
        try Self.check(response, data)
        return try JSONDecoder().decode(T.self, from: data)
    }

    private func form(_ path: String, _ fields: [String: String]) async throws {
        var request = URLRequest(url: url(path))
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        config.authorize(&request)
        var all = fields
        all["client_id"] = config.clientId
        request.httpBody = Data(Self.formEncode(all).utf8)
        let (data, response) = try await session.data(for: request)
        try Self.check(response, data)
    }

    public static func formEncode(_ fields: [String: String]) -> String {
        var allowed = CharacterSet.alphanumerics
        allowed.insert(charactersIn: "-._~")
        return fields.sorted(by: { $0.key < $1.key }).map { k, v in
            "\(k)=\(v.addingPercentEncoding(withAllowedCharacters: allowed) ?? v)"
        }.joined(separator: "&")
    }

    private static func check(_ response: URLResponse, _ data: Data) throws {
        guard let http = response as? HTTPURLResponse else { return }
        guard (200..<300).contains(http.statusCode) else {
            throw LessonClientError.http(http.statusCode, String(decoding: data, as: UTF8.self))
        }
    }
}
