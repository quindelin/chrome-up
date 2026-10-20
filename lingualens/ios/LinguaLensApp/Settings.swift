import Foundation
import LinguaLensCore
import Security

/// Server URL, access key and client id.
///
/// Defaults come from the build (Config/Secrets.xcconfig -> Info.plist, never
/// committed); anything typed on the Settings screen wins. The key lives in
/// the Keychain, the rest in UserDefaults.
enum Settings {
    private static let defaults = UserDefaults.standard

    private static func info(_ key: String) -> String {
        let v = (Bundle.main.object(forInfoDictionaryKey: key) as? String) ?? ""
        return v.hasPrefix("$(") ? "" : v.trimmingCharacters(in: .whitespaces)
    }

    static var server: String {
        get { defaults.string(forKey: "server") ?? info("LLServerHost") }
        set { defaults.set(newValue, forKey: "server") }
    }

    static var clientId: String {
        get {
            let v = defaults.string(forKey: "client_id") ?? info("LLClientID")
            return v.isEmpty ? "me" : v
        }
        set { defaults.set(newValue, forKey: "client_id") }
    }

    static var key: String {
        get { Keychain.read("lingualens.key") ?? info("LLServerKey") }
        set { Keychain.write("lingualens.key", newValue) }
    }

    static var handsFree: Bool {
        get { defaults.object(forKey: "hands_free") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "hands_free") }
    }

    /// Draw each step on the glasses display. On by default: the glasses
    /// are the main screen for a lesson, not the phone.
    static var glassesDisplay: Bool {
        get { defaults.object(forKey: "glasses_display") as? Bool ?? true }
        set { defaults.set(newValue, forKey: "glasses_display") }
    }

    static var config: ServerConfig? {
        ServerConfig.parse(server, key: key, clientId: clientId)
    }
}

enum Keychain {
    private static func query(_ account: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: "com.lingualens.app",
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
