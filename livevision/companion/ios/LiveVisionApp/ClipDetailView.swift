import AVKit
import SwiftUI

/// One clip: watch it, fix title / caption / hashtags, pick platforms, post.
/// YouTube and Instagram post from the VPS in the background (this screen
/// polls their status); TikTok and X open on the phone, where you finish
/// the post (docs/CLIP_POSTING.md).
struct ClipDetailView: View {
    let platforms: HUDClient.Platforms?
    var changed: () -> Void

    @State private var item: HUDClient.Pending
    @State private var title: String
    @State private var caption: String
    @State private var tags: String
    @State private var privacy: String
    @State private var selected: Set<String>
    @State private var player: AVPlayer?
    @State private var working: String?
    @State private var error: String?
    @State private var confirmDrop = false
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL

    init(item: HUDClient.Pending, platforms: HUDClient.Platforms?, changed: @escaping () -> Void) {
        self.platforms = platforms
        self.changed = changed
        _item = State(initialValue: item)
        _title = State(initialValue: item.title)
        _caption = State(initialValue: item.caption)
        _tags = State(initialValue: item.hashtags.map { "#\($0)" }.joined(separator: " "))
        _privacy = State(initialValue: item.edits?.youtubePrivacy ?? platforms?.youtubePrivacy ?? "public")
        // YouTube + Instagram when they are set up and not posted yet; TikTok / X are opt-in
        let ready = Set((platforms?.platforms ?? []).filter { !$0.onDevice && $0.configured }.map(\.name))
        _selected = State(initialValue: ready.filter { item.post($0)?.isDone != true })
    }

    var body: some View {
        Form {
            Section {
                ZStack {
                    if let player {
                        VideoPlayer(player: player)
                    } else {
                        Button { play() } label: {
                            Image(systemName: "play.circle.fill").font(.system(size: 54)).foregroundStyle(.white)
                                .frame(maxWidth: .infinity, maxHeight: .infinity).background(.black)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .aspectRatio(9 / 16, contentMode: .fit)
                .frame(maxHeight: 420)
                .frame(maxWidth: .infinity)
                .listRowInsets(EdgeInsets())
            }

            Section {
                TextField("Title (YouTube)", text: $title, axis: .vertical)
                TextField("Caption", text: $caption, axis: .vertical).lineLimit(3...8)
                TextField("#hashtags", text: $tags)
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
            } header: {
                Text("Text")
            } footer: {
                Text(counters).monospacedDigit()
            }

            Section {
                ForEach(platforms?.platforms ?? []) { p in
                    Toggle(isOn: binding(p.name)) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(PlatformName.label(p.name))
                            Text(subtitle(p)).font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .disabled(!p.configured || item.post(p.name)?.isDone == true)
                }
                if selected.contains("youtube") {
                    Picker("YouTube visibility", selection: $privacy) {
                        ForEach(platforms?.youtubePrivacyOptions ?? ["public", "unlisted", "private"], id: \.self) {
                            Text($0.capitalized)
                        }
                    }
                }
            } header: {
                Text("Post to")
            } footer: {
                if platforms?.isLive == false {
                    Text("Dry run: YouTube and Instagram only copy to the VPS outbox.")
                }
            }

            Section {
                Button { post() } label: {
                    HStack {
                        Spacer()
                        if let working {
                            ProgressView().padding(.trailing, 6)
                            Text(working)
                        }
                        else { Label(postLabel, systemImage: "paperplane.fill") }
                        Spacer()
                    }
                }
                .disabled(working != nil || selected.isEmpty || item.isPosting)
                Button("Save text without posting") { save() }
                    .disabled(working != nil)
            }

            if let posts = item.posts, !posts.isEmpty {
                Section("Status") {
                    ForEach(posts.keys.sorted(), id: \.self) { name in
                        statusRow(name, posts[name]!)
                    }
                }
            }

            Section {
                Button("Drop this clip", role: .destructive) { confirmDrop = true }
            }
        }
        .navigationTitle(title.isEmpty ? "Clip" : title)
        .navigationBarTitleDisplayMode(.inline)
        .task(id: item.isPosting) {
            // poll while the VPS is uploading
            while item.isPosting && !Task.isCancelled {
                try? await Task.sleep(for: .seconds(2))
                await refresh()
            }
        }
        .onDisappear { player?.pause() }
        .confirmationDialog("Drop this clip?", isPresented: $confirmDrop, titleVisibility: .visible) {
            Button("Drop", role: .destructive) { drop() }
        }
        .alert("Clip", isPresented: Binding(get: { error != nil }, set: { if !$0 { error = nil } })) {
            Button("OK", role: .cancel) {}
        } message: { Text(error ?? "") }
    }

    // MARK: rows

    @ViewBuilder
    private func statusRow(_ name: String, _ p: HUDClient.Post) -> some View {
        let device = platform(name)?.onDevice ?? false
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                if p.isBusy { ProgressView().controlSize(.small) }
                else {
                    Image(systemName: p.isDone ? "checkmark.circle.fill" : "exclamationmark.triangle.fill")
                        .foregroundStyle(p.isDone ? Color.green : Color.orange)
                }
                Text(PlatformName.label(name)).bold()
                Spacer()
                Text(stateLabel(p)).font(.caption).foregroundStyle(.secondary)
            }
            if let m = p.message, !m.isEmpty, !p.isDone {
                Text(m).font(.caption).foregroundStyle(.secondary)
            }
            HStack {
                if let u = p.url, let url = URL(string: u), u.hasPrefix("http") {
                    Button("Open") { openURL(url) }.buttonStyle(.bordered)
                }
                if !p.isDone && !p.isBusy {
                    Button(device ? "Share again" : "Retry") { post(only: [name]) }.buttonStyle(.bordered)
                    if device {
                        Button("Mark posted") { mark(name, "shared") }.buttonStyle(.bordered)
                    }
                }
            }
            .disabled(working != nil)
        }
    }

    // MARK: helpers

    private func platform(_ name: String) -> HUDClient.Platform? {
        platforms?.platforms.first { $0.name == name }
    }

    private func binding(_ name: String) -> Binding<Bool> {
        Binding(get: { selected.contains(name) },
                set: { on in if on { selected.insert(name) } else { selected.remove(name) } })
    }

    private func subtitle(_ p: HUDClient.Platform) -> String {
        if let done = item.post(p.name), done.isDone { return stateLabel(done) }
        if !p.configured { return p.reason ?? "not set up" }
        return p.onDevice ? "opens \(PlatformName.label(p.name)) on this phone" : "posted by the VPS"
    }

    private func stateLabel(_ p: HUDClient.Post) -> String {
        switch p.state {
        case "queued": "waiting"
        case "uploading": "uploading…"
        case "posted": "posted"
        case "dry_run": "dry run ✓"
        case "shared": "handed over"
        case "cancelled": "cancelled"
        default: "failed"
        }
    }

    private var hashtags: [String] {
        tags.split(whereSeparator: { $0 == " " || $0 == "," || $0 == "\n" })
            .map { String($0).trimmingCharacters(in: CharacterSet(charactersIn: "#")) }
            .filter { !$0.isEmpty }
    }

    /// The text TikTok / X / Instagram see: caption, then the hashtags.
    private var fullCaption: String {
        let t = hashtags.map { "#\($0)" }.joined(separator: " ")
        return [caption, t].filter { !$0.isEmpty }.joined(separator: caption.isEmpty ? "" : "\n\n")
    }

    /// "YouTube title 24/100 · Instagram 140/2200 · X 300/280 ⚠︎" for what's selected.
    private var counters: String {
        var parts: [String] = []
        for p in platforms?.platforms ?? [] where selected.contains(p.name) {
            if let max = p.limits?.title { parts.append("\(PlatformName.label(p.name)) title \(title.count)/\(max)\(title.count > max ? " ⚠︎" : "")") }
            if let max = p.limits?.caption {
                let n = fullCaption.count
                parts.append("\(PlatformName.label(p.name)) \(n)/\(max)\(n > max ? " ⚠︎" : "")")
            }
        }
        return parts.isEmpty ? "Pick a platform below." : parts.joined(separator: " · ")
    }

    private var postLabel: String {
        let names = (platforms?.platforms ?? []).filter { selected.contains($0.name) }.map { PlatformName.label($0.name) }
        return names.isEmpty ? "Post" : "Post to " + names.joined(separator: ", ")
    }

    private var videoURL: URL? {
        guard let c = try? HUDClient.fromSettings() else { return nil }
        if let v = item.videoUrl, !v.isEmpty { return c.mediaURL(v) }
        return c.videoURL(item.clip)
    }

    private func play() {
        guard let url = videoURL else { return }
        let p = AVPlayer(url: url)            // outbox is public: no login needed
        p.actionAtItemEnd = .none
        NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: p.currentItem,
                                               queue: .main) { _ in p.seek(to: .zero); p.play() }
        player = p
        p.play()
    }

    // MARK: actions

    private func refresh() async {
        guard let c = try? HUDClient.fromSettings(), let fresh = try? await c.clip(item.id) else { return }
        item = fresh
        if !fresh.isPosting { changed() }
    }

    private func save() {
        Task {
            working = "Saving…"
            defer { working = nil }
            do {
                item = try await HUDClient.fromSettings().edit(item.id, title: title, caption: caption,
                                                               hashtags: hashtags, youtubePrivacy: privacy)
                changed()
            } catch { self.error = error.localizedDescription }
        }
    }

    /// Server platforms go to the VPS in one call (it answers at once); then
    /// each device platform opens on the phone, one after the other.
    private func post(only: [String]? = nil) {
        let names = only ?? (platforms?.platforms ?? []).map(\.name).filter { selected.contains($0) }
        let server = names.filter { platform($0)?.onDevice == false }
        let device = names.filter { platform($0)?.onDevice == true }
        Task {
            defer { working = nil }
            do {
                let c = try HUDClient.fromSettings()
                working = "Sending…"
                if server.isEmpty {
                    item = try await c.edit(item.id, title: title, caption: caption, hashtags: hashtags,
                                            youtubePrivacy: privacy)
                } else {
                    item = try await c.post(item.id, platforms: server, title: title, caption: caption,
                                            hashtags: hashtags, youtubePrivacy: privacy)
                }
                for name in device {
                    guard let url = videoURL else { break }
                    working = "Opening \(PlatformName.label(name))…"
                    let outcome = name == "tiktok"
                        ? try await ClipShare.tiktok(video: url, caption: fullCaption)
                        : try await ClipShare.x(video: url, caption: fullCaption)
                    if case .unconfirmed = outcome {
                        error = "Did it post on \(PlatformName.label(name))? Tap Mark posted under Status if it did."
                        item = try await c.shared(item.id, platform: name, state: "failed",
                                                  message: "not confirmed: finish it in \(PlatformName.label(name)), then Mark posted")
                    } else {
                        item = try await c.shared(item.id, platform: name, state: outcome.state, message: outcome.message)
                    }
                }
                changed()
            } catch {
                self.error = error.localizedDescription
                await refresh()
            }
        }
    }

    private func mark(_ name: String, _ state: String) {
        Task {
            do {
                item = try await HUDClient.fromSettings().shared(item.id, platform: name, state: state)
                changed()
            } catch { self.error = error.localizedDescription }
        }
    }

    private func drop() {
        Task {
            do {
                try await HUDClient.fromSettings().reject(item.id)
                changed()
                dismiss()
            } catch { self.error = error.localizedDescription }
        }
    }
}
