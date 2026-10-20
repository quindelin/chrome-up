import XCTest
@testable import LinguaLensCore

private func fixture(_ name: String) throws -> Data {
    let url = try XCTUnwrap(Bundle.module.url(forResource: name, withExtension: "json", subdirectory: "Fixtures"))
    return try Data(contentsOf: url)
}

private func state(_ json: String) throws -> LessonState {
    try JSONDecoder().decode(LessonState.self, from: Data(json.utf8))
}

final class StateDecodingTests: XCTestCase {
    func testDecodesLiveServerSnapshot() throws {
        // captured from the Cloud Run server's /api/state
        let s = try JSONDecoder().decode(LessonState.self, from: fixture("state_info"))
        XCTAssertEqual(s.step?.kind, "info")
        XCTAssertEqual(s.step?.waitSeconds, 6)
        XCTAssertEqual(s.position, Position(index: 0, total: 125))
        XCTAssertEqual(s.voiceLanguage, "zh-CN")
        XCTAssertEqual(s.config.listeningRate.listen, 1.0)
        XCTAssertEqual(s.config.listeningRate.slow, 0.6)
        XCTAssertEqual(s.courses.first?.id, "zh")
        XCTAssertTrue(s.courses.first?.active ?? false)
        XCTAssertEqual(s.title, "HSK 1 · L1 Hello")
        XCTAssertNil(s.lastScore)
    }

    func testDecodesScoreHistoryAndIgnoresUnknownFields() throws {
        let s = try JSONDecoder().decode(LessonState.self, from: fixture("state_recall"))
        XCTAssertEqual(s.step?.kind, "recall")
        XCTAssertEqual(s.step?.promptEn, "Say hello")
        XCTAssertFalse(s.step?.showTarget ?? true)
        XCTAssertEqual(s.lastScore?.passed, true)
        XCTAssertEqual(s.lastScore?.pron ?? 0, 81.2, accuracy: 0.001)
        XCTAssertEqual(s.lastScore?.tone, -1)
        XCTAssertEqual(s.history.first?.attempt, 1)
    }

    func testCourseCompleteHasNoStep() throws {
        let s = try state(#"{"step": null, "position": {"index": 12, "total": 12}, "language": "ja"}"#)
        XCTAssertNil(s.step)
        XCTAssertEqual(s.voiceLanguage, "ja-JP")
        XCTAssertEqual(s.config, ClientConfig())
        XCTAssertEqual(StepPlanner().plan(for: s).cues, [])
    }

    func testWrongTypesDegradeInsteadOfThrowing() throws {
        let s = try state(#"{"step": {"kind": "speak", "text": "你好", "wait_seconds": "soon"}, "attempts": "x", "courses": 3}"#)
        XCTAssertEqual(s.step?.text, "你好")
        XCTAssertEqual(s.step?.waitSeconds, 0)
        XCTAssertEqual(s.attempts, 0)
        XCTAssertEqual(s.courses, [])
    }
}

final class StepPlannerTests: XCTestCase {
    private func make(_ step: String, attempts: Int = 0, slow: Bool = false, lang: String = "zh-CN") throws -> LessonState {
        try state("""
        {"step": \(step), "position": {"index": 4, "total": 20}, "attempts": \(attempts),
         "slow_replay": \(slow), "speech_lang": "\(lang)",
         "config": {"listening_rate": {"model": 0.95, "slow": 0.6, "listen": 1.0, "drill": 0.85}}}
        """)
    }

    func testListenSpeaksThenAdvances() throws {
        let p = StepPlanner().plan(for: try make(#"{"kind": "listen", "text": "你好"}"#))
        XCTAssertEqual(p.cues, [.say("你好", language: "zh-CN", rate: 1.0), .wait(0.35), .advance])
        XCTAssertEqual(p.key, "4:listen:你好:0")
    }

    func testHearPlaysAudioTextNotText() throws {
        let p = StepPlanner().plan(for: try make(#"{"kind": "hear", "text": "", "audio_text": "我们走吧"}"#))
        XCTAssertEqual(p.cues.first, .say("我们走吧", language: "zh-CN", rate: 1.0))
        XCTAssertEqual(p.cues.last, .advance)
    }

    func testSpeakFirstTryHandsFreeModelsThenRecords() throws {
        let p = StepPlanner().plan(for: try make(#"{"kind": "speak", "text": "谢谢"}"#))
        XCTAssertEqual(p.cues, [.say("谢谢", language: "zh-CN", rate: 0.95), .record])
    }

    func testSpeakRetryUsesDrillThenSlowRate() throws {
        let drill = StepPlanner().plan(for: try make(#"{"kind": "speak", "text": "谢谢"}"#, attempts: 1))
        XCTAssertEqual(drill.cues, [.say("谢谢", language: "zh-CN", rate: 0.85), .record])
        let slow = StepPlanner().plan(for: try make(#"{"kind": "speak", "text": "谢谢"}"#, attempts: 2, slow: true))
        XCTAssertEqual(slow.cues.first, .say("谢谢", language: "zh-CN", rate: 0.6))
        XCTAssertNotEqual(drill.key, slow.key)
    }

    func testRecallSpeaksTheEnglishPromptNotTheAnswer() throws {
        let p = StepPlanner().plan(for: try make(
            #"{"kind": "recall", "text": "你好", "en": "Hello", "prompt_en": "Greet her", "show_target": false}"#))
        XCTAssertEqual(p.cues, [.say("Greet her", language: "en-US", rate: 1.0), .record])
    }

    func testWebParityWithoutHandsFree() throws {
        let planner = StepPlanner(handsFree: false)
        // app.js says nothing on a first speak attempt and never records by itself
        XCTAssertEqual(planner.plan(for: try make(#"{"kind": "speak", "text": "谢谢"}"#)).cues, [])
        XCTAssertEqual(planner.plan(for: try make(#"{"kind": "answer", "text": "你叫什么？"}"#, attempts: 1)).cues,
                       [.say("你叫什么？", language: "zh-CN", rate: 0.6)])
        XCTAssertEqual(planner.plan(for: try make(#"{"kind": "info", "en": "A scene", "wait_seconds": 6}"#)).cues,
                       [.wait(6), .advance])
        XCTAssertEqual(planner.plan(for: try make(#"{"kind": "kana", "text": "あ"}"#, lang: "ja-JP")).cues, [])
    }

    func testInfoAndLiteracyInPocketMode() throws {
        let info = StepPlanner().plan(for: try make(#"{"kind": "info", "en": "You meet a neighbour.", "wait_seconds": 6}"#))
        XCTAssertEqual(info.cues, [.say("You meet a neighbour.", language: "en-US", rate: 1.0), .wait(0.6), .advance])
        let kana = StepPlanner().plan(for: try make(#"{"kind": "kana", "text": "あ"}"#, lang: "ja-JP"))
        XCTAssertEqual(kana.cues, [.say("あ", language: "ja-JP", rate: 0.95), .wait(1.5), .advance])
    }

    func testRateFallbacksWhenConfigMissing() {
        XCTAssertEqual(StepPlanner.rate("listen", ClientConfig(), fallback: 0.9), 0.9)
        XCTAssertEqual(StepPlanner.rate("slow", ClientConfig(listeningRate: ListeningRate(slow: 0.5)), fallback: 0.6), 0.5)
    }

    func testSpeechRateAndPitchMapping() {
        XCTAssertEqual(SpeechRate.avRate(fromWeb: 1.0), 0.5)
        XCTAssertEqual(SpeechRate.avRate(fromWeb: 0.6), 0.3, accuracy: 0.0001)
        XCTAssertEqual(SpeechRate.avRate(fromWeb: 5), 1.0)
        let pitches = (0..<5).map { SpeechRate.pitch(cursor: $0) }
        XCTAssertEqual(Set(pitches).count, 5)
        XCTAssertTrue(pitches.allSatisfy { $0 >= 0.85 && $0 <= 1.13 })
    }
}

final class WAVTests: XCTestCase {
    func testHeaderIs16kMono16Bit() {
        let pcm = Data(repeating: 0, count: 3200)
        let wav = WAV.encode(pcm: pcm)
        XCTAssertEqual(wav.count, 44 + 3200)
        XCTAssertEqual(String(decoding: wav[0..<4], as: UTF8.self), "RIFF")
        XCTAssertEqual(String(decoding: wav[8..<16], as: UTF8.self), "WAVEfmt ")
        XCTAssertEqual(String(decoding: wav[36..<40], as: UTF8.self), "data")
        func u32(_ o: Int) -> UInt32 { wav[o..<o + 4].withUnsafeBytes { $0.loadUnaligned(as: UInt32.self) }.littleEndian }
        func u16(_ o: Int) -> UInt16 { wav[o..<o + 2].withUnsafeBytes { $0.loadUnaligned(as: UInt16.self) }.littleEndian }
        XCTAssertEqual(u32(4), 36 + 3200)
        XCTAssertEqual(u16(20), 1)        // PCM
        XCTAssertEqual(u16(22), 1)        // mono
        XCTAssertEqual(u32(24), 16_000)   // sample rate
        XCTAssertEqual(u32(28), 32_000)   // byte rate
        XCTAssertEqual(u16(32), 2)        // block align
        XCTAssertEqual(u16(34), 16)       // bits
        XCTAssertEqual(u32(40), 3200)
    }

    func testPCM16ClipsAndScales() {
        let d = WAV.pcm16([0, 1, -1, 2, -2, 0.5])
        let v = d.withUnsafeBytes { Array($0.bindMemory(to: Int16.self)) }.map { Int16(littleEndian: $0) }
        XCTAssertEqual(v, [0, 32767, -32768, 32767, -32768, 16383])
    }

    func testResampleKeepsDuration() {
        let oneSecond48k = [Float](repeating: 0.25, count: 48_000)
        let out = WAV.resample(oneSecond48k, from: 48_000)
        XCTAssertEqual(out.count, 16_000)
        XCTAssertEqual(out[100], 0.25, accuracy: 1e-6)
    }

    func testRMS() {
        XCTAssertEqual(WAV.rmsDB([]), -120)
        XCTAssertEqual(WAV.rmsDB([0, 0]), -120)
        XCTAssertEqual(WAV.rmsDB([1, -1, 1, -1]), 0, accuracy: 0.001)
        XCTAssertEqual(WAV.rmsDB([0.1, -0.1]), -20, accuracy: 0.01)
    }
}

final class EndpointerTests: XCTestCase {
    private func run(_ levels: [Float], block: Double = 0.1) -> (SpeechEndpointer.Decision, Double) {
        var e = SpeechEndpointer()
        for l in levels {
            let d = e.feed(levelDB: l, duration: block)
            if d != .listening { return (d, e.elapsed) }
        }
        return (.listening, e.elapsed)
    }

    func testStopsAfterSpeechThenSilence() {
        let levels = [Float](repeating: -60, count: 5) + [Float](repeating: -20, count: 10) + [Float](repeating: -60, count: 20)
        let (d, t) = run(levels)
        XCTAssertEqual(d, .finished)
        XCTAssertEqual(t, 0.5 + 1.0 + 1.1, accuracy: 0.11)
    }

    func testNoSpeechTimesOut() {
        let (d, t) = run([Float](repeating: -70, count: 100))
        XCTAssertEqual(d, .noSpeech)
        XCTAssertEqual(t, 7, accuracy: 0.11)
    }

    func testCapsLongTakes() {
        let (d, t) = run([Float](repeating: -15, count: 200))
        XCTAssertEqual(d, .finished)
        XCTAssertEqual(t, 12, accuracy: 0.11)
    }

    func testClickIsNotSpeech() {
        // one loud 50 ms block (a cough, a tap on the glasses) is not an answer
        var e = SpeechEndpointer()
        _ = e.feed(levelDB: -10, duration: 0.05)
        XCTAssertFalse(e.heardSpeech)
    }
}

final class ClientTests: XCTestCase {
    func testParsesPastedPhoneLink() throws {
        let c = try XCTUnwrap(ServerConfig.parse("https://ll.example.run.app/phone?key=abc123&client_id=me"))
        XCTAssertEqual(c.baseURL.absoluteString, "https://ll.example.run.app")
        XCTAssertEqual(c.key, "abc123")
        XCTAssertEqual(c.clientId, "me")
        XCTAssertEqual(c.socketURL.absoluteString, "wss://ll.example.run.app/ws?client_id=me")
    }

    func testBareHostAndExplicitValues() throws {
        let c = try XCTUnwrap(ServerConfig.parse("192.168.1.5:8899", key: "k", clientId: "tester"))
        XCTAssertEqual(c.baseURL.absoluteString, "https://192.168.1.5:8899")
        let local = try XCTUnwrap(ServerConfig.parse("http://192.168.1.5:8899"))
        XCTAssertEqual(local.socketURL.absoluteString, "ws://192.168.1.5:8899/ws?client_id=me")
        XCTAssertNil(ServerConfig.parse("   "))
    }

    func testAuthorizeSetsHeaderOnlyWithKey() {
        var r = URLRequest(url: URL(string: "https://x")!)
        ServerConfig(baseURL: URL(string: "https://x")!, key: "").authorize(&r)
        XCTAssertNil(r.value(forHTTPHeaderField: "X-LinguaLens-Key"))
        ServerConfig(baseURL: URL(string: "https://x")!, key: "s3cret").authorize(&r)
        XCTAssertEqual(r.value(forHTTPHeaderField: "X-LinguaLens-Key"), "s3cret")
    }

    func testMultipartAndFormEncoding() {
        let (body, boundary) = LessonClient.multipart(fields: ["client_id": "me", "encoding": "wav"], fileField: "file",
                                                      filename: "attempt.wav", mime: "audio/wav",
                                                      file: Data("RIFF".utf8), boundary: "B")
        XCTAssertEqual(boundary, "B")
        let text = String(decoding: body, as: UTF8.self)
        XCTAssertTrue(text.contains("name=\"client_id\"\r\n\r\nme\r\n"))
        XCTAssertTrue(text.contains("filename=\"attempt.wav\"\r\nContent-Type: audio/wav\r\n\r\nRIFF\r\n--B--\r\n"))
        XCTAssertEqual(LessonClient.formEncode(["at": "3", "client_id": "me & you"]), "at=3&client_id=me%20%26%20you")
    }
}
