import CoreLocation
import SwiftUI

/// What the HUD's web control panel and /phone page did, natively: phone
/// sensors, the navigation objective, the gesture pad, skills and a shout.
struct ControlView: View {
    @Environment(SensorBridge.self) private var sensors
    @State private var status: HUDClient.Status?
    @State private var destination = ""
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        @Bindable var sensors = sensors
        NavigationStack {
            Form {
                Section {
                    Toggle("Compass heading", isOn: $sensors.compassOn)
                    Toggle("GPS (navigation)", isOn: $sensors.gpsOn)
                    Toggle("Motion (running, lifting…)", isOn: $sensors.motionOn)
                    LabeledContent("Link") {
                        Text(sensors.connected ? "connected · \(sensors.sent) sent" : "connecting…")
                            .foregroundStyle(sensors.connected ? .green : .orange)
                            .monospacedDigit()
                    }
                    if let h = sensors.heading {
                        LabeledContent("Heading", value: String(format: "%.0f° ±%.0f", h, sensors.headingAccuracy ?? 0))
                    }
                    if sensors.authorization == .denied {
                        Text("Location is off for LiveVision: Settings › Privacy › Location Services.")
                            .font(.caption).foregroundStyle(.orange)
                    } else if let e = sensors.lastError {
                        Text(e).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                    }
                } header: {
                    Text("Phone sensors → HUD")
                } footer: {
                    Text("Drives the compass, the navigation objective and the motion skills. Sends while LiveVision is open, and in your pocket while the glasses stream.")
                }

                BodyTrackingSection()

                Section("Navigation") {
                    if let obj = status?.nav?.objective, status?.nav?.active == true {
                        LabeledContent(obj.step ?? obj.name ?? "Objective") {
                            if let d = obj.distance { Text(d >= 1000 ? String(format: "%.1f km", d / 1000) : "\(Int(d)) m") }
                        }
                    } else if let s = status?.nav?.status, !s.isEmpty {
                        Text(s).foregroundStyle(.secondary)
                    }
                    TextField("Maps link or place name", text: $destination)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .submitLabel(.go)
                        .onSubmit { run { try await $0.setDestination(destination); destination = "" } }
                    HStack {
                        Button("Set destination") { run { try await $0.setDestination(destination); destination = "" } }
                            .disabled(destination.trimmingCharacters(in: .whitespaces).isEmpty)
                        Spacer()
                        Button("Clear", role: .destructive) { run { try await $0.clearDestination() } }
                    }
                    .buttonStyle(.borderless)
                }

                Section {
                    Grid(horizontalSpacing: 10, verticalSpacing: 10) {
                        GridRow {
                            pad("Swipe ◀", "swipe_left")
                            pad("Tap", "tap")
                            pad("Swipe ▶", "swipe_right")
                        }
                        GridRow {
                            pad("Spread", "spread")
                            Color.clear.gridCellUnsizedAxes([.horizontal, .vertical])
                            Button { run { try await $0.shout() } } label: {
                                Text("Fus Ro Dah").frame(maxWidth: .infinity, minHeight: 44)
                            }
                            .buttonStyle(.borderedProminent).tint(.red)
                        }
                    }
                    .padding(.vertical, 4)
                } header: {
                    Text("Gestures & shout")
                } footer: {
                    Text("Tap opens the HUD menu, swipes change tabs, spread closes it.")
                }

                if let skills = status?.skills, !skills.isEmpty {
                    Section("Skills · level \(status?.playerLevel ?? 1)") {
                        ForEach(skills.sorted { $0.value.level > $1.value.level }, id: \.key) { key, s in
                            VStack(alignment: .leading, spacing: 4) {
                                HStack {
                                    Text(s.name ?? key.capitalized)
                                    if s.active == true { Image(systemName: "bolt.fill").foregroundStyle(.yellow).font(.caption) }
                                    Spacer()
                                    Text("\(s.level)").monospacedDigit().foregroundStyle(.secondary)
                                }
                                ProgressView(value: min(max(s.xp ?? 0, 0), 1))
                            }
                        }
                    }
                }
            }
            .navigationTitle("Control")
            .refreshable { await load() }
            .task {
                while !Task.isCancelled {
                    await load()
                    try? await Task.sleep(for: .seconds(5))
                }
            }
            .alert("HUD", isPresented: Binding(get: { error != nil }, set: { if !$0 { error = nil } })) {
                Button("OK", role: .cancel) {}
            } message: { Text(error ?? "") }
        }
    }

    private func pad(_ label: String, _ gesture: String) -> some View {
        Button { sensors.gesture(gesture) } label: {
            Text(label).frame(maxWidth: .infinity, minHeight: 44)
        }
        .buttonStyle(.bordered)
    }

    private func load() async {
        status = try? await HUDClient.fromSettings().status()
    }

    private func run(_ action: @escaping (HUDClient) async throws -> Void) {
        Task {
            busy = true
            defer { busy = false }
            do { try await action(try HUDClient.fromSettings()); await load() }
            catch { self.error = error.localizedDescription }
        }
    }
}
