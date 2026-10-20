import SwiftUI

/// autoclip's approval queue, natively (docs/CLIP_POSTING.md): every clip
/// autoclip cuts waits here. Tap one to watch it, fix the caption, pick the
/// platforms and post; posted clips move to the bottom with their links.
struct ClipsView: View {
    @State private var pending: [HUDClient.Pending] = []
    @State private var posted: [HUDClient.Pending] = []
    @State private var platforms: HUDClient.Platforms?
    @State private var error: String?
    @State private var loaded = false

    var body: some View {
        NavigationStack {
            List {
                if let platforms, !platforms.isLive {
                    Section {
                        Label("Dry run: posting only copies to the VPS outbox. Set AUTOCLIP_PUBLISH=live on the VM to post for real.",
                              systemImage: "testtube.2")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                }
                Section("Waiting for you") {
                    if pending.isEmpty {
                        Text(loaded ? "Nothing waiting" : "Loading…").foregroundStyle(.secondary)
                    }
                    ForEach(pending) { item in
                        NavigationLink(value: item.id) { ClipRow(item: item) }
                            .swipeActions {
                                Button(role: .destructive) { drop(item.id) } label: { Label("Drop", systemImage: "trash") }
                            }
                    }
                }
                if !posted.isEmpty {
                    Section("Posted") {
                        ForEach(posted) { item in
                            NavigationLink(value: item.id) { ClipRow(item: item) }
                        }
                    }
                }
            }
            .navigationTitle("Clips")
            .navigationDestination(for: String.self) { id in
                if let item = (pending + posted).first(where: { $0.id == id }) {
                    ClipDetailView(item: item, platforms: platforms, changed: { Task { await load() } })
                }
            }
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
            async let d = c.posted()
            async let f = c.platforms()
            pending = try await p
            posted = (try? await d) ?? []
            platforms = try? await f
        } catch {
            if !loaded { self.error = error.localizedDescription }
        }
        loaded = true
    }

    private func drop(_ id: String) {
        Task {
            do { try await HUDClient.fromSettings().reject(id) } catch { self.error = error.localizedDescription }
            await load()
        }
    }
}

private struct ClipRow: View {
    let item: HUDClient.Pending

    var body: some View {
        HStack(spacing: 12) {
            AsyncImage(url: thumbURL) { img in
                img.resizable().aspectRatio(contentMode: .fill)
            } placeholder: {
                Color.black.overlay(Image(systemName: "film").foregroundStyle(.secondary))
            }
            .frame(width: 54, height: 96)
            .clipShape(RoundedRectangle(cornerRadius: 6))
            VStack(alignment: .leading, spacing: 4) {
                Text(item.title.isEmpty ? item.clip.fileName : item.title).font(.headline).lineLimit(2)
                if !item.caption.isEmpty {
                    Text(item.caption).font(.subheadline).foregroundStyle(.secondary).lineLimit(2)
                }
                Text(String(format: "%.0fs · score %.2f", item.clip.duration ?? 0, item.clip.decision?.score ?? 0))
                    .font(.caption).foregroundStyle(.secondary)
                PostBadges(posts: item.posts ?? [:])
            }
        }
    }

    private var thumbURL: URL? {
        guard let t = item.thumbUrl, !t.isEmpty else { return nil }
        return try? HUDClient.fromSettings().mediaURL(t)
    }
}

/// One chip per platform the clip went to: spinner, ✓ or ✗.
struct PostBadges: View {
    let posts: [String: HUDClient.Post]

    var body: some View {
        if !posts.isEmpty {
            HStack(spacing: 6) {
                ForEach(posts.keys.sorted(), id: \.self) { name in
                    let p = posts[name]!
                    HStack(spacing: 3) {
                        if p.isBusy { ProgressView().controlSize(.mini) }
                        else { Image(systemName: p.isDone ? "checkmark.circle.fill" : "xmark.circle.fill") }
                        Text(PlatformName.label(name))
                    }
                    .font(.caption2)
                    .padding(.horizontal, 6).padding(.vertical, 2)
                    .background(Capsule().fill(p.isDone ? Color.green.opacity(0.2)
                                               : p.isBusy ? Color.gray.opacity(0.2) : Color.red.opacity(0.2)))
                }
            }
        }
    }
}

enum PlatformName {
    static func label(_ name: String) -> String {
        switch name {
        case "youtube": "YouTube"
        case "instagram": "Instagram"
        case "tiktok": "TikTok"
        case "x": "X"
        default: name.capitalized
        }
    }
}
