import AVKit
import SwiftUI

/// autoclip's approval queue, natively: watch a clip, then post or drop it.
/// Replaces the https://<host>/autoclip/ page.
struct ClipsView: View {
    @State private var pending: [HUDClient.Pending] = []
    @State private var recent: [HUDClient.Clip] = []
    @State private var acting: Set<String> = []
    @State private var error: String?
    @State private var loaded = false

    var body: some View {
        NavigationStack {
            List {
                Section("Waiting for approval") {
                    if pending.isEmpty {
                        Text(loaded ? "Nothing waiting" : "Loading…").foregroundStyle(.secondary)
                    }
                    ForEach(pending) { item in
                        VStack(alignment: .leading, spacing: 8) {
                            ClipCard(clip: item.clip, platforms: item.platforms)
                            HStack {
                                Button(role: .destructive) { act(item.id) { try await $0.reject(item.id) } } label: {
                                    Label("Drop", systemImage: "trash").frame(maxWidth: .infinity)
                                }
                                .buttonStyle(.bordered)
                                Button { act(item.id) { try await $0.approve(item.id) } } label: {
                                    Label("Post", systemImage: "paperplane.fill").frame(maxWidth: .infinity)
                                }
                                .buttonStyle(.borderedProminent)
                            }
                            .disabled(acting.contains(item.id))
                        }
                        .padding(.vertical, 4)
                    }
                }
                Section("Recent clips") {
                    if recent.isEmpty && loaded { Text("No clips yet").foregroundStyle(.secondary) }
                    ForEach(recent) { ClipCard(clip: $0, platforms: nil) }
                }
            }
            .navigationTitle("Clips")
            .refreshable { await load() }
            .task {
                while !Task.isCancelled {
                    await load()
                    try? await Task.sleep(for: .seconds(30))
                }
            }
            .alert("Clips", isPresented: Binding(get: { error != nil }, set: { if !$0 { error = nil } })) {
                Button("OK", role: .cancel) {}
            } message: { Text(error ?? "") }
        }
    }

    private func load() async {
        do {
            let c = try HUDClient.fromSettings()
            async let p = c.pending()
            async let r = c.clips()
            pending = try await p
            recent = Array(try await r.suffix(10).reversed())
        } catch {
            if !loaded { self.error = error.localizedDescription }
        }
        loaded = true
    }

    private func act(_ id: String, _ action: @escaping (HUDClient) async throws -> Void) {
        Task {
            acting.insert(id)
            defer { acting.remove(id) }
            do { try await action(try HUDClient.fromSettings()) } catch { self.error = error.localizedDescription }
            await load()
        }
    }
}

private struct ClipCard: View {
    let clip: HUDClient.Clip
    let platforms: [String]?
    @State private var player: AVPlayer?

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            ZStack {
                if let player {
                    VideoPlayer(player: player)
                } else {
                    Button { start() } label: {
                        Image(systemName: "play.circle.fill").font(.system(size: 44)).foregroundStyle(.white)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                            .background(.black)
                    }
                    .buttonStyle(.plain)
                }
            }
            .aspectRatio(9 / 16, contentMode: .fit)
            .frame(maxHeight: 360)
            .clipShape(RoundedRectangle(cornerRadius: 10))
            Text(clip.decision?.title ?? clip.fileName).font(.headline)
            if let c = clip.decision?.caption, !c.isEmpty {
                Text(c).font(.subheadline).foregroundStyle(.secondary).lineLimit(3)
            }
            Text(meta).font(.caption).foregroundStyle(.secondary)
        }
    }

    private var meta: String {
        var parts = [String(format: "%.0fs", clip.duration ?? 0),
                     String(format: "score %.2f", clip.decision?.score ?? 0)]
        if let p = platforms, !p.isEmpty { parts.append("→ " + p.joined(separator: ", ")) }
        return parts.joined(separator: " · ")
    }

    private func start() {
        guard let c = try? HUDClient.fromSettings() else { return }
        let p = AVPlayer(url: c.videoURL(clip))   // outbox is public: no login needed
        player = p
        p.play()
    }
}
