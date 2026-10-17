import SwiftUI
import AVFoundation
import UIKit
import WebKit
import LinguaLensCore

// MARK: - App

/// LinguaLens on Ray-Ban Display.
///
/// The lesson UI is the 600x600 web app served by the LinguaLens server; this
/// target is the wrapper a web app cannot be - microphone, haptics and the
/// Device Access Toolkit. Input mapping matches the Android wrapper:
///   swipe up / down -> ArrowUp / ArrowDown, tap -> Enter, swipe back -> Escape.
@main
struct LinguaLensApp: App {
    @StateObject private var model = GlassesViewModel()

    var body: some Scene {
        WindowGroup {
            LessonView(model: model)
                .task { await model.connect() }
        }
    }
}

// MARK: - Glasses bridge (DAT)

@MainActor
final class GlassesViewModel: NSObject, ObservableObject {
    enum Status: String { case disconnected, connecting, connected, unsupported }

    @Published var status: Status = .disconnected
    @Published var deviceName: String?
    @Published var lastMessage = ""

    let client: LessonClient
    let capture = AudioCapture()
    private let feedback = UINotificationFeedbackGenerator()
    private let impact = UIImpactFeedbackGenerator(style: .medium)
    private let selection = UISelectionFeedbackGenerator()

    override init() {
        // point this at your HTTPS host before shipping to the glasses
        let url = URL(string: UserDefaults.standard.string(forKey: "server_url") ?? "http://10.0.0.10:8899")!
        self.client = LessonClient(baseURL: url, clientId: "glasses")
        super.init()
    }

    func connect() async {
        status = .connecting
        // DAT: mwdat-core
        //   Wearables.shared.initialize()
        //   for await devices in Wearables.shared.devices {
        //       let glasses = devices.first { $0.isDisplayCapable }
        //       deviceName = glasses?.name
        //       status = glasses == nil ? .disconnected : .connected
        //   }
        // Without glasses the lesson still runs - you speak into the phone.
        status = .disconnected
        try? capture.configureSession(preferGlassesMic: true)
    }

    /// Mirror the current line onto MWDATDisplay (the web app already shows it).
    func showLine(hanzi: String, pinyin: String) {
        // DAT: mwdat-display
        //   MWDATDisplay.shared.show(.text(primary: hanzi, secondary: pinyin))
    }

    func haptic(_ kind: String) {
        switch kind {
        case "pass": feedback.notificationOccurred(.success)
        case "fail": feedback.notificationOccurred(.error)
        case "select": impact.impactOccurred(intensity: 0.9)
        case "back": impact.impactOccurred(intensity: 0.4)
        default: selection.selectionChanged()
        }
    }

    func startTalking() {
        guard !capture.isRecording else { return }
        try? capture.start()
        haptic("select")
    }

    func stopTalking() {
        guard capture.isRecording, let wav = capture.stop() else { return }
        Task {
            let result = try? await client.submit(wav: wav)
            haptic(result?.passed == true ? "pass" : "fail")
            lastMessage = result?.reasons?.first ?? ""
        }
    }
}

// MARK: - UI (WebView + push to talk)

struct LessonView: View {
    @ObservedObject var model: GlassesViewModel
    @State private var talking = false

    var body: some View {
        ZStack(alignment: .bottomTrailing) {
            WebLessonView(model: model)
                .ignoresSafeArea()

            VStack(spacing: 12) {
                Text(model.status.rawValue + (model.deviceName.map { " · \($0)" } ?? ""))
                    .font(.caption)
                    .padding(6)
                    .background(.black.opacity(0.6))
                    .foregroundStyle(.white)
                    .clipShape(Capsule())

                Circle()
                    .fill(talking ? .red : .white)
                    .frame(width: 88, height: 88)
                    .overlay(Image(systemName: "mic.fill").font(.title).foregroundStyle(.black))
                    .onLongPressGesture(minimumDuration: 0.01, pressing: { pressing in
                        if pressing { talking = true; model.startTalking() }
                        else { talking = false; model.stopTalking() }
                    }, perform: {})
            }
            .padding(24)
        }
        .preferredColorScheme(.dark)
    }
}

struct WebLessonView: UIViewRepresentable {
    let model: GlassesViewModel
    private let url: URL = {
        let base = UserDefaults.standard.string(forKey: "server_url") ?? "http://10.0.0.10:8899"
        return URL(string: "\(base)/?client_id=glasses")!
    }()

    func makeUIView(context: Context) -> WKWebView {
        let controller = WKUserContentController()
        // window.webkit.messageHandlers.haptics.postMessage("select")
        controller.add(context.coordinator, name: "haptics")
        let config = WKWebViewConfiguration()
        config.userContentController = controller
        config.mediaTypesRequiringUserActionForPlayback = []

        let web = WKWebView(frame: .zero, configuration: config)
        web.navigationDelegate = context.coordinator
        web.load(URLRequest(url: url))
        return web
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(model: model) }

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        let model: GlassesViewModel
        init(model: GlassesViewModel) { self.model = model }

        func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
            if message.name == "haptics", let kind = message.body as? String {
                model.haptic(kind)
            }
        }
    }
}
