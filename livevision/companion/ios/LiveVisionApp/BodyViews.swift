import SwiftUI

/// Control tab: what drives the avatar's body, and whether each part is live.
struct BodyTrackingSection: View {
    @Environment(BodyTracker.self) private var body_
    @Environment(SensorBridge.self) private var sensors
    @Environment(WatchLink.self) private var watch
    @State private var bandWrist = Settings.bandWrist
    @State private var hfov = Settings.cameraHFOV

    var body: some View {
        @Bindable var b = body_
        @Bindable var sensors = sensors
        Section {
            Toggle("Sitting / standing (phone in pocket)", isOn: $sensors.postureOn)
            Toggle(isOn: $b.headOn) {
                VStack(alignment: .leading) {
                    Text("Head + Neural Band (glasses motion)")
                    Text(motionText).font(.caption).foregroundStyle(motionColor)
                }
            }
            Toggle(isOn: $b.handsOn) {
                VStack(alignment: .leading) {
                    Text("Hands (glasses camera)")
                    Text(handsText).font(.caption).foregroundStyle(.secondary)
                }
            }
            Toggle(isOn: $b.watchOn) {
                VStack(alignment: .leading) {
                    Text("Apple Watch (wrist + heart rate)")
                    Text(watchText).font(.caption).foregroundStyle(watch.fresh() ? .green : .secondary)
                }
            }
            Picker("Neural Band wrist", selection: $bandWrist) {
                Text("Left").tag("left")
                Text("Right").tag("right")
            }
            .onChange(of: bandWrist) { Settings.bandWrist = bandWrist }
            VStack(alignment: .leading) {
                LabeledContent("Camera field of view", value: "\(Int(hfov))°")
                Slider(value: $hfov, in: 40...100, step: 1)
                    .onChange(of: hfov) { Settings.cameraHFOV = hfov }
            }
        } header: {
            Text("Body tracking → avatar")
        } footer: {
            Text("Head and band motion need the glasses connected (DAT beta, Developer Mode); hands need the camera streaming. If the avatar's hand sits closer or further than yours, adjust the field of view.")
        }
    }

    private var motionText: String {
        switch body_.motion {
        case .off: return "off"
        case .waiting: return "waiting for the glasses"
        case .starting: return "starting…"
        case .streaming: return "live · head \(body_.headSamples)" + (body_.bandSamples > 0 ? " · band \(body_.bandSamples)" : " · no band data")
        case .failed(let why): return why
        }
    }

    private var motionColor: Color {
        switch body_.motion {
        case .streaming: return .green
        case .failed: return .orange
        default: return .secondary
        }
    }

    private var handsText: String {
        guard body_.handsOn else { return "off" }
        if let seen = body_.handsSeenAt, Date().timeIntervalSince(seen) < 1 {
            return "seeing " + body_.hands.keys.sorted().joined(separator: " + ")
        }
        return "none in view (needs the camera streaming)"
    }

    private var watchText: String {
        guard watch.supported else { return "this phone can't pair a Watch" }
        guard watch.paired else { return "no Watch paired" }
        guard watch.installed else { return "install LiveVision on the Watch" }
        if watch.fresh() {
            let hr = watch.heartRate.map { " · \(Int($0)) bpm" } ?? ""
            return "live · \(watch.side) wrist\(hr)"
        }
        return watch.reachable ? "open LiveVision on the Watch and tap Start" : "Watch app not running"
    }
}
