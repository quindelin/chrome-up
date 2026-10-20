import SwiftUI

/// LiveVision: is the IRL stream live, and is the VPS healthy? Polls the VPS's
/// autoclip API (GET /autoclip/api/autoclip/stack) while the app is open.
@main
struct LiveVisionApp: App {
    @State private var store = StackStore()
    @Environment(\.scenePhase) private var phase

    var body: some Scene {
        WindowGroup {
            DashboardView()
                .environment(store)
        }
        .onChange(of: phase, initial: true) { _, p in
            // no background polling: iOS would suspend it anyway
            if p == .active { store.start() } else { store.stop() }
        }
    }
}
