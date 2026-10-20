import Foundation
import Security

/// VPS host and the approval-page login (Caddy basic auth on /autoclip/*).
///
/// Defaults come from the build (Config/Secrets.xcconfig -> Info.plist, never
/// committed; `deploy/obs-vps/gcp.sh companion` writes it); anything typed on
/// the Settings screen wins. The password lives in the Keychain, the rest in
/// UserDefaults.
enum Settings {
    private static let defaults = UserDefaults.standard

    private static func info(_ key: String) -> String {
        let v = (Bundle.main.object(forInfoDictionaryKey: key) as? String) ?? ""
        return v.hasPrefix("$(") ? "" : v.trimmingCharacters(in: .whitespaces)
    }

    /// Host only, e.g. 136-80-148-90.sslip.io (a pasted https:// URL is tolerated).
    static var host: String {
        get { defaults.string(forKey: "host") ?? info("OnAirHost") }
        set { defaults.set(newValue, forKey: "host") }
    }

    static var user: String {
        get {
            let v = defaults.string(forKey: "user") ?? info("OnAirUser")
            return v.isEmpty ? "clips" : v
        }
        set { defaults.set(newValue, forKey: "user") }
    }

    static var password: String {
        get { Keychain.read("onair.password") ?? info("OnAirPassword") }
        set { Keychain.write("onair.password", newValue) }
    }

    /// https://<host>/autoclip, or nil until a host is set.
    static var baseURL: URL? {
        var h = host.trimmingCharacters(in: .whitespacesAndNewlines)
        for prefix in ["https://", "http://"] where h.hasPrefix(prefix) { h.removeFirst(prefix.count) }
        h = h.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard !h.isEmpty else { return nil }
        return URL(string: "https://\(h)/autoclip")
    }
}

enum Keychain {
    private static func query(_ account: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: "com.chromeup.onair",
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
