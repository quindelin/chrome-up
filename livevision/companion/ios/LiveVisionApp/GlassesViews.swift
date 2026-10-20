import MWDATCamera
import SwiftUI

/// Dashboard section: connect the glasses and stream their camera to the VPS.
struct GlassesSection: View {
    @Environment(GlassesStreamer.self) private var g
    /// The server's view of the same feed (stack.ingest), when known.
    let ingestLive: Bool?

    var body: some View {
        Section {
            HStack {
                Label(g.deviceName ?? (g.isMock ? "Mock glasses" : "Meta glasses"), systemImage: "eyeglasses")
                Spacer()
                if let b = g.battery {
                    Label("\(b)%", systemImage: batterySymbol(b))
                        .labelStyle(.titleAndIcon)
                        .font(.callout.monospacedDigit())
                        .foregroundStyle(b < 20 ? .red : .secondary)
                }
            }
            LabeledContent("Glasses", value: linkText)

            if g.isStreaming {
                StreamStatusRow()
            }

            HStack {
                connectButton
                Spacer()
                streamButton
            }
            .buttonStyle(.bordered)

            if let err = g.lastError {
                Text(err).font(.caption).foregroundStyle(.orange)
            }
        } header: {
            Text("Glasses camera")
        } footer: {
            Text(footer)
        }
    }

    @ViewBuilder private var connectButton: some View {
        switch g.link {
        case .connected, .paused, .connecting:
            Button("Disconnect", role: .destructive) { g.disconnect() }
        case .registering:
            Button("Waiting for Meta AI…") {}.disabled(true)
        case .unavailable:
            Button("Connect glasses") {}.disabled(true)
        default:
            Button("Connect glasses") { g.connect() }
        }
    }

    @ViewBuilder private var streamButton: some View {
        if g.isStreaming {
            Button { Task { await g.stopStreaming() } } label: {
                Label("Stop", systemImage: "stop.fill")
            }
            .tint(.red)
        } else {
            Button { Task { await g.startStreaming() } } label: {
                Label("Start streaming", systemImage: "dot.radiowaves.left.and.right")
            }
            .buttonStyle(.borderedProminent)
            .tint(.red)
            .disabled({ if case .unavailable = g.link { return true }; return false }())
        }
    }

    private var linkText: String {
        switch g.link {
        case .unavailable(let why): "DAT unavailable: \(why)"
        case .unregistered: "not set up — Connect opens Meta AI"
        case .registering: "approve LiveVision in Meta AI"
        case .idle: "not connected"
        case .connecting: "connecting…"
        case .connected: "connected"
        case .paused: "paused (resumes by itself)"
        }
    }

    private var footer: String {
        if g.isStreaming, ingestLive == true { return "The VPS is receiving the feed (Glasses → VPS is LIVE)." }
        if g.isStreaming { return "Keep the phone unlocked or in a pocket — the stream keeps running with the screen off." }
        return "Sends the glasses camera and your voice to the VPS (\(Settings.transport == .srt ? "SRT" : "RTMP")). Battery goes to the HUD's magicka bar."
    }

    private func batterySymbol(_ b: Int) -> String {
        if g.charging { return "battery.100.bolt" }
        switch b {
        case ..<13: return "battery.0"
        case ..<38: return "battery.25"
        case ..<63: return "battery.50"
        case ..<88: return "battery.75"
        default: return "battery.100"
        }
    }
}

private struct StreamStatusRow: View {
    @Environment(GlassesStreamer.self) private var g

    var body: some View {
        let (text, color) = state
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Circle().fill(color).frame(width: 10, height: 10)
                Text(text).font(.headline)
                Spacer()
                if let t = g.startedAt, g.uplink == .live {
                    Text(t, style: .timer).font(.callout.monospacedDigit()).foregroundStyle(.secondary)
                }
            }
            Text(detail).font(.caption.monospacedDigit()).foregroundStyle(.secondary)
        }
        .accessibilityElement(children: .combine)
    }

    private var state: (String, Color) {
        switch g.uplink {
        case .idle: return ("Starting…", .gray)
        case .connecting: return ("Connecting to VPS…", .yellow)
        case .live where g.fpsIn == 0: return ("Connected — waiting for camera", .orange)
        case .live: return ("LIVE to VPS", .red)
        case .reconnecting(let n, let why): return ("Reconnecting (\(n)) — \(why)", .orange)
        }
    }

    private var detail: String {
        var parts = ["camera \(cameraText)", "\(g.fpsIn) fps"]
        let k = g.stats.kbpsOut
        parts.append(k >= 1000 ? String(format: "%.1f Mb/s", Double(k) / 1000) : "\(k) kb/s")
        parts.append("dropped \(g.droppedFrames) fr")
        if Settings.transport == .srt { parts.append("\(g.stats.droppedPackets) pkt") }
        if let rtt = g.stats.rttMs { parts.append(String(format: "rtt %.0f ms", rtt)) }
        return parts.joined(separator: " · ")
    }

    private var cameraText: String {
        switch g.camera {
        case nil: "—"
        case .streaming: "on"
        case .waitingForDevice: "waiting for glasses"
        case .starting: "starting"
        case .paused: "paused"
        case .stopping, .stopped: "stopped"
        @unknown default: "?"
        }
    }
}
