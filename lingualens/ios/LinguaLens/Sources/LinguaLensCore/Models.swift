import Foundation

// The server's session snapshot (Session.to_dict in server/engine.py plus the
// course fields App.state adds in server/main.py). The server is the source of
// truth: the app only reads these and sends intents back. Every field is
// optional or defaulted, so a server that grows a field - or drops one - never
// breaks decoding on a phone that has not been updated.

public struct LessonState: Decodable, Equatable, Sendable {
    public var mode: String?
    public var lesson: Lesson?
    public var level: Level?
    public var topic: Topic?
    public var step: Step?
    public var position: Position
    public var attempts: Int
    public var slowReplay: Bool
    public var lastScore: Score?
    public var message: String?
    public var scene: String?
    public var history: [HistoryRow]
    public var reviewDue: Int
    public var clientId: String?
    public var active: String?
    public var language: String?
    public var languageName: String?
    public var native: String?
    public var speechLang: String?
    public var provider: String?
    public var courses: [CourseRow]
    public var config: ClientConfig
    /// What the glasses waveguide shows for this step (engine.glasses_card).
    public var glasses: GlassesCard?

    enum CodingKeys: String, CodingKey {
        case mode, lesson, level, topic, step, position, attempts, message, scene, history
        case active, language, native, provider, courses, config, glasses
        case slowReplay = "slow_replay"
        case lastScore = "last_score"
        case reviewDue = "review_due"
        case clientId = "client_id"
        case languageName = "language_name"
        case speechLang = "speech_lang"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        mode = try c.decodeIfPresent(String.self, forKey: .mode)
        lesson = try? c.decodeIfPresent(Lesson.self, forKey: .lesson)
        level = try? c.decodeIfPresent(Level.self, forKey: .level)
        topic = try? c.decodeIfPresent(Topic.self, forKey: .topic)
        step = try c.decodeIfPresent(Step.self, forKey: .step)
        position = (try? c.decodeIfPresent(Position.self, forKey: .position)) ?? Position(index: 0, total: 0)
        attempts = (try? c.decodeIfPresent(Int.self, forKey: .attempts)) ?? 0
        slowReplay = (try? c.decodeIfPresent(Bool.self, forKey: .slowReplay)) ?? false
        lastScore = try? c.decodeIfPresent(Score.self, forKey: .lastScore)
        message = try? c.decodeIfPresent(String.self, forKey: .message)
        scene = try? c.decodeIfPresent(String.self, forKey: .scene)
        history = (try? c.decodeIfPresent([HistoryRow].self, forKey: .history)) ?? []
        reviewDue = (try? c.decodeIfPresent(Int.self, forKey: .reviewDue)) ?? 0
        clientId = try? c.decodeIfPresent(String.self, forKey: .clientId)
        active = try? c.decodeIfPresent(String.self, forKey: .active)
        language = try? c.decodeIfPresent(String.self, forKey: .language)
        languageName = try? c.decodeIfPresent(String.self, forKey: .languageName)
        native = try? c.decodeIfPresent(String.self, forKey: .native)
        speechLang = try? c.decodeIfPresent(String.self, forKey: .speechLang)
        provider = try? c.decodeIfPresent(String.self, forKey: .provider)
        courses = (try? c.decodeIfPresent([CourseRow].self, forKey: .courses)) ?? []
        config = (try? c.decodeIfPresent(ClientConfig.self, forKey: .config)) ?? ClientConfig()
        glasses = try? c.decodeIfPresent(GlassesCard.self, forKey: .glasses)
    }

    /// BCP-47 tag to speak with; same fallback as app.js speechLang().
    public var voiceLanguage: String {
        if let s = speechLang, !s.isEmpty { return s }
        return language == "ja" ? "ja-JP" : "zh-CN"
    }

    /// "HSK 1 · L3 Ordering food", or the vocab topic.
    public var title: String {
        if let t = topic { return "Vocabulary · \(t.titleNative ?? "") \(t.title ?? "")" }
        if let l = lesson { return "\(level?.code ?? "") · L\(l.id) \(l.title ?? "")" }
        return "—"
    }
}

/// One screen for the glasses, decided by the server for every step kind so
/// that a recall shows its English cue and never a bare "…".
public struct GlassesCard: Decodable, Equatable, Sendable {
    public var header: String
    public var cue: String
    public var target: String
    public var reading: String
    public var english: String
    public var footer: String

    public init(header: String = "", cue: String = "", target: String = "",
                reading: String = "", english: String = "", footer: String = "") {
        self.header = header; self.cue = cue; self.target = target
        self.reading = reading; self.english = english; self.footer = footer
    }

    enum CodingKeys: String, CodingKey { case header, cue, target, reading, english, footer }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        func s(_ k: CodingKeys) -> String { (try? c.decodeIfPresent(String.self, forKey: k)) ?? "" }
        self.init(header: s(.header), cue: s(.cue), target: s(.target),
                  reading: s(.reading), english: s(.english), footer: s(.footer))
    }

    /// For a server that predates `glasses`: the old three-field mirror,
    /// fixed so a recall still shows its English cue.
    public static func fallback(for step: Step?) -> GlassesCard {
        guard let step else { return GlassesCard(target: "Lesson complete") }
        switch step.kind {
        case "hear":
            return GlassesCard(cue: "Listen", target: step.note.isEmpty ? "Just listen" : step.note)
        case "info":
            return GlassesCard(target: step.en.isEmpty ? step.text : step.en)
        default:
            if step.text.isEmpty {
                return GlassesCard(cue: "Say it", target: step.promptEn.isEmpty ? step.en : step.promptEn)
            }
            return GlassesCard(target: step.text, reading: step.showReading ? step.reading : "",
                               english: step.en.isEmpty ? step.promptEn : step.en)
        }
    }
}

public struct Step: Decodable, Equatable, Sendable {
    public var kind: String
    public var text: String
    public var reading: String
    public var en: String
    public var promptEn: String
    public var note: String
    public var waitSeconds: Double
    public var round: Int
    public var showTarget: Bool
    public var showReading: Bool
    public var audioText: String
    public var passageTitle: String
    public var chunkIndex: Int
    public var chunkTotal: Int

    enum CodingKeys: String, CodingKey {
        case kind, text, reading, en, note, round
        case promptEn = "prompt_en"
        case waitSeconds = "wait_seconds"
        case showTarget = "show_target"
        case showReading = "show_reading"
        case audioText = "audio_text"
        case passageTitle = "passage_title"
        case chunkIndex = "chunk_index"
        case chunkTotal = "chunk_total"
    }

    public init(kind: String, text: String = "", reading: String = "", en: String = "",
                promptEn: String = "", note: String = "", waitSeconds: Double = 0, round: Int = 0,
                showTarget: Bool = true, showReading: Bool = true, audioText: String = "") {
        self.kind = kind; self.text = text; self.reading = reading; self.en = en
        self.promptEn = promptEn; self.note = note; self.waitSeconds = waitSeconds
        self.round = round; self.showTarget = showTarget; self.showReading = showReading
        self.audioText = audioText; self.passageTitle = ""; self.chunkIndex = 0; self.chunkTotal = 0
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        func s(_ k: CodingKeys) -> String { (try? c.decodeIfPresent(String.self, forKey: k)) ?? "" }
        kind = s(.kind)
        text = s(.text); reading = s(.reading); en = s(.en); promptEn = s(.promptEn); note = s(.note)
        audioText = s(.audioText); passageTitle = s(.passageTitle)
        waitSeconds = (try? c.decodeIfPresent(Double.self, forKey: .waitSeconds)) ?? 0
        round = (try? c.decodeIfPresent(Int.self, forKey: .round)) ?? 0
        showTarget = (try? c.decodeIfPresent(Bool.self, forKey: .showTarget)) ?? true
        showReading = (try? c.decodeIfPresent(Bool.self, forKey: .showReading)) ?? true
        chunkIndex = (try? c.decodeIfPresent(Int.self, forKey: .chunkIndex)) ?? 0
        chunkTotal = (try? c.decodeIfPresent(Int.self, forKey: .chunkTotal)) ?? 0
    }

    /// Steps the server grades by speech (needs_speech() in engine.py).
    public var isSpoken: Bool { ["speak", "recall", "answer", "read", "write"].contains(kind) }
}

public struct Position: Decodable, Equatable, Sendable {
    public var index: Int
    public var total: Int
    public init(index: Int, total: Int) { self.index = index; self.total = total }
}

public struct Lesson: Decodable, Equatable, Sendable {
    public var id: Int
    public var title: String?
    public var goal: String?
}

public struct Level: Decodable, Equatable, Sendable {
    public var id: Int
    public var code: String?
    public var title: String?
}

public struct Topic: Decodable, Equatable, Sendable {
    public var id: String?
    public var title: String?
    public var titleNative: String?
    enum CodingKeys: String, CodingKey { case id, title; case titleNative = "title_native" }
}

public struct Score: Decodable, Equatable, Sendable {
    public var passed: Bool
    public var pron: Double
    public var accuracy: Double
    public var fluency: Double
    public var completeness: Double
    public var tone: Double
    public var recognized: String
    public var reasons: [String]
    public var provider: String?

    enum CodingKeys: String, CodingKey {
        case passed, pron, accuracy, fluency, completeness, tone, recognized, reasons, provider
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        func d(_ k: CodingKeys, _ dflt: Double = 0) -> Double { (try? c.decodeIfPresent(Double.self, forKey: k)) ?? dflt }
        passed = (try? c.decodeIfPresent(Bool.self, forKey: .passed)) ?? false
        pron = d(.pron); accuracy = d(.accuracy); fluency = d(.fluency)
        completeness = d(.completeness); tone = d(.tone, -1)
        recognized = (try? c.decodeIfPresent(String.self, forKey: .recognized)) ?? ""
        reasons = (try? c.decodeIfPresent([String].self, forKey: .reasons)) ?? []
        provider = try? c.decodeIfPresent(String.self, forKey: .provider)
    }
}

public struct HistoryRow: Decodable, Equatable, Sendable {
    public var text: String?
    public var passed: Bool?
    public var score: Double?
    public var attempt: Int?
}

public struct CourseRow: Decodable, Equatable, Sendable, Identifiable {
    public var id: String
    public var name: String?
    public var native: String?
    public var ready: Bool
    public var active: Bool
    public var lessons: Int?
    public var vocab: Int?
    public var lessonsDone: Int?
    public var wordsLearned: Int?
    public var streakDays: Int?
    public var reviewDue: Int?
    public var speechLang: String?
    public var error: String?

    enum CodingKeys: String, CodingKey {
        case id, name, native, ready, active, lessons, vocab, error
        case lessonsDone = "lessons_done"
        case wordsLearned = "words_learned"
        case streakDays = "streak_days"
        case reviewDue = "review_due"
        case speechLang = "speech_lang"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try? c.decodeIfPresent(String.self, forKey: .name)
        native = try? c.decodeIfPresent(String.self, forKey: .native)
        ready = (try? c.decodeIfPresent(Bool.self, forKey: .ready)) ?? false
        active = (try? c.decodeIfPresent(Bool.self, forKey: .active)) ?? false
        lessons = try? c.decodeIfPresent(Int.self, forKey: .lessons)
        vocab = try? c.decodeIfPresent(Int.self, forKey: .vocab)
        lessonsDone = try? c.decodeIfPresent(Int.self, forKey: .lessonsDone)
        wordsLearned = try? c.decodeIfPresent(Int.self, forKey: .wordsLearned)
        streakDays = try? c.decodeIfPresent(Int.self, forKey: .streakDays)
        reviewDue = try? c.decodeIfPresent(Int.self, forKey: .reviewDue)
        speechLang = try? c.decodeIfPresent(String.self, forKey: .speechLang)
        error = try? c.decodeIfPresent(String.self, forKey: .error)
    }
}

/// `state.config`: listening rates are Web Speech rates (1.0 = normal).
public struct ClientConfig: Decodable, Equatable, Sendable {
    public var listeningRate: ListeningRate
    public var listeningVaryPitch: Bool
    public var vocabLabel: String?

    enum CodingKeys: String, CodingKey {
        case listeningRate = "listening_rate"
        case listeningVaryPitch = "listening_vary_pitch"
        case vocabLabel = "vocab_label"
    }

    public init(listeningRate: ListeningRate = ListeningRate(), listeningVaryPitch: Bool = true) {
        self.listeningRate = listeningRate
        self.listeningVaryPitch = listeningVaryPitch
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        listeningRate = (try? c.decodeIfPresent(ListeningRate.self, forKey: .listeningRate)) ?? ListeningRate()
        listeningVaryPitch = (try? c.decodeIfPresent(Bool.self, forKey: .listeningVaryPitch)) ?? true
        vocabLabel = try? c.decodeIfPresent(String.self, forKey: .vocabLabel)
    }
}

public struct ListeningRate: Decodable, Equatable, Sendable {
    public var model: Double?
    public var slow: Double?
    public var listen: Double?
    public var drill: Double?
    public init(model: Double? = nil, slow: Double? = nil, listen: Double? = nil, drill: Double? = nil) {
        self.model = model; self.slow = slow; self.listen = listen; self.drill = drill
    }
}

// MARK: - course tree (/api/course)

public struct CourseTree: Decodable, Sendable {
    public var language: String?
    public var levels: [CourseLevel]
}

public struct CourseLevel: Decodable, Sendable, Identifiable {
    public var id: Int
    public var code: String?
    public var title: String?
    public var lessonCount: Int?
    public var units: [CourseUnit]
    public var vocabTopics: [VocabTopic]?
    enum CodingKeys: String, CodingKey {
        case id, code, title, units
        case lessonCount = "lesson_count"
        case vocabTopics = "vocab_topics"
    }
}

public struct CourseUnit: Decodable, Sendable, Identifiable {
    public var id: Int
    public var title: String?
    public var lessons: [CourseLesson]
}

public struct CourseLesson: Decodable, Sendable, Identifiable {
    public var id: Int
    public var title: String?
    public var goal: String?
}

public struct VocabTopic: Decodable, Sendable, Identifiable {
    public var id: String
    public var title: String?
    public var titleNative: String?
    public var count: Int?
    enum CodingKeys: String, CodingKey { case id, title, count; case titleNative = "title_native" }
}

// MARK: - progress (/api/progress, /api/progress/words)

public struct ProgressSummary: Decodable, Sendable {
    public var course: String?
    public var name: String?
    public var native: String?
    public var lessonsDone: Int
    public var lessonsTotal: Int
    public var wordsLearned: Int
    public var wordsTotal: Int
    public var phrasesLearned: Int
    public var minutes: Double
    public var streakDays: Int
    public var reviewDue: Int
    public var bands: [Band]

    public struct Band: Decodable, Sendable, Identifiable {
        public var id: Int
        public var code: String?
        public var lessonsDone: Int?
        public var lessonsTotal: Int?
        public var wordsLearned: Int?
        public var wordsTotal: Int?
        enum CodingKeys: String, CodingKey {
            case id, code
            case lessonsDone = "lessons_done", lessonsTotal = "lessons_total"
            case wordsLearned = "words_learned", wordsTotal = "words_total"
        }
    }

    enum CodingKeys: String, CodingKey {
        case course, name, native, minutes, bands
        case lessonsDone = "lessons_done", lessonsTotal = "lessons_total"
        case wordsLearned = "words_learned", wordsTotal = "words_total"
        case phrasesLearned = "phrases_learned"
        case streakDays = "streak_days", reviewDue = "review_due"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        func i(_ k: CodingKeys) -> Int { (try? c.decodeIfPresent(Int.self, forKey: k)) ?? 0 }
        course = try? c.decodeIfPresent(String.self, forKey: .course)
        name = try? c.decodeIfPresent(String.self, forKey: .name)
        native = try? c.decodeIfPresent(String.self, forKey: .native)
        lessonsDone = i(.lessonsDone); lessonsTotal = i(.lessonsTotal)
        wordsLearned = i(.wordsLearned); wordsTotal = i(.wordsTotal)
        phrasesLearned = i(.phrasesLearned); streakDays = i(.streakDays); reviewDue = i(.reviewDue)
        minutes = (try? c.decodeIfPresent(Double.self, forKey: .minutes)) ?? 0
        bands = (try? c.decodeIfPresent([Band].self, forKey: .bands)) ?? []
    }
}

public struct WordsPage: Decodable, Sendable {
    public var total: Int
    public var items: [LearnedWord]
}

public struct LearnedWord: Decodable, Sendable, Identifiable {
    public var text: String
    public var reading: String?
    public var en: String?
    public var kind: String?
    public var lastDay: String?
    public var id: String { text + "|" + (kind ?? "") }
    enum CodingKeys: String, CodingKey { case text, reading, en, kind; case lastDay = "last_day" }
}

/// POST /api/attempt response.
public struct AttemptResult: Decodable, Sendable {
    public var passed: Bool
    public var reasons: [String]
    public var score: Score?
    public var heard: String?

    enum CodingKeys: String, CodingKey { case passed, reasons, score, heard }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        passed = (try? c.decodeIfPresent(Bool.self, forKey: .passed)) ?? false
        reasons = (try? c.decodeIfPresent([String].self, forKey: .reasons)) ?? []
        score = try? c.decodeIfPresent(Score.self, forKey: .score)
        heard = try? c.decodeIfPresent(String.self, forKey: .heard)
    }
}
