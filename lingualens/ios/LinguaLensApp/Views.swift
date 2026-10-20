import LinguaLensCore
import SwiftUI

// MARK: - now playing

struct NowPlayingView: View {
    @Environment(SessionStore.self) private var store
    @State private var showEnglish = false

    var body: some View {
        let s = store.state
        let step = s?.step
        VStack(spacing: 18) {
            HStack {
                Text(s?.title ?? "LinguaLens").font(.headline).lineLimit(1)
                Spacer()
                if let s { Text("\(s.position.index + (step == nil ? 0 : 1))/\(s.position.total)").monospacedDigit() }
            }
            .foregroundStyle(.secondary)

            Text(store.connection).font(.caption).foregroundStyle(.secondary)

            Spacer()

            Text(role(step)).font(.caption.weight(.semibold)).textCase(.uppercase)
                .padding(.horizontal, 10).padding(.vertical, 4)
                .background(.tint.opacity(0.15), in: Capsule())

            if let step {
                if step.kind != "hear" {
                    if step.showReading && !step.reading.isEmpty {
                        Text(step.reading).font(.title3).foregroundStyle(.secondary)
                    }
                    Text(step.text.isEmpty ? step.en : step.text)
                        .font(.system(size: step.text.count > 10 ? 30 : 44, weight: .semibold))
                        .multilineTextAlignment(.center)
                } else {
                    Text("Just listen").font(.title)
                }
                if !step.en.isEmpty && !step.text.isEmpty {
                    Text(showEnglish ? step.en : "Tap to show English")
                        .foregroundStyle(.secondary)
                        .onTapGesture { showEnglish.toggle() }
                }
            } else if s != nil {
                Text("Course complete").font(.largeTitle)
            }

            if let score = s?.lastScore { ScoreView(score: score, attempts: s?.attempts ?? 0) }

            Spacer()

            Text(store.lastMessage).font(.footnote).foregroundStyle(.secondary)
                .multilineTextAlignment(.center).lineLimit(3)

            Text(phaseLabel).font(.caption).foregroundStyle(store.phase == .listening ? .red : .secondary)
            if store.phase == .listening {
                ProgressView(value: Double(max(0, store.level + 60)), total: 60).tint(.red)
            }

            GlassesBar()

            HStack(spacing: 36) {
                Button { store.repeatLine() } label: { Image(systemName: "gobackward") }
                Button { store.isPlaying ? store.pause() : store.play() } label: {
                    Image(systemName: store.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                        .font(.system(size: 64))
                }
                Button { store.next() } label: { Image(systemName: "forward.end") }
            }
            .font(.title)

            Button { store.talk() } label: {
                Label(store.phase == .listening ? "Stop & grade" : "Talk", systemImage: "mic.fill")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(store.phase == .listening ? .red : .accentColor)
            .disabled(step?.isSpoken != true)
        }
        .padding()
        .onChange(of: step?.text) { showEnglish = false }
    }

    private var phaseLabel: String {
        switch store.phase {
        case .listening: return "Listening… speak now"
        case .speaking: return "Playing model line"
        case .grading: return "Grading…"
        case .paused: return "Paused - press play, then put the phone away"
        case .waiting: return store.isPlaying ? "…" : ""
        case .idle: return ""
        }
    }

    private func role(_ step: Step?) -> String {
        guard let step else { return "done" }
        switch step.kind {
        case "info": return step.round == 0 ? "scene" : "recall round"
        case "listen", "hear": return "listen"
        default: return step.kind
        }
    }
}

struct ScoreView: View {
    let score: Score
    let attempts: Int
    var body: some View {
        VStack(spacing: 4) {
            Text("\(Int(score.pron.rounded()))")
                .font(.system(size: 40, weight: .bold)).monospacedDigit()
                .foregroundStyle(score.passed ? .green : .orange)
            Text("\(score.passed ? "passed" : "not yet") · \(attempts) attempt\(attempts == 1 ? "" : "s")"
                 + (score.tone >= 0 ? " · tone \(Int(score.tone))" : ""))
                .font(.caption).foregroundStyle(.secondary)
            if !score.recognized.isEmpty { Text("heard: \(score.recognized)").font(.caption2) }
        }
    }
}

// MARK: - courses / lessons

struct CoursesView: View {
    @Environment(SessionStore.self) private var store
    @State private var tree: CourseTree?
    @State private var error: String?

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Button("Review (\(store.state?.reviewDue ?? 0) due)") { store.startReview(); store.play() }
                }
                Section("Course") {
                    ForEach(store.state?.courses ?? []) { c in
                        Button {
                            store.selectCourse(c.id)
                        } label: {
                            HStack {
                                Text("\(c.native ?? c.id) · \(c.name ?? "")")
                                Spacer()
                                if c.active { Image(systemName: "checkmark") }
                            }
                        }
                        .disabled(!c.ready)
                    }
                }
                ForEach(tree?.levels ?? []) { level in
                    Section(level.title ?? level.code ?? "Level \(level.id)") {
                        ForEach(level.units) { unit in
                            NavigationLink(unit.title ?? "Unit \(unit.id)") {
                                List(unit.lessons) { lesson in
                                    Button {
                                        store.startLesson(lesson.id); store.play()
                                    } label: {
                                        VStack(alignment: .leading) {
                                            Text("L\(lesson.id) \(lesson.title ?? "")")
                                            if let g = lesson.goal { Text(g).font(.caption).foregroundStyle(.secondary) }
                                        }
                                    }
                                }
                                .navigationTitle(unit.title ?? "")
                            }
                        }
                        if let topics = level.vocabTopics, !topics.isEmpty {
                            NavigationLink("Vocabulary · \(topics.count) topics") {
                                List(topics) { t in
                                    Button("\(t.titleNative ?? "") · \(t.title ?? "") (\(t.count ?? 0))") {
                                        store.startVocab(t.id); store.play()
                                    }
                                }
                            }
                        }
                    }
                }
                if let error { Text(error).foregroundStyle(.red) }
            }
            .navigationTitle("Courses")
            .task(id: store.state?.active) { await load() }
            .refreshable { await load() }
        }
    }

    private func load() async {
        guard let client = store.client else { return }
        do { tree = try await client.course(store.state?.active ?? ""); error = nil }
        catch { self.error = error.localizedDescription }
    }
}

// MARK: - progress

struct ProgressScreen: View {
    @Environment(SessionStore.self) private var store
    @State private var summary: ProgressSummary?
    @State private var words: [LearnedWord] = []
    @State private var query = ""

    var body: some View {
        NavigationStack {
            List {
                if let p = summary {
                    Section(p.name ?? "") {
                        LabeledContent("Lessons", value: "\(p.lessonsDone) / \(p.lessonsTotal)")
                        LabeledContent("Words", value: "\(p.wordsLearned) / \(p.wordsTotal)")
                        LabeledContent("Phrases", value: "\(p.phrasesLearned)")
                        LabeledContent("Minutes", value: "\(Int(p.minutes))")
                        LabeledContent("Streak", value: "\(p.streakDays) days")
                        LabeledContent("Review due", value: "\(p.reviewDue)")
                    }
                    Section("Bands") {
                        ForEach(p.bands) { b in
                            LabeledContent(b.code ?? "\(b.id)",
                                           value: "\(b.lessonsDone ?? 0)/\(b.lessonsTotal ?? 0) lessons · \(b.wordsLearned ?? 0) words")
                        }
                    }
                }
                Section("Learned words") {
                    ForEach(words) { w in
                        VStack(alignment: .leading) {
                            Text(w.text).font(.headline)
                            Text([w.reading, w.en].compactMap { $0 }.joined(separator: " · "))
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    if words.isEmpty { Text("Nothing yet - pass a line to learn its words.").foregroundStyle(.secondary) }
                }
            }
            .searchable(text: $query)
            .navigationTitle("Progress")
            .task(id: query) { await load() }
            .refreshable { await load() }
        }
    }

    private func load() async {
        guard let client = store.client else { return }
        summary = try? await client.progress()
        words = (try? await client.words(query: query))?.items ?? []
    }
}

// MARK: - settings

struct SettingsView: View {
    @Environment(SessionStore.self) private var store
    @State private var server = Settings.server
    @State private var key = Settings.key
    @State private var clientId = Settings.clientId
    @State private var glassesDisplay = Settings.glassesDisplay

    var body: some View {
        @Bindable var store = store
        NavigationStack {
            Form {
                Section {
                    TextField("https://lingualens-….run.app (or paste the phone link)", text: $server)
                        .textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                    SecureField("Access key", text: $key)
                    TextField("Client id", text: $clientId)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                    Button("Save & reconnect") {
                        if let parsed = ServerConfig.parse(server, key: key, clientId: clientId) {
                            Settings.server = parsed.baseURL.absoluteString
                            Settings.key = parsed.key
                            Settings.clientId = parsed.clientId
                            server = Settings.server; key = Settings.key; clientId = Settings.clientId
                        }
                        store.connect()
                    }
                    Text(store.connection).font(.caption).foregroundStyle(.secondary)
                } header: { Text("Server") } footer: {
                    Text("Same client id as the glasses page = one shared session.")
                }

                Section("Player") {
                    Toggle("Hands-free (pocket mode)", isOn: $store.handsFree)
                    Text("Speaks every line, records your answer after each model line and stops on its own when you go quiet. Lock-screen and headphone controls: play/pause, next, previous = repeat.")
                        .font(.caption).foregroundStyle(.secondary)
                    LabeledContent("Microphone", value: store.audio.inputName)
                    LabeledContent("Last voice", value: store.audio.lastVoice)
                    Text("For natural model audio, download an Enhanced or Premium Chinese / Japanese voice: iOS Settings → Accessibility → Spoken Content → Voices. LinguaLens uses the best one installed.")
                        .font(.caption).foregroundStyle(.secondary)
                }

                Section("Ray-Ban Display") {
                    Text(store.glasses.status).font(.callout).textSelection(.enabled)
                    Text(store.glasses.diagnostics).font(.caption.monospaced())
                        .foregroundStyle(.secondary).textSelection(.enabled)
                    Button("Register with Meta AI") { Task { await store.glasses.register() } }
                    Toggle("Show lessons on the glasses", isOn: $glassesDisplay)
                        .onChange(of: glassesDisplay) { Settings.glassesDisplay = glassesDisplay }
                    Text("Each step appears on the glasses display: the English, characters and pinyin. Turn off to run lessons by audio only. Takes effect the next time you connect.")
                        .font(.caption).foregroundStyle(.secondary)
                    Button("Connect glasses") { store.glasses.connect(withDisplay: glassesDisplay) }
                    Button("Disconnect", role: .destructive) { store.glasses.disconnect() }
                    Text("Tap / pinch = talk · swipe forward = next · swipe back = repeat.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Settings")
        }
    }
}

/// Connect to the glasses from the lesson screen, not only from Settings,
/// and bring the lesson back after it was closed there.
struct GlassesBar: View {
    @Environment(SessionStore.self) private var store

    var body: some View {
        let g = store.glasses
        VStack(spacing: 4) {
            if !g.registered {
                Button { Task { await g.register() } } label: {
                    Label("Set up glasses", systemImage: "eyeglasses")
                }
                .buttonStyle(.bordered)
            } else if !g.connected {
                Button { g.showOnGlasses() } label: {
                    Label("Connect glasses", systemImage: "eyeglasses")
                }
                .buttonStyle(.borderedProminent)
            } else if !g.displayActive && Settings.glassesDisplay {
                Button { g.showOnGlasses() } label: {
                    Label("Show on glasses", systemImage: "eyeglasses")
                }
                .buttonStyle(.borderedProminent)
            }
            Text(g.status).font(.caption2).foregroundStyle(.secondary).lineLimit(1)
        }
    }
}
