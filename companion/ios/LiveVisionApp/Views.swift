import SwiftUI

struct DashboardView: View {
    @Environment(StackStore.self) private var store
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            List {
                Section { HeadlineCard() }
                    .listRowInsets(EdgeInsets())
                    .listRowBackground(Color.clear)

                GlassesSection(ingestLive: store.stack?.ingest?.isLive)

                if let s = store.stack {
                    FeedsSection(stack: s)
                    RestreamSection(stack: s)
                    ClipsSection(stack: s)
                    HostSection(host: s.host)
                }

                if let u = store.updated {
                    Section {
                        Text("Updated \(u, style: .relative) ago")
                            .font(.footnote)
                            .foregroundStyle(store.isStale ? .orange : .secondary)
                    }
                }
            }
            .navigationTitle("LiveVision")
            .refreshable { await store.refresh() }
            .toolbar {
                Button { showSettings = true } label: { Image(systemName: "gearshape") }
                    .accessibilityLabel("Settings")
            }
            .sheet(isPresented: $showSettings) {
                SettingsView { Task { await store.refresh() } }
            }
            .alert("Restream", isPresented: Binding(
                get: { store.actionError != nil },
                set: { if !$0 { store.actionError = nil } })) {
                Button("OK", role: .cancel) {}
            } message: { Text(store.actionError ?? "") }
        }
    }
}

// MARK: - headline

private struct HeadlineCard: View {
    @Environment(StackStore.self) private var store

    var body: some View {
        let (title, detail, color, symbol) = describe(store.headline)
        HStack(spacing: 14) {
            Image(systemName: symbol)
                .font(.system(size: 34, weight: .semibold))
                .symbolEffect(.pulse, isActive: isLive)
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(.title2.bold())
                Text(detail).font(.subheadline).opacity(0.9)
            }
            Spacer(minLength: 0)
        }
        .foregroundStyle(.white)
        .padding(18)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(color.gradient, in: RoundedRectangle(cornerRadius: 18))
        .padding(.horizontal, 16)
        .padding(.vertical, 4)
        .accessibilityElement(children: .combine)
    }

    private var isLive: Bool {
        if case .liveOn = store.headline { return true }
        return false
    }

    private func describe(_ h: StackStore.Headline) -> (String, String, Color, String) {
        switch h {
        case .liveOn(let names):
            return ("LIVE", "on " + names.map(\.capitalized).joined(separator: ", "),
                    .red, "dot.radiowaves.left.and.right")
        case .program:
            return ("On the VPS", "HUD program is up — not public until you go live",
                    .orange, "antenna.radiowaves.left.and.right")
        case .glassesOnly:
            return ("Glasses only", "Feed is arriving, OBS is not publishing the program",
                    .yellow, "eyeglasses")
        case .idle:
            return ("Ready", "VPS is up, glasses are not sending", .gray, "pause.circle")
        case .offline(let why):
            return ("Offline", why, Color(white: 0.25), "bolt.horizontal.circle")
        case .loading:
            return ("Checking…", Settings.baseURL?.host() ?? "", Color(white: 0.35), "hourglass")
        }
    }
}

// MARK: - sections

private struct FeedsSection: View {
    let stack: Stack

    var body: some View {
        Section("Feeds") {
            FeedRow(title: "Glasses → VPS", feed: stack.ingest, symbol: "eyeglasses")
            FeedRow(title: "OBS program (HUD)", feed: stack.program, symbol: "tv")
        }
    }
}

private struct FeedRow: View {
    let title: String
    let feed: Stack.Feed?
    let symbol: String

    var body: some View {
        let live = feed?.isLive ?? false
        HStack {
            Label(title, systemImage: symbol)
            Spacer()
            VStack(alignment: .trailing, spacing: 2) {
                Text(live ? "LIVE" : "off")
                    .font(.caption.bold())
                    .padding(.horizontal, 8).padding(.vertical, 2)
                    .background(live ? Color.red : Color.secondary.opacity(0.2), in: Capsule())
                    .foregroundStyle(live ? .white : .secondary)
                if live {
                    Text(detail).font(.caption).foregroundStyle(.secondary).monospacedDigit()
                } else if let err = feed?.error {
                    Text(err).font(.caption2).foregroundStyle(.orange).lineLimit(1)
                }
            }
        }
    }

    private var detail: String {
        var parts: [String] = []
        if let k = feed?.bitrateKbps { parts.append(k >= 1000 ? String(format: "%.1f Mb/s", Double(k) / 1000) : "\(k) kb/s") }
        if let d = feed?.sinceDate { parts.append(Fmt.duration(Date().timeIntervalSince(d))) }
        return parts.joined(separator: " · ")
    }
}

private struct RestreamSection: View {
    @Environment(StackStore.self) private var store
    let stack: Stack

    var body: some View {
        Section {
            if stack.restream?.enabled == false {
                Text("Off on the VPS. Set AUTOCLIP_LIVE_STREAMS=1 and the stream keys in deploy/obs-vps/.env, then ./gcp.sh deploy.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            ForEach(stack.restream?.targets ?? []) { t in
                TargetRow(target: t, programLive: stack.program?.isLive ?? false)
            }
        } header: {
            Text("Restream")
        } footer: {
            if stack.restream?.enabled != false {
                Text("Same as saying “go live on …”. Restreams the OBS program, HUD included.")
            }
        }
    }
}

private struct TargetRow: View {
    @Environment(StackStore.self) private var store
    let target: Stack.Target
    let programLive: Bool

    var body: some View {
        let busy = store.busyTargets.contains(target.name)
        let active = target.active ?? false
        VStack(alignment: .leading, spacing: 2) {
            Toggle(isOn: Binding(
                get: { active },
                set: { on in Task { await store.setRestream(target.name, on: on) } })) {
                HStack {
                    Text(target.name.capitalized)
                    if busy { ProgressView().controlSize(.small) }
                }
            }
            .tint(.red)
            .disabled(busy || !(target.keySet ?? false) || (!active && !programLive))
            if !(target.keySet ?? false) {
                Text("No stream key on the VPS").font(.caption).foregroundStyle(.secondary)
            } else if active, let up = target.uptimeSeconds {
                Text("live \(Fmt.duration(up))").font(.caption).foregroundStyle(.secondary)
            } else if let err = target.lastError, !err.isEmpty {
                Text(err).font(.caption).foregroundStyle(.orange).lineLimit(2)
            } else if !programLive {
                Text("Waiting for the OBS program").font(.caption).foregroundStyle(.secondary)
            }
        }
    }
}

private struct ClipsSection: View {
    let stack: Stack

    var body: some View {
        let a = stack.autoclip
        Section("Clips") {
            if let url = try? StackClient.fromSettings().approvalPage {
                Link(destination: url) {
                    HStack {
                        Label("Approval queue", systemImage: "checkmark.rectangle.stack")
                        Spacer()
                        if let n = a?.pending, n > 0 {
                            Text("\(n)").font(.callout.bold()).foregroundStyle(.white)
                                .padding(.horizontal, 8).background(.red, in: Capsule())
                        }
                    }
                }
            }
            LabeledContent("Clips made", value: "\(a?.clips ?? 0)")
            LabeledContent("Publishing", value: a?.publishMode == "live" ? "live (after approval)" : "dry run")
            if let ts = a?.lastCycleTs {
                LabeledContent("Last cycle") {
                    Text(Date(timeIntervalSince1970: ts), style: .relative)
                }
            }
            if let note = a?.lastNote, !note.isEmpty {
                Text(note).font(.caption).foregroundStyle(.secondary).lineLimit(3)
            }
        }
    }
}

private struct HostSection: View {
    let host: Stack.Host?

    var body: some View {
        Section("VPS") {
            if let h = host {
                if let load = h.load?.first, let cpus = h.cpus, cpus > 0 {
                    Gauge(value: min(load / Double(cpus), 1)) {
                        Text("CPU")
                    } currentValueLabel: {
                        Text(String(format: "load %.1f / %d", load, cpus))
                    }
                    .tint(load / Double(cpus) > 0.9 ? .red : .accentColor)
                }
                if let total = h.memTotal, let avail = h.memAvailable, total > 0 {
                    Gauge(value: Double(total - avail) / Double(total)) {
                        Text("Memory")
                    } currentValueLabel: {
                        Text("\(Fmt.bytes(total - avail)) of \(Fmt.bytes(total))")
                    }
                }
                if let total = h.diskTotal, let free = h.diskFree, total > 0 {
                    Gauge(value: Double(total - free) / Double(total)) {
                        Text("Disk")
                    } currentValueLabel: {
                        Text("\(Fmt.bytes(free)) free")
                    }
                    .tint(free < 1_500_000_000 ? .red : .accentColor)
                }
                if let up = h.uptimeSeconds {
                    LabeledContent("Up for", value: Fmt.duration(up))
                }
                if let err = h.error {
                    Text(err).font(.caption).foregroundStyle(.orange)
                }
            } else {
                Text("No host stats").foregroundStyle(.secondary)
            }
        }
    }
}

// MARK: - settings

struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(GlassesStreamer.self) private var glasses
    @State private var host = Settings.host
    @State private var user = Settings.user
    @State private var password = Settings.password
    @State private var streamKey = Settings.streamKey
    @State private var srtPassphrase = Settings.srtPassphrase
    @State private var transport = Settings.transport
    @State private var audioSource = Settings.audioSource
    @State private var mock = Settings.mockGlasses
    var onSave: () -> Void

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("136-80-148-90.sslip.io", text: $host)
                        .textContentType(.URL)
                        .keyboardType(.URL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                } header: {
                    Text("VPS host")
                } footer: {
                    Text("The fixed host from ./gcp.sh info (after ./gcp.sh static-ip).")
                }
                Section {
                    TextField("User", text: $user)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                    SecureField("Password", text: $password)
                } header: {
                    Text("Approval page login")
                } footer: {
                    Text("AUTOCLIP_USER / AUTOCLIP_PASSWORD from deploy/obs-vps/.env on the VM. ./gcp.sh companion writes all of this into the build.")
                }
                Section {
                    SecureField("Stream key", text: $streamKey)
                    SecureField("SRT passphrase", text: $srtPassphrase)
                    Picker("Send over", selection: $transport) {
                        ForEach(Settings.Transport.allCases) { Text($0.label).tag($0) }
                    }
                    Picker("Audio", selection: $audioSource) {
                        ForEach(Settings.AudioSource.allCases) { Text($0.label).tag($0) }
                    }
                } header: {
                    Text("Glasses stream")
                } footer: {
                    Text("STREAM_KEY / SRT_PASSPHRASE from the VM's .env. RTMP is the tested path; SRT is experimental (the VM drops it after a few seconds). The glasses mic needs DAT's beta audio; the phone mic always works. Applies the next time you start streaming.")
                }
                Section {
                    Toggle("Mock glasses", isOn: $mock)
                } footer: {
                    Text("DAT's simulated Ray-Ban Display with a test-pattern camera, for trying the stream without the glasses (also in the Simulator).")
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Settings.host = host
                        Settings.user = user
                        Settings.password = password
                        Settings.streamKey = streamKey
                        Settings.srtPassphrase = srtPassphrase
                        Settings.transport = transport
                        Settings.audioSource = audioSource
                        if mock != Settings.mockGlasses {
                            Task { await glasses.setMock(mock) }
                        }
                        onSave()
                        dismiss()
                    }
                }
            }
        }
    }
}

// MARK: - formatting

enum Fmt {
    static func duration(_ s: Double) -> String {
        let f = DateComponentsFormatter()
        f.allowedUnits = s >= 3600 ? [.day, .hour, .minute] : [.minute, .second]
        f.unitsStyle = .abbreviated
        f.maximumUnitCount = 2
        return f.string(from: max(0, s)) ?? ""
    }

    static func bytes(_ b: Int64) -> String {
        ByteCountFormatter.string(fromByteCount: b, countStyle: .memory)
    }
}
