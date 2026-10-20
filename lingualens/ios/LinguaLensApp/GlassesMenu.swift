import Foundation
import LinguaLensCore
import MWDATDisplay

/// The screens on the glasses, and how you move between them.
///
/// The phone is the source of truth for navigation (DAT keeps no state on
/// the glasses), so this holds the current screen and redraws it in full on
/// every change. The layout follows Meta's display guidance: a root screen
/// (Home) you can always get back to, lists of buttons, and the controls you
/// need most at the TOP - the display scrolls vertically, and controls at
/// the bottom of a long lesson card were below the fold.
///
///     Home ─┬─ Continue ─────────────▶ Lesson  (Menu · Redo · Start/Stop · Skip)
///           ├─ Review · N due ───────▶ Lesson
///           ├─ Lessons ─▶ Level ─▶ Lesson list ─▶ Lesson
///           └─ Course ──▶ Mandarin / Japanese / Spanish ─▶ Home
@MainActor
final class GlassesMenu {
    enum Screen: Equatable {
        case home
        case levels
        case lessons(levelIndex: Int)
        case courses
        case lesson
    }

    private(set) var screen: Screen = .home
    private weak var store: SessionStore?
    private var tree: CourseTree?
    private var treeCourse: String?
    private var loading = false

    init(store: SessionStore) {
        self.store = store
    }

    // MARK: navigation

    func go(_ next: Screen) {
        screen = next
        if case .lessons = next { loadTree() }
        if next == .levels { loadTree() }
        render()
    }

    /// The lesson is running (started from the phone, the glasses or voice).
    func showLesson() { go(.lesson) }

    /// A new state snapshot: only the lesson screen follows it. A menu you
    /// are reading is not yanked away because the lesson moved on.
    func update() {
        if let active = store?.state?.active, active != treeCourse { tree = nil }
        if screen == .lesson || screen == .home { render() }
    }

    func render() {
        guard let store else { return }
        let view: FlexBox
        switch screen {
        case .home: view = home(store)
        case .levels: view = levels(store)
        case .lessons(let i): view = lessons(store, levelIndex: i)
        case .courses: view = courses(store)
        case .lesson: view = lesson(store)
        }
        store.glasses.present(view)
    }

    // MARK: screens

    private func home(_ store: SessionStore) -> FlexBox {
        let s = store.state
        let course = [s?.native, s?.languageName].compactMap { $0 }.joined(separator: " · ")
        let due = s?.reviewDue ?? 0
        let current = s?.lesson.map { "L\($0.id) · \($0.title ?? "")" } ?? "No lesson yet"
        return FlexBox(direction: .column, spacing: 10, padding: EdgeInsets(all: 16)) {
            Text("LinguaLens" + (course.isEmpty ? "" : " · \(course)"), style: .heading)
            Text(current, style: .body)
            Button(label: store.isPlaying ? "Back to lesson" : "Continue", style: .primary,
                   onClick: act { [weak self] in
                       self?.store?.play()
                       self?.go(.lesson)
                   })
            Button(label: due > 0 ? "Review · \(due) due" : "Review", style: .secondary,
                   onClick: act { [weak self] in
                       self?.store?.startReview()
                       self?.store?.play()
                       self?.go(.lesson)
                   })
            Button(label: "Lessons", style: .secondary, onClick: act { [weak self] in self?.go(.levels) })
            Button(label: "Course", style: .outline, onClick: act { [weak self] in self?.go(.courses) })
        }
    }

    private func levels(_ store: SessionStore) -> FlexBox {
        let levels = tree?.levels ?? []
        return FlexBox(direction: .column, spacing: 8, padding: EdgeInsets(all: 16)) {
            Button(label: "‹ Home", style: .outline, onClick: act { [weak self] in self?.go(.home) })
            Text("Choose a level", style: .heading)
            if levels.isEmpty {
                Text(loading ? "Loading…" : "Couldn't load the course - check the phone", style: .body)
            }
            for (i, level) in levels.enumerated() {
                Button(label: [level.code, level.title].compactMap { $0 }.joined(separator: " · "),
                       style: .secondary,
                       onClick: act { [weak self] in self?.go(.lessons(levelIndex: i)) })
            }
        }
    }

    private func lessons(_ store: SessionStore, levelIndex: Int) -> FlexBox {
        let level = (tree?.levels ?? []).indices.contains(levelIndex) ? tree?.levels[levelIndex] : nil
        let current = store.state?.lesson?.id
        let all = level?.units.flatMap(\.lessons) ?? []
        return FlexBox(direction: .column, spacing: 8, padding: EdgeInsets(all: 16)) {
            Button(label: "‹ Levels", style: .outline, onClick: act { [weak self] in self?.go(.levels) })
            Text(level?.code ?? "Lessons", style: .heading)
            for lesson in all {
                Button(label: (lesson.id == current ? "▸ " : "") + "L\(lesson.id) · \(lesson.title ?? "")",
                       style: lesson.id == current ? .primary : .secondary,
                       onClick: act { [weak self] in
                           self?.store?.startLesson(lesson.id)
                           self?.store?.play()
                           self?.go(.lesson)
                       })
            }
        }
    }

    private func courses(_ store: SessionStore) -> FlexBox {
        let rows = store.state?.courses ?? []
        return FlexBox(direction: .column, spacing: 8, padding: EdgeInsets(all: 16)) {
            Button(label: "‹ Home", style: .outline, onClick: act { [weak self] in self?.go(.home) })
            Text("Course", style: .heading)
            for c in rows where c.ready {
                Button(label: "\(c.native ?? c.id) · \(c.name ?? "")" + (c.active ? "  ✓" : ""),
                       style: c.active ? .primary : .secondary,
                       onClick: act { [weak self] in
                           self?.store?.selectCourse(c.id)
                           self?.tree = nil
                           self?.go(.home)
                       })
            }
        }
    }

    private func lesson(_ store: SessionStore) -> FlexBox {
        let card = store.state?.glasses ?? .fallback(for: store.state?.step)
        let playing = store.isPlaying
        return FlexBox(direction: .column, spacing: 10, padding: EdgeInsets(all: 16)) {
            // controls first: always on screen, never below the fold
            ButtonGroup {
                Button(label: "Menu", style: .outline, onClick: act { [weak self] in self?.go(.home) })
                Button(label: "Redo", style: .outline, onClick: act { [weak self] in self?.store?.repeatLine() })
                Button(label: playing ? "Stop" : "Start", style: .primary, onClick: act { [weak self] in
                    guard let store = self?.store else { return }
                    store.isPlaying ? store.pause() : store.play()
                })
                Button(label: "Skip", style: .outline, onClick: act { [weak self] in self?.store?.next() })
            }
            if !card.header.isEmpty { Text(card.header, style: .meta) }
            if !card.cue.isEmpty { Text(card.cue, style: .body) }
            Text(card.target.isEmpty ? " " : card.target, style: .heading)
            if !card.reading.isEmpty { Text(card.reading, style: .body) }
            if !card.english.isEmpty { Text(card.english, style: .body) }
            if !card.footer.isEmpty { Text(card.footer, style: .body) }
        }
    }

    // MARK: data

    private func loadTree() {
        guard tree == nil, !loading, let store, let client = store.client else { return }
        loading = true
        let course = store.state?.active ?? ""
        Task { [weak self] in
            let t = try? await client.course(course)
            guard let self else { return }
            self.loading = false
            self.tree = t
            self.treeCourse = course
            self.render()
        }
    }

    /// A display button's handler. DAT calls it off the main actor.
    private func act(_ f: @escaping @MainActor @Sendable () -> Void) -> @Sendable () -> Void {
        { Task { @MainActor in f() } }
    }
}
