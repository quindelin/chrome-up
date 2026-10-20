import SwiftUI

/// LinguaLens for iPhone: a headless lesson player for the LinguaLens server.
///
/// The server (Cloud Run) owns the curriculum, the gate and the session; the
/// Ray-Ban Display shows the 600x600 Web App, which has no microphone and
/// only an English voice. This app is the audio half: it speaks the model
/// lines in zh-CN / ja-JP, records your answers (through the glasses mic when
/// paired) and keeps doing so with the phone locked in your pocket.
@main
struct LinguaLensApp: App {
    @State private var store = SessionStore()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
                .task {
                    store.glasses.configure()
                    store.connect()
                    if ProcessInfo.processInfo.arguments.contains("-autoplay") { store.play() }
                }
                .onOpenURL { store.glasses.handle(url: $0) }
        }
    }
}

struct RootView: View {
    var body: some View {
        TabView {
            NowPlayingView().tabItem { Label("Lesson", systemImage: "waveform") }
            CoursesView().tabItem { Label("Courses", systemImage: "list.bullet") }
            ProgressScreen().tabItem { Label("Progress", systemImage: "chart.bar") }
            SettingsView().tabItem { Label("Settings", systemImage: "gear") }
        }
    }
}
