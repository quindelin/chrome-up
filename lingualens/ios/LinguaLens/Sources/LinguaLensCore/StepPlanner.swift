import Foundation

/// One thing the player does for a step, in order.
public enum Cue: Equatable, Sendable {
    /// Speak `text` in `language` (BCP-47) at a Web Speech rate (1.0 = normal).
    case say(String, language: String, rate: Double)
    case wait(Double)
    /// Hands-free take: beep, record until silence, upload to /api/attempt.
    case record
    /// POST /api/next with at=<position.index>.
    case advance
}

/// What to do for the current step. `key` changes whenever the step, its text
/// or the attempt count changes, which is when app.js re-speaks (spokenKey).
public struct StepPlan: Equatable, Sendable {
    public var key: String
    public var cues: [Cue]
}

/// Mirrors server/web/app.js - maybeSpeak, maybeAdvance and the pacing in
/// render() - for a player with no screen in front of the learner.
///
/// `handsFree` is the pocket mode: since nothing is being read off a screen,
/// lines the web page would only print are spoken (the English cue of a
/// recall, a passage to read back, a scene), and every graded step ends in an
/// automatic recording. With it off the plan is exactly the web phone page's:
/// speak what it speaks, advance what it advances, and leave recording to the
/// talk button.
public struct StepPlanner: Sendable {
    public var handsFree: Bool
    /// Kana / kanji / hanzi cards: spoken and moved past on their own in
    /// hands-free mode (on the web page they wait for a tap).
    public var autoAdvanceLiteracy: Bool
    public var englishVoice: String

    public init(handsFree: Bool = true, autoAdvanceLiteracy: Bool = true, englishVoice: String = "en-US") {
        self.handsFree = handsFree
        self.autoAdvanceLiteracy = autoAdvanceLiteracy
        self.englishVoice = englishVoice
    }

    public static func key(for state: LessonState) -> String {
        guard let s = state.step else { return "\(state.position.index):done" }
        return "\(state.position.index):\(s.kind):\(s.text):\(state.attempts)"
    }

    /// Web Speech rate for a kind of line, from state.config.listening_rate.
    public static func rate(_ kind: String, _ config: ClientConfig, fallback: Double) -> Double {
        let r = config.listeningRate
        switch kind {
        case "listen": return r.listen ?? fallback
        case "slow": return r.slow ?? fallback
        case "drill": return r.drill ?? fallback
        default: return r.model ?? fallback
        }
    }

    public func plan(for state: LessonState) -> StepPlan {
        let key = Self.key(for: state)
        guard let s = state.step else { return StepPlan(key: key, cues: []) }
        let lang = state.voiceLanguage
        let cfg = state.config
        func rate(_ k: String, _ f: Double) -> Double { Self.rate(k, cfg, fallback: f) }
        func say(_ text: String, _ r: Double) -> [Cue] { text.isEmpty ? [] : [.say(text, language: lang, rate: r)] }
        func english(_ text: String) -> [Cue] {
            (handsFree && !text.isEmpty) ? [.say(text, language: englishVoice, rate: 1.0)] : []
        }
        let take: [Cue] = handsFree ? [.record] : []
        var cues: [Cue] = []

        switch s.kind {
        case "info":
            // the scene / recall-round card: counts down, then moves on
            cues += english(s.en)
            if s.waitSeconds > 0 && !handsFree { cues.append(.wait(s.waitSeconds)) }
            else if handsFree { cues.append(.wait(0.6)) }
            cues.append(.advance)

        case "listen":
            // the model line, at something close to how it would actually be said
            cues += say(s.text, rate("listen", 0.9)) + [.wait(0.35), .advance]

        case "hear":
            // audio_text, not text: the line must be playable without being shown
            let line = s.audioText.isEmpty ? s.text : s.audioText
            cues += say(line, rate("listen", 1.0)) + [.wait(0.35), .advance]

        case "answer":
            // the question out loud, slower once you have missed it
            cues += say(s.text, state.attempts > 0 ? rate("slow", 0.6) : rate("model", 0.9)) + take

        case "speak", "recall":
            let replay = state.slowReplay ? rate("slow", 0.55) : rate("drill", 0.8)
            if state.attempts > 0 {
                cues += say(s.text, replay)
            } else if handsFree {
                if s.kind == "recall" && !s.showTarget {
                    // retrieval from memory: the English is the only prompt
                    cues += english(s.promptEn.isEmpty ? s.en : s.promptEn)
                } else {
                    cues += say(s.text, rate("model", 0.9))
                }
            }
            cues += take

        case "read", "write":
            // a passage to read aloud or summarise: nobody is reading it here
            if handsFree { cues += say(s.text, rate("model", 0.9)) }
            cues += take

        case "kana", "kanji", "hanzi":
            if handsFree && autoAdvanceLiteracy {
                cues += say(s.text, rate("model", 0.9)) + [.wait(1.5), .advance]
            }

        default:
            break
        }
        return StepPlan(key: key, cues: cues)
    }
}

/// Web Speech rate (1.0 = normal) to AVSpeechUtterance.rate, whose normal is
/// AVSpeechUtteranceDefaultSpeechRate (0.5) on a 0...1 scale.
public enum SpeechRate {
    public static let avDefault: Float = 0.5

    public static func avRate(fromWeb rate: Double) -> Float {
        min(1.0, max(0.1, Float(rate) * avDefault))
    }

    /// app.js: 0.85 + ((voiceCursor * 7) % 5) * 0.07 - a nudge, not a cartoon.
    public static func pitch(cursor: Int) -> Float {
        0.85 + Float((cursor * 7) % 5) * 0.07
    }
}

/// Which system voices are fit to model a line.
public enum SpeechVoices {
    /// Apple's Eloquence voices (Eddy, Flo, Grandma, Grandpa, Reed, Rocko,
    /// Sandy, Shelley) and the novelty voices are characters, not speakers.
    public static func isNatural(identifier: String, isNovelty: Bool) -> Bool {
        !isNovelty && !identifier.lowercased().contains("eloquence")
    }
}
