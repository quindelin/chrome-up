import Observation
import SwiftUI
import UIKit
import UniformTypeIdentifiers

/// Share → LiveVision, from Apple Maps (or Google Maps, Safari, Messages):
/// a small sheet naming the place, Walking / Driving, and "Navigate". The
/// place goes into the App Group for LiveVision's RouteNavigator (NavInbox in
/// the app) and a Darwin notification tells a running LiveVision to start
/// right away; it stays running in the background while the glasses stream.
/// If it isn't running, the route starts the next time it opens.
///
/// Extensions can't open their host app, so this one doesn't try.
final class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        let model = ShareModel(context: extensionContext)
        let host = UIHostingController(rootView: ShareSheet(model: model))
        addChild(host)
        host.view.frame = view.bounds
        host.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(host.view)
        host.didMove(toParent: self)
        Task { await model.load() }
    }
}

@MainActor
@Observable
final class ShareModel {
    enum Phase: Equatable { case loading, ready, sent, nothing }

    private(set) var phase: Phase = .loading
    private(set) var title = "This place"
    private(set) var detail: String?
    var transport: String

    @ObservationIgnored private let context: NSExtensionContext?
    @ObservationIgnored private var payload: String?

    private static let notification = "com.chromeup.livevision.nav-inbox"
    private static var group: UserDefaults? {
        guard let id = Bundle.main.object(forInfoDictionaryKey: "LiveVisionAppGroup") as? String,
              !id.isEmpty else { return nil }
        return UserDefaults(suiteName: id)
    }

    init(context: NSExtensionContext?) {
        self.context = context
        transport = Self.group?.string(forKey: "nav.transport") ?? "walking"
    }

    /// The first link among the shared items, else their text.
    func load() async {
        var link: URL?
        var text: String?
        for item in context?.inputItems as? [NSExtensionItem] ?? [] {
            if text == nil, let t = item.attributedContentText?.string, !t.isEmpty { text = t }
            for provider in item.attachments ?? [] {
                if link == nil, provider.hasItemConformingToTypeIdentifier(UTType.url.identifier),
                   let url = try? await provider.loadItem(forTypeIdentifier: UTType.url.identifier) as? URL,
                   url.scheme?.hasPrefix("http") == true {
                    link = url
                }
                if text == nil, provider.hasItemConformingToTypeIdentifier(UTType.plainText.identifier),
                   let t = try? await provider.loadItem(forTypeIdentifier: UTType.plainText.identifier) as? String {
                    text = t
                }
            }
        }
        if link == nil, let text { link = Self.firstLink(in: text) }

        if let link {
            payload = link.absoluteString
            let items = URLComponents(url: link, resolvingAgainstBaseURL: false)?.queryItems ?? []
            func value(_ k: String) -> String? { items.first { $0.name == k }?.value }
            title = value("name") ?? value("q") ?? text?.components(separatedBy: "\n").first ?? "This place"
            detail = value("address") ?? link.host()
        } else if let text, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            payload = text.trimmingCharacters(in: .whitespacesAndNewlines)
            title = payload ?? title
        }
        phase = payload == nil ? .nothing : .ready
    }

    func send() {
        guard let payload, let group = Self.group else { phase = .nothing; return }
        group.set(["text": payload, "transport": transport, "ts": Date().timeIntervalSince1970],
                  forKey: "nav.inbox")
        group.set(transport, forKey: "nav.transport")
        CFNotificationCenterPostNotification(CFNotificationCenterGetDarwinNotifyCenter(),
                                             CFNotificationName(Self.notification as CFString), nil, nil, true)
        phase = .sent
        Task {
            try? await Task.sleep(for: .seconds(1.6))
            context?.completeRequest(returningItems: nil)
        }
    }

    func cancel() {
        context?.cancelRequest(withError: NSError(domain: NSCocoaErrorDomain, code: NSUserCancelledError))
    }

    private static func firstLink(in text: String) -> URL? {
        let detector = try? NSDataDetector(types: NSTextCheckingResult.CheckingType.link.rawValue)
        return detector?.firstMatch(in: text, range: NSRange(text.startIndex..., in: text))?.url
    }
}

struct ShareSheet: View {
    @Bindable var model: ShareModel

    var body: some View {
        NavigationStack {
            VStack(spacing: 18) {
                switch model.phase {
                case .loading:
                    ProgressView()
                case .nothing:
                    ContentUnavailableView("Nothing to navigate to",
                                           systemImage: "mappin.slash",
                                           description: Text("Share a place or a maps link."))
                case .ready, .sent:
                    VStack(spacing: 4) {
                        Image(systemName: "location.north.circle.fill")
                            .font(.system(size: 44)).foregroundStyle(.tint)
                        Text(model.title).font(.title3.weight(.semibold)).multilineTextAlignment(.center)
                        if let d = model.detail {
                            Text(d).font(.footnote).foregroundStyle(.secondary).multilineTextAlignment(.center)
                        }
                    }
                    Picker("Directions", selection: $model.transport) {
                        Text("Walking").tag("walking")
                        Text("Driving").tag("driving")
                    }
                    .pickerStyle(.segmented)
                    if model.phase == .sent {
                        Label("Sent to LiveVision", systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                        Text("It starts on the HUD now if LiveVision is streaming, otherwise when you open LiveVision.")
                            .font(.footnote).foregroundStyle(.secondary).multilineTextAlignment(.center)
                    } else {
                        Button { model.send() } label: {
                            Text("Navigate on the HUD").frame(maxWidth: .infinity, minHeight: 44)
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                Spacer()
            }
            .padding(24)
            .navigationTitle("LiveVision")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { model.cancel() }
                }
            }
        }
    }
}
