import Foundation

/// Thin client for the LinguaLens server. Every method maps 1:1 to a route in
/// server/main.py - the curriculum and the gate stay server-side.
public struct AttemptResult: Decodable {
    public let passed: Bool
    public let reasons: [String]?
    public let score: Score?
    public struct Score: Decodable {
        public let pron: Double?
        public let tone: Double?
        public let provider: String?
    }
}

public final class LessonClient {
    public let baseURL: URL
    public let clientId: String
    private let session: URLSession

    public init(baseURL: URL, clientId: String = "glasses") {
        self.baseURL = baseURL
        self.clientId = clientId
        self.session = URLSession(configuration: .default)
    }

    public func state() async throws -> [String: Any] { try await get("/api/state") }

    public func course() async throws -> [String: Any] { try await get("/api/course") }

    @discardableResult
    public func next() async throws -> [String: Any] { try await form("/api/next", [:]) }

    @discardableResult
    public func startLesson(_ id: Int) async throws -> [String: Any] {
        try await form("/api/lesson/start", ["lesson_id": String(id)])
    }

    @discardableResult
    public func review(limit: Int = 20) async throws -> [String: Any] {
        try await form("/api/review/start", ["limit": String(limit)])
    }

    @discardableResult
    public func think(_ text: String) async throws -> [String: Any] {
        try await form("/api/think", ["text": text])
    }

    /// Uploads one WAV attempt; returns the grade and whether you may advance.
    public func submit(wav: Data) async throws -> AttemptResult {
        let boundary = "LinguaLens-\(UUID().uuidString)"
        var body = Data()
        func field(_ name: String, _ value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }
        field("client_id", clientId)
        field("encoding", "wav")
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"attempt.wav\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: audio/wav\r\n\r\n".data(using: .utf8)!)
        body.append(wav)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        var request = URLRequest(url: baseURL.appendingPathComponent("/api/attempt"))
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        let (data, _) = try await session.upload(for: request, from: body)
        return try JSONDecoder().decode(AttemptResult.self, from: data)
    }

    private func get(_ path: String) async throws -> [String: Any] {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "client_id", value: clientId)]
        let (data, _) = try await session.data(from: components.url!)
        return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
    }

    @discardableResult
    private func form(_ path: String, _ fields: [String: String]) async throws -> [String: Any] {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        var parts = ["client_id=\(clientId.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? clientId)"]
        for (k, v) in fields {
            let enc = v.addingPercentEncoding(withAllowedCharacters: .alphanumerics) ?? v
            parts.append("\(k)=\(enc)")
        }
        request.httpBody = parts.joined(separator: "&").data(using: .utf8)
        let (data, _) = try await session.data(for: request)
        return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
    }
}
