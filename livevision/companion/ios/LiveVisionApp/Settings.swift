import Foundation
import Security

/// VPS host, the approval-page login (Caddy basic auth on /autoclip/*) and
/// the glasses ingest (MediaMTX live/<stream key>).
///
/// Defaults come from the build (Config/Secrets.xcconfig -> Info.plist, never
/// committed; `deploy/obs-vps/gcp.sh companion` writes it); anything typed on
/// the Settings screen wins. The password, stream key and SRT passphrase live
/// in the Keychain, the rest in UserDefaults.
enum Settings {
    private static let defaults = UserDefaults.standard

    private static func info(_ key: String) -> String {
        let v = (Bundle.main.object(forInfoDictionaryKey: key) as? String) ?? ""
        return v.hasPrefix("$(") ? "" : v.trimmingCharacters(in: .whitespaces)
    }

    /// Host only, e.g. 136-80-148-90.sslip.io (a pasted https:// URL is tolerated).
    static var host: String {
        get { defaults.string(forKey: "host") ?? info("LiveVisionHost") }
        set { defaults.set(newValue, forKey: "host") }
    }

    static var user: String {
        get {
            let v = defaults.string(forKey: "user") ?? info("LiveVisionUser")
            return v.isEmpty ? "clips" : v
        }
        set { defaults.set(newValue, forKey: "user") }
    }

    static var password: String {
        get { Keychain.read("livevision.password") ?? info("LiveVisionPassword") }
        set { Keychain.write("livevision.password", newValue) }
    }

    /// VM start/stop function (gcp.sh control-deploy): host only, and its token.
    static var controlHost: String {
        get { defaults.string(forKey: "control_host") ?? info("LiveVisionControlHost") }
        set { defaults.set(newValue, forKey: "control_host") }
    }

    static var controlToken: String {
        get { Keychain.read("livevision.controlToken") ?? info("LiveVisionControlToken") }
        set { Keychain.write("livevision.controlToken", newValue) }
    }

    /// STREAM_KEY in the VM's .env: the glasses publish to live/<key>.
    static var streamKey: String {
        get { Keychain.read("livevision.streamKey") ?? info("LiveVisionStreamKey") }
        set { Keychain.write("livevision.streamKey", newValue) }
    }

    /// SRT_PASSPHRASE in the VM's .env (MediaMTX srtPublishPassphrase).
    static var srtPassphrase: String {
        get { Keychain.read("livevision.srtPassphrase") ?? info("LiveVisionSRTPassphrase") }
        set { Keychain.write("livevision.srtPassphrase", newValue) }
    }

    enum Transport: String, CaseIterable, Identifiable {
        case srt, rtmp
        var id: String { rawValue }
        var label: String { self == .srt ? "SRT (experimental)" : "RTMP" }
    }

    /// RTMP by default. SRT would cope better with cellular loss, but MediaMTX
    /// drops HaishinKit 2.2.5's SRT publish after a few seconds ("astits: max
    /// buffer size exceeded" on the VM) while the same encoder over RTMP is fine.
    static var transport: Transport {
        get { defaults.string(forKey: "transport").flatMap(Transport.init) ?? .rtmp }
        set { defaults.set(newValue.rawValue, forKey: "transport") }
    }

    /// DAT's Mock Device Kit instead of real glasses: a simulated Ray-Ban
    /// Display whose camera plays a bundled test pattern. Works in the Simulator.
    static var mockGlasses: Bool {
        get { defaults.bool(forKey: "mockGlasses") }
        set { defaults.set(newValue, forKey: "mockGlasses") }
    }

    /// Host only, scheme and slashes stripped.
    static var bareHost: String? {
        var h = host.trimmingCharacters(in: .whitespacesAndNewlines)
        for prefix in ["https://", "http://"] where h.hasPrefix(prefix) { h.removeFirst(prefix.count) }
        h = h.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        return h.isEmpty ? nil : h
    }

    /// https://<host>/autoclip, or nil until a host is set.
    static var baseURL: URL? {
        bareHost.flatMap { URL(string: "https://\($0)/autoclip") }
    }

    /// https://<host>: the HUD server (POST /api/glasses, no auth).
    static var hudURL: URL? {
        bareHost.flatMap { URL(string: "https://\($0)") }
    }

    /// The VM's IPv4 for SRT/RTMP. sslip.io names carry it (34-57-203-238.sslip.io),
    /// which skips a DNS lookup libsrt would otherwise do with gethostbyname.
    static var ingestHost: String? {
        guard let h = bareHost else { return nil }
        let first = h.split(separator: ".").first.map(String.init) ?? h
        let dashed = first.split(separator: "-")
        if h.hasSuffix(".sslip.io"), dashed.count == 4, dashed.allSatisfy({ UInt8($0) != nil }) {
            return dashed.joined(separator: ".")
        }
        return h
    }
}

enum Keychain {
    private static func query(_ account: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: "com.chromeup.livevision",
         kSecAttrAccount as String: account]
    }

    static func read(_ account: String) -> String? {
        var q = query(account)
        q[kSecReturnData as String] = true
        q[kSecMatchLimit as String] = kSecMatchLimitOne
        var out: AnyObject?
        guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess, let d = out as? Data else { return nil }
        return String(data: d, encoding: .utf8)
    }

    static func write(_ account: String, _ value: String) {
        SecItemDelete(query(account) as CFDictionary)
        guard !value.isEmpty else { return }
        var q = query(account)
        q[kSecValueData as String] = Data(value.utf8)
        q[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        SecItemAdd(q as CFDictionary, nil)
    }
}
