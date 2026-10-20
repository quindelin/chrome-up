import SwiftUI

/// The speeches bundled with the app (LiveVisionApp/Speeches/<id>.md, copied
/// from livevision/speeches on the speeches branch), grouped the way
/// livevision/speeches/manifest.json numbers them.
struct Speech: Identifiable, Hashable {
    let id: String          // "02-the-will-to-god"
    let title: String       // the file's "# " heading
    let words: Int
    let url: URL

    var number: Int { Int(id.prefix(2)) ?? 0 }

    var category: String {
        switch number {
        case 1: "Satire"
        case 2...6: "Esketian philosophy"
        case 7...11: "American mental health"
        case 12...16: "The AI economy"
        case 17...21: "Birth rates"
        default: "Famous speeches"
        }
    }

    static let all: [Speech] = {
        let urls = Bundle.main.urls(forResourcesWithExtension: "md", subdirectory: nil) ?? []
        return urls.compactMap { url in
            let id = url.deletingPathExtension().lastPathComponent
            guard id.range(of: #"^\d{2}-"#, options: .regularExpression) != nil,
                  let text = try? String(contentsOf: url, encoding: .utf8) else { return nil }
            let title = text.split(separator: "\n").first { $0.hasPrefix("# ") }
                .map { String($0.dropFirst(2)) } ?? id
            let words = text.split(whereSeparator: \.isWhitespace).count
            return Speech(id: id, title: title, words: words, url: url)
        }
        .sorted { $0.id < $1.id }
    }()
}

/// Scroll, tap, and the speech is the teleprompter's script.
struct SpeechLibraryView: View {
    @Environment(Teleprompter.self) private var p
    @Environment(\.dismiss) private var dismiss

    private var groups: [(String, [Speech])] {
        var order: [String] = []
        var byCategory: [String: [Speech]] = [:]
        for s in Speech.all {
            if byCategory[s.category] == nil { order.append(s.category) }
            byCategory[s.category, default: []].append(s)
        }
        return order.map { ($0, byCategory[$0] ?? []) }
    }

    var body: some View {
        List {
            if Speech.all.isEmpty {
                Text("No speeches are bundled in this build.").foregroundStyle(.secondary)
            }
            ForEach(groups, id: \.0) { category, speeches in
                Section(category) {
                    ForEach(speeches) { s in
                        Button { load(s) } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(s.title).foregroundStyle(.primary)
                                    Text("\(s.number) · \(TeleprompterView.clock(Double(s.words) / Double(p.wordsPerMinute) * 60)) at \(p.wordsPerMinute) wpm")
                                        .font(.caption).foregroundStyle(.secondary)
                                }
                                Spacer()
                                if p.scriptTitle == s.title {
                                    Image(systemName: "checkmark").foregroundStyle(.tint)
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Speeches")
    }

    private func load(_ s: Speech) {
        guard let text = try? String(contentsOf: s.url, encoding: .utf8) else { return }
        p.script = text
        dismiss()
    }
}
