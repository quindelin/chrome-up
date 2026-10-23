import SwiftUI

/// Control tab: what drives the avatar's body, and whether each part is live.
struct BodyTrackingSection: View {
    @Environment(BodyTracker.self) private var body_
    @Environment(SensorBridge.self) private var sensors
    @Environment(WatchLink.self) private var watch
    @State private var bandWrist = Settings.bandWrist
    /// arm calibration: nil, or what to do right now
    @State private var calStep: String?

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
                Button(calStep ?? "Calibrate arms") { Task { await calibrateArms() } }
                    .disabled(calStep != nil)
                if let ask = body_.armPrompt, calStep == nil {
                    Text(ask).font(.caption).foregroundStyle(.orange)
                }
                Text("Hold each pose until the next prompt: arms hanging at your sides, then a T-pose. Do it once per session with the Watch and band on (again if the arms drift).")
                    .font(.caption).foregroundStyle(.secondary)
            }
        } header: {
            Text("Body tracking → avatar")
        } footer: {
            Text("Head and band motion need the glasses connected (DAT beta, Developer Mode). The arms follow the Watch and the Neural Band once calibrated; the lens reminds you when they aren't.")
        }
    }

    /// Two holds the HUD measures (server/arms.py): arms down finds each
    /// sensor's forearm axis, the T-pose says which way is "out".
    private func calibrateArms() async {
        let haptic = UINotificationFeedbackGenerator()
        for (pose, phase) in [("Arms down at your sides", "down"), ("T-pose: arms straight out", "tpose")] {
            for n in stride(from: 3, through: 1, by: -1) {
                calStep = "\(pose) · \(n)"
                try? await Task.sleep(for: .seconds(1))
            }
            sensors.sendJSON(["body": ["calibrate": phase]])
            haptic.notificationOccurred(.success)
        }
        calStep = "Calibrated"
        try? await Task.sleep(for: .seconds(1.5))
        calStep = nil
    }

    private var motionText: String {
        switch body_.motion {
        case .off: return "off"
        case .waiting: return "waiting for the glasses"
        case .starting: return "starting…"
        case .streaming:
            var s = "live · head \(body_.headSamples)" + (body_.bandSamples > 0 ? " · band \(body_.bandSamples)" : " · no band data")
            if body_.unknownSamples > 0 { s += " · unknown \(body_.unknownSamples)" }
            if let input = LensRouter.shared.lastInput { s += " · last input: \(input)" }
            return s
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
