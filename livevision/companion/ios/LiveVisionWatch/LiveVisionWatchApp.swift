import SwiftUI

/// LiveVision on the Apple Watch: Start, and your wrist and heart rate drive
/// the stream avatar's arm (via the iPhone app). Runs as a workout so it keeps
/// going with your wrist down.
@main
struct LiveVisionWatchApp: App {
    @State private var tracker = WatchTracker()

    var body: some Scene {
        WindowGroup {
            WatchHome()
                .environment(tracker)
                .task { tracker.activate() }
        }
    }
}

struct WatchHome: View {
    @Environment(WatchTracker.self) private var t

    var body: some View {
        @Bindable var t = t
        ScrollView {
            VStack(spacing: 10) {
                HStack(spacing: 6) {
                    Image(systemName: "heart.fill").foregroundStyle(.red)
                    Text(t.heartRate.map { "\(Int($0))" } ?? "--")
                        .font(.system(size: 34, weight: .semibold, design: .rounded))
                        .monospacedDigit()
                    Text("bpm").font(.caption).foregroundStyle(.secondary)
                }
                Button {
                    if t.running { t.stop() } else { Task { await t.start() } }
                } label: {
                    Label(t.running ? "Stop" : "Start", systemImage: t.running ? "stop.fill" : "play.fill")
                        .frame(maxWidth: .infinity)
                }
                .tint(t.running ? .red : .green)

                Picker("Wrist", selection: $t.side) {
                    Text("Left").tag("left")
                    Text("Right").tag("right")
                }
                .disabled(t.running)

                Label(t.phoneReachable ? "iPhone connected" : "Open LiveVision on your iPhone",
                      systemImage: t.phoneReachable ? "iphone" : "iphone.slash")
                    .font(.footnote)
                    .foregroundStyle(t.phoneReachable ? .green : .orange)
                if let e = t.error {
                    Text(e).font(.caption2).foregroundStyle(.orange).multilineTextAlignment(.center)
                }
            }
            .padding(.horizontal, 4)
        }
        .navigationTitle("LiveVision")
    }
}
