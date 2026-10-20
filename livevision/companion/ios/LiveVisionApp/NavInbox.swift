import Foundation

/// Apple Maps' Share → LiveVision (the LiveVisionShare extension) leaves the
/// place here: one entry in the App Group's UserDefaults, plus a Darwin
/// notification so a running LiveVision (it stays alive in the background
/// while the glasses stream) starts the route right away. Otherwise
/// RouteNavigator picks it up the next time the app opens.
///
/// The group comes from LIVEVISION_APP_GROUP (Config/Base.xcconfig), through
/// Info.plist, so it follows the entitlements of both targets.
@MainActor
enum NavInbox {
    static let notification = "com.chromeup.livevision.nav-inbox"
    static let key = "nav.inbox"
    /// A share older than this was forgotten about: don't navigate to it.
    static let maxAge: TimeInterval = 30 * 60

    static var defaults: UserDefaults? {
        guard let group = Bundle.main.object(forInfoDictionaryKey: "LiveVisionAppGroup") as? String,
              !group.isEmpty else { return nil }
        return UserDefaults(suiteName: group)
    }

    /// Takes the waiting place, if any (link or text, and the transport picked in the sheet).
    static func take() -> (text: String, transport: String?)? {
        guard let d = defaults, let entry = d.dictionary(forKey: key) else { return nil }
        d.removeObject(forKey: key)
        guard let text = entry["text"] as? String, !text.isEmpty,
              let ts = entry["ts"] as? Double,
              Date().timeIntervalSince1970 - ts < maxAge else { return nil }
        return (text, entry["transport"] as? String)
    }

    private static var onPost: (@MainActor () -> Void)?

    static func listen(_ handler: @escaping @MainActor () -> Void) {
        let first = onPost == nil
        onPost = handler
        guard first else { return }
        CFNotificationCenterAddObserver(
            CFNotificationCenterGetDarwinNotifyCenter(), nil,
            { _, _, _, _, _ in Task { @MainActor in NavInbox.onPost?() } },
            notification as CFString, nil, .deliverImmediately)
    }
}
