import SwiftUI
import UniformTypeIdentifiers

/// Prompter tab: load a script, pace it, and put it on the glasses' lens
/// (Teleprompter) without giving up the camera stream.
struct TeleprompterView: View {
    @Environment(Teleprompter.self) private var p
    @Environment(GlassesStreamer.self) private var glasses
    @State private var importing = false
    @State private var importError: String?

    var body: some View {
        @Bindable var p = p
        NavigationStack {
            Form {
                Section {
                    LabeledContent("Lens", value: lensText)
                    if glasses.isStreaming {
                        Label("Streaming continues while the script shows.", systemImage: "dot.radiowaves.left.and.right")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    if p.wantsLens {
                        Button("Hide from glasses", role: .destructive) { p.hide() }
                    } else {
                        Button("Show on glasses") { p.show(on: glasses) }
                        if p.pages.isEmpty {
                            Text("No script yet: paste or import one under Script below.")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    if case .failed(let why) = p.lens {
                        Text(why).font(.caption).foregroundStyle(.orange)
                    }
                    if let input = p.lastInput {
                        LabeledContent("Last glasses input", value: input).font(.caption)
                    }
                    if glasses.isMock, p.lens == .showing {
                        MockLens().frame(height: 260)
                        Button("Simulate a Neural Band swipe") { MockRig.swipeRight() }
                    }
                } header: {
                    Text("Glasses")
                } footer: {
                    Text("Swipe on the Neural Band or temple to turn pages, tap the lens for the next page, select to start or stop auto-scroll. Two-finger tap on the temple closes it.")
                }

                if let page = p.page {
                    Section {
                        if !page.section.isEmpty {
                            Text(page.section).font(.caption).foregroundStyle(.secondary)
                        }
                        Text(page.text).font(.title3)
                        HStack {
                            Button { p.previous() } label: { Image(systemName: "backward.fill") }
                                .disabled(p.index == 0)
                            Spacer()
                            Button { p.toggleAuto() } label: {
                                Label(p.autoScroll ? "Pause" : "Auto", systemImage: p.autoScroll ? "pause.fill" : "play.fill")
                            }
                            Spacer()
                            Button { p.next() } label: { Image(systemName: "forward.fill") }
                                .disabled(p.index + 1 >= p.pages.count)
                        }
                        .buttonStyle(.bordered)
                        if p.pages.count > 1 {
                            Slider(value: Binding(get: { Double(p.index) }, set: { p.go(to: Int($0.rounded())) }),
                                   in: 0...Double(p.pages.count - 1), step: 1)
                        }
                    } header: {
                        Text("Page \(p.index + 1) of \(p.pages.count)")
                    } footer: {
                        Text("\(Self.clock(p.remaining)) left at \(p.wordsPerMinute) words a minute")
                    }
                }

                Section("Pace") {
                    Stepper("\(p.wordsPerMinute) words a minute", value: $p.wordsPerMinute, in: 80...220, step: 5)
                    Stepper("\(p.wordsPerPage) words a page", value: $p.wordsPerPage, in: 15...90, step: 5)
                }

                Section {
                    NavigationLink { SpeechLibraryView() } label: {
                        LabeledContent("Speech library", value: p.scriptTitle ?? "")
                    }
                    NavigationLink("Edit script") { ScriptEditor() }
                    Button("Paste from clipboard") {
                        if let s = UIPasteboard.general.string, !s.isEmpty { p.script = s }
                    }
                    Button("Import a file…") { importing = true }
                    if !p.script.isEmpty {
                        Button("Clear script", role: .destructive) { p.hide(); p.script = "" }
                    }
                    if let importError {
                        Text(importError).font(.caption).foregroundStyle(.orange)
                    }
                } header: {
                    Text("Script")
                } footer: {
                    Text(p.pages.isEmpty
                         ? "Paste or import a speech (.md or .txt). # headings become section labels."
                         : "\(p.totalWords) words · \(p.pages.count) pages · \(Self.clock(Double(p.totalWords) / Double(p.wordsPerMinute) * 60))")
                }
            }
            .navigationTitle("Prompter")
            .fileImporter(isPresented: $importing,
                          allowedContentTypes: [.plainText, UTType(filenameExtension: "md") ?? .plainText]) { result in
                importError = nil
                do {
                    let url = try result.get()
                    let scoped = url.startAccessingSecurityScopedResource()
                    defer { if scoped { url.stopAccessingSecurityScopedResource() } }
                    p.script = try String(contentsOf: url, encoding: .utf8)
                } catch {
                    importError = "Couldn't read that file: \(error.localizedDescription)"
                }
            }
        }
    }

    private var lensText: String {
        switch p.lens {
        case .off: return "Off"
        case .waiting:
            switch glasses.link {
            case .connecting, .registering: return "Connecting glasses…"
            case .paused: return "Glasses paused"
            default: return "Waiting for glasses"
            }
        case .starting: return "Starting…"
        case .showing: return "On the lens"
        case .failed: return "Unavailable"
        }
    }

    static func clock(_ seconds: TimeInterval) -> String {
        let s = Int(seconds.rounded())
        return s >= 3600
            ? String(format: "%d:%02d:%02d", s / 3600, s / 60 % 60, s % 60)
            : String(format: "%d:%02d", s / 60, s % 60)
    }
}

private struct ScriptEditor: View {
    @Environment(Teleprompter.self) private var p
    @State private var draft = ""

    var body: some View {
        TextEditor(text: $draft)
            .font(.body.monospaced())
            .padding(.horizontal, 8)
            .navigationTitle("Script")
            .navigationBarTitleDisplayMode(.inline)
            .onAppear { draft = p.script }
            .onDisappear { if draft != p.script { p.script = draft } }
    }
}

/// The Mock Device Kit's rendering of the lens, in the Simulator.
private struct MockLens: UIViewRepresentable {
    func makeUIView(context: Context) -> UIView { MockRig.lensPreview() ?? UIView() }
    func updateUIView(_ view: UIView, context: Context) {}
}
