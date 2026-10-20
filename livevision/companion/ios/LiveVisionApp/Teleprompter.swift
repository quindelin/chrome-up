import Foundation
import MWDATCore
import MWDATDisplay
import MWDATInputs

/// A teleprompter on the Ray-Ban Display lens, through LiveVision's own DAT
/// session: the glasses allow one session at a time, and ours already holds
/// the camera, so a separate teleprompter app can't connect while we stream.
/// DeviceSession takes a Display beside the Camera, so the script goes out on
/// the same link.
///
/// The script is paged on the phone (DAT has no partial updates: every send
/// replaces the whole view). The lens dims after 20 s without a send and
/// sleeps at 25 s, so the current page is re-sent every 12 s.
///
/// Advance: swipe / D-pad on the Neural Band or temple (MWDATInputs, still
/// experimental in DAT 1.0), a tap on the lens, the phone, or auto-scroll at
/// the speaking rate.
///
/// No SwiftUI here: MWDATDisplay's Text/Button would clash with SwiftUI's.
@MainActor
@Observable
final class Teleprompter {
    struct Page: Equatable {
        let section: String
        let text: String
        let words: Int
    }

    enum Lens: Equatable {
        case off
        case waiting        // asked to show, no glasses session yet
        case starting
        case showing
        case failed(String)
    }

    private(set) var pages: [Page] = []
    private(set) var index = 0
    private(set) var lens: Lens = .off
    /// Advance by itself at `wordsPerMinute`.
    private(set) var autoScroll = false
    /// The last input the glasses reported, for the status line.
    private(set) var lastInput: String?

    var script: String {
        didSet {
            guard script != oldValue else { return }
            Self.defaults.set(script, forKey: "prompter.script")
            repaginate(keepingWord: false)
        }
    }
    var wordsPerMinute: Int {
        didSet { Self.defaults.set(wordsPerMinute, forKey: "prompter.wpm"); restartAuto() }
    }
    var wordsPerPage: Int {
        didSet {
            guard wordsPerPage != oldValue else { return }
            Self.defaults.set(wordsPerPage, forKey: "prompter.wordsPerPage")
            repaginate(keepingWord: true)
        }
    }

    var page: Page? { pages.indices.contains(index) ? pages[index] : nil }
    var totalWords: Int { pages.reduce(0) { $0 + $1.words } }
    /// Spoken time left from the start of the current page.
    var remaining: TimeInterval {
        let left = pages.dropFirst(index).reduce(0) { $0 + $1.words }
        return Double(left) / Double(max(wordsPerMinute, 1)) * 60
    }
    var wantsLens: Bool { lens != .off }

    @ObservationIgnored private static let defaults = UserDefaults.standard
    @ObservationIgnored private var display: Display?
    @ObservationIgnored private var inputs: Inputs?
    @ObservationIgnored private weak var attachedTo: DeviceSession?
    @ObservationIgnored private var tokens = ListenerTokenBag()
    @ObservationIgnored private var inputTask: Task<Void, Never>?
    @ObservationIgnored private var keepAwake: Task<Void, Never>?
    @ObservationIgnored private var autoTask: Task<Void, Never>?

    init() {
        script = Self.defaults.string(forKey: "prompter.script") ?? ""
        let wpm = Self.defaults.integer(forKey: "prompter.wpm")
        wordsPerMinute = wpm > 0 ? wpm : 140
        let wpp = Self.defaults.integer(forKey: "prompter.wordsPerPage")
        wordsPerPage = wpp > 0 ? wpp : 40
        repaginate(keepingWord: false)
        index = min(Self.defaults.integer(forKey: "prompter.index"), max(pages.count - 1, 0))
    }

    // MARK: - navigation

    func next() { go(to: index + 1) }
    func previous() { go(to: index - 1) }

    func go(to i: Int) {
        guard !pages.isEmpty else { return }
        let clamped = min(max(i, 0), pages.count - 1)
        guard clamped != index else { return }
        index = clamped
        Self.defaults.set(index, forKey: "prompter.index")
        sendPage()
        restartAuto()
    }

    func toggleAuto() {
        autoScroll.toggle()
        restartAuto()
        sendPage()
    }

    // MARK: - the lens

    /// "Show on glasses": attaches once the glasses session is up (connecting
    /// it if needed) and keeps re-attaching after reconnects until `hide()`.
    func show(on glasses: GlassesStreamer) {
        if lens == .off || lens.isFailure { lens = .waiting }
        if glasses.link == .idle || glasses.link == .unregistered { glasses.connect() }
        sessionChanged(glasses)
    }

    func hide() {
        lens = .off
        detach()
    }

    /// Call when the glasses link changes (connect, pause, reconnect).
    func sessionChanged(_ glasses: GlassesStreamer) {
        guard wantsLens else { return }
        guard glasses.link == .connected, let session = glasses.deviceSession else {
            if glasses.deviceSession == nil, attachedTo != nil { detach(); lens = .waiting }
            return
        }
        if session === attachedTo, display != nil { return }
        attach(to: session)
    }

    private func attach(to session: DeviceSession) {
        detach()
        lens = .starting
        attachedTo = session
        let d: Display
        do {
            d = try session.addDisplay()
        } catch {
            lens = .failed("No lens: \(error.localizedDescription). The teleprompter needs Meta Ray-Ban Display glasses.")
            log.error("addDisplay: \(String(describing: error))")
            return
        }
        display = d
        d.statePublisher.listen { [weak self] state in
            Task { @MainActor in self?.displayChanged(state) }
        }.store(in: tokens)
        d.start()
        if d.state == .started { displayChanged(.started) }

        // Neural Band / temple swipes. Experimental in DAT: without it the
        // lens tap, the phone and auto-scroll still work.
        do {
            if let i = try session.addInputs() {
                inputs = i
                inputTask = Task { [weak self] in
                    for await event in i.events { self?.handle(event) }
                }
            }
        } catch {
            log.notice("inputs unavailable: \(String(describing: error))")
        }
    }

    private func detach() {
        keepAwake?.cancel(); keepAwake = nil
        inputTask?.cancel(); inputTask = nil
        display?.stop()
        display = nil
        if inputs != nil { try? attachedTo?.removeInputs() }
        inputs = nil
        attachedTo = nil
        let old = tokens
        tokens = ListenerTokenBag()
        Task { await old.cancelAll() }
    }

    private func displayChanged(_ state: DisplayState) {
        switch state {
        case .started:
            lens = .showing
            sendPage()
            startKeepAwake()
        case .stopped:
            // the wearer ended it (two-finger tap) or the session went away
            keepAwake?.cancel(); keepAwake = nil
            display = nil
            if lens == .showing || lens == .starting { lens = .waiting }
        case .starting, .stopping:
            break
        }
    }

    private func handle(_ event: InputEvent) {
        switch event {
        case .nav(let dir, let source, _):
            lastInput = "\(dir) · \(source)"
            switch dir {
            case .right, .down: next()
            case .left, .up: previous()
            @unknown default: break
            }
        case .select(let source, _):
            lastInput = "select · \(source)"
            toggleAuto()
        case .back(let source, _):
            lastInput = "back · \(source)"
            previous()
        default:
            break
        }
    }

    private func startKeepAwake() {
        keepAwake?.cancel()
        keepAwake = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(12))
                self?.sendPage()
            }
        }
    }

    private func sendPage() {
        guard let display, lens == .showing else { return }
        let view = lensView()
        Task {
            do { try await display.send(view) }
            catch { log.error("display send: \(String(describing: error))") }
        }
    }

    private func lensView() -> FlexBox {
        let header: String
        if let page {
            let section = page.section.isEmpty ? "" : "\(page.section) · "
            header = "\(section)\(index + 1)/\(pages.count)\(autoScroll ? " · auto" : "")"
        } else {
            header = "Teleprompter"
        }
        let body = page?.text ?? "Paste a script in LiveVision's Prompter tab."
        return FlexBox(direction: .column, spacing: 10, padding: EdgeInsets(all: 12)) {
            Text(header, style: .meta, color: .secondary)
            Text(body, style: .body)
        }
        .onTap { [weak self] in Task { @MainActor in self?.next() } }
    }

    // MARK: - auto-scroll

    private func restartAuto() {
        autoTask?.cancel()
        guard autoScroll, let page else { autoTask = nil; return }
        let seconds = Double(page.words) / Double(max(wordsPerMinute, 1)) * 60
        autoTask = Task { [weak self] in
            try? await Task.sleep(for: .seconds(max(seconds, 1.5)))
            guard !Task.isCancelled, let self else { return }
            if self.index + 1 < self.pages.count { self.next() } else { self.autoScroll = false; self.sendPage() }
        }
    }

    // MARK: - paging

    private func repaginate(keepingWord: Bool) {
        let wordBefore = pages.prefix(index).reduce(0) { $0 + $1.words }
        pages = Self.paginate(script, wordsPerPage: wordsPerPage)
        if keepingWord {
            var count = 0, i = 0
            while i < pages.count - 1, count + pages[i].words <= wordBefore { count += pages[i].words; i += 1 }
            index = i
        } else {
            index = 0
        }
        Self.defaults.set(index, forKey: "prompter.index")
        sendPage()
        restartAuto()
    }

    /// Markdown speech -> pages of about `wordsPerPage` words. `#` headings
    /// become the page's section label; paragraphs stay whole when they fit,
    /// long ones break at sentence ends, and only a single overlong sentence
    /// is cut mid-sentence. Cue lines like [PAUSE] stay in the text.
    nonisolated static func paginate(_ script: String, wordsPerPage: Int) -> [Page] {
        let limit = max(wordsPerPage, 5)
        var pages: [Page] = []
        var section = ""
        var chunks: [String] = []   // paragraphs on the page being built
        var line: [String] = []     // words of the paragraph being built
        var count = 0

        func flush() {
            if !line.isEmpty { chunks.append(line.joined(separator: " ")); line = [] }
            guard count > 0 else { return }
            pages.append(Page(section: section, text: chunks.joined(separator: "\n\n"), words: count))
            chunks = []; count = 0
        }

        let blocks = script.replacingOccurrences(of: "\r\n", with: "\n")
            .components(separatedBy: "\n\n")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        for block in blocks {
            if block.hasPrefix("#") {
                flush()
                let title = block.split(separator: "\n").first.map(String.init) ?? block
                section = title.drop(while: { $0 == "#" || $0 == " " }).trimmingCharacters(in: .whitespaces)
                if section.count > 40 { section = String(section.prefix(39)) + "…" }
                continue
            }
            let plain = block.replacingOccurrences(of: "**", with: "")
                .replacingOccurrences(of: "\n", with: " ")
            let words = plain.split(whereSeparator: \.isWhitespace).map(String.init)
            guard !words.isEmpty else { continue }
            if count > 0, count + words.count > limit { flush() }
            if words.count <= limit - count {
                chunks.append(words.joined(separator: " ")); count += words.count
                continue
            }
            // too long for one page: sentence by sentence
            for sentence in sentences(words) {
                if count > 0, count + sentence.count > limit { flush() }
                for w in sentence {
                    if count >= limit { flush() }
                    line.append(w); count += 1
                }
            }
            if !line.isEmpty { chunks.append(line.joined(separator: " ")); line = [] }
        }
        flush()
        return pages
    }

    nonisolated private static func sentences(_ words: [String]) -> [[String]] {
        var out: [[String]] = [], cur: [String] = []
        for w in words {
            cur.append(w)
            let end = w.trimmingCharacters(in: CharacterSet(charactersIn: "\"'”’)]"))
            if end.hasSuffix(".") || end.hasSuffix("?") || end.hasSuffix("!") { out.append(cur); cur = [] }
        }
        if !cur.isEmpty { out.append(cur) }
        return out
    }
}

private extension Teleprompter.Lens {
    var isFailure: Bool { if case .failed = self { return true } else { return false } }
}
