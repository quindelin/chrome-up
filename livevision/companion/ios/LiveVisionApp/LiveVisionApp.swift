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
            .task { glasses.configure() }
            // the lens rides on the glasses session: re-attach after reconnects
            .onChange(of: glasses.link) { prompter.sessionChanged(glasses) }
            // the Meta AI app's registration callback
            .onOpenURL { glasses.handle(url: $0) }
        }
        .onChange(of: phase, initial: true) { _, p in
            // no background polling: iOS would suspend it anyway. The glasses
            // stream keeps going (audio background mode, see BackgroundAudio).
            if p == .active { store.start(); sensors.start() } else { store.stop(); sensors.stop() }
        }
    }
}
