import SwiftUI

/// LiveVision: is the IRL stream live, and is the VPS healthy? Polls the VPS's
/// autoclip API (GET /autoclip/api/autoclip/stack) while the app is open, and
/// streams the Meta glasses' camera to the VPS (GlassesStreamer).
@main
struct LiveVisionApp: App {
    @State private var store = StackStore()
    @State private var glasses = GlassesStreamer()
    @State private var sensors = SensorBridge()
    @State private var prompter = Teleprompter()
    @State private var navigator = RouteNavigator()
    @State private var bodyTracker = BodyTracker()
    @State private var watch = WatchLink()
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            // the HUD's web control panel, /phone and approval page live here now
            TabView {
                DashboardView().tabItem { Label("Status", systemImage: "dot.radiowaves.left.and.right") }
                ControlView().tabItem { Label("Control", systemImage: "slider.horizontal.3") }
                ClipsView().tabItem { Label("Clips", systemImage: "film.stack") }
                TeleprompterView().tabItem { Label("Prompter", systemImage: "text.alignleft") }
            }
            .environment(store)
            .environment(glasses)
            .environment(sensors)
            .environment(prompter)
            .environment(navigator)
            .environment(bodyTracker)
            .environment(watch)
            .task {
                glasses.configure()
                navigator.start(sensors: sensors, glasses: glasses)
                bodyTracker.start(glasses: glasses, sensors: sensors, watch: watch)
                bodyTracker.onHead = { [navigator] q in navigator.headTurned(q) }
            }
            // the lens (prompter + directions, LensRouter) rides on the glasses
            // session: re-attach after reconnects
            .onChange(of: glasses.link) {
                prompter.sessionChanged(glasses)
                bodyTracker.sessionChanged(glasses)        // DAT Motion rides the same session
            }
            // livevision://navigate?to=<maps link or place> (Shortcuts, links);
            // TikTok's Share Kit answer (ClipShare); anything else is the
            // Meta AI app's registration callback
            .onOpenURL { url in
                if ClipShare.handle(url: url) { return }
                if url.host() == "navigate",
                   let to = URLComponents(url: url, resolvingAgainstBaseURL: false)?
                       .queryItems?.first(where: { $0.name == "to" })?.value {
                    Task { try? await navigator.navigate(to: to) }
                } else {
                    glasses.handle(url: url)
                }
            }
            // TikTok's callback as a universal link, once Associated Domains is set up
            .onContinueUserActivity(NSUserActivityTypeBrowsingWeb) { activity in
                if let url = activity.webpageURL { _ = ClipShare.handle(url: url) }
            }
        }
        .onChange(of: phase, initial: true) { _, p in
            // no background polling: iOS would suspend it anyway. The glasses
            // stream keeps going (audio background mode, see BackgroundAudio).
            // Phone sensors and body tracking keep running in your pocket while
            // the glasses stream (that's when the avatar needs them); otherwise
            // they stop with the app as before.
            if p == .active { store.start(); sensors.start(); navigator.checkInbox() }
            else { store.stop(); if !glasses.isStreaming { sensors.stop() } }
        }
    }
}
