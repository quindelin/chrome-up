import MapKit
import SwiftUI

/// Pick a destination the way Apple Maps' search does: suggestions as you type
/// (MKLocalSearchCompleter, biased to where you are), saved and recent places,
/// or a maps link from the clipboard. Picking one starts RouteNavigator.
struct DestinationSearchView: View {
    @Environment(RouteNavigator.self) private var nav
    @Environment(\.dismiss) private var dismiss
    @State private var search = PlaceSearch()
    @State private var query = ""
    @State private var busy = false
    @State private var error: String?

    var body: some View {
        @Bindable var nav = nav
        List {
            Section {
                Picker("Directions", selection: $nav.transport) {
                    ForEach(RouteNavigator.Transport.allCases) { Text($0.label).tag($0) }
                }
                .pickerStyle(.segmented)
                if let error {
                    Text(error).font(.caption).foregroundStyle(.orange)
                }
            }

            if query.trimmingCharacters(in: .whitespaces).isEmpty {
                Section {
                    PasteButton(payloadType: String.self) { strings in
                        if let text = strings.first { go(text) }
                    }
                } footer: {
                    Text("Or from Apple Maps: open a place, tap Share, then LiveVision.")
                }
                let saved = nav.places.filter(\.saved)
                if !saved.isEmpty {
                    Section("Saved") { ForEach(saved) { placeRow($0) } }
                }
                let recent = nav.places.filter { !$0.saved }
                if !recent.isEmpty {
                    Section("Recent") { ForEach(recent) { placeRow($0) } }
                }
            } else {
                Section {
                    if query.contains("://") {
                        Button { go(query) } label: { Label("Open this link", systemImage: "link") }
                    }
                    ForEach(search.results, id: \.self) { completion in
                        Button { pick(completion) } label: {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(completion.title).foregroundStyle(.primary)
                                if !completion.subtitle.isEmpty {
                                    Text(completion.subtitle).font(.caption).foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                    if !query.contains("://") {
                        Button { go(query) } label: {
                            Label("Search for “\(query)”", systemImage: "magnifyingglass")
                        }
                    }
                }
            }
        }
        .overlay { if busy { ProgressView().controlSize(.large) } }
        .disabled(busy)
        .searchable(text: $query, placement: .navigationBarDrawer(displayMode: .always),
                    prompt: "Place, address or maps link")
        .autocorrectionDisabled()
        .onChange(of: query) { search.update(query, near: nav.here) }
        .onSubmit(of: .search) { go(query) }
        .navigationTitle("Destination")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func placeRow(_ place: RouteNavigator.Place) -> some View {
        Button {
            run { await nav.navigate(to: place.coordinate, name: place.name) }
        } label: {
            Label(place.name, systemImage: place.saved ? "star.fill" : "clock")
                .foregroundStyle(.primary)
        }
        .swipeActions(edge: .trailing) {
            Button(role: .destructive) { nav.forget(place) } label: { Label("Remove", systemImage: "trash") }
        }
        .swipeActions(edge: .leading) {
            Button { nav.toggleSaved(place) } label: {
                Label(place.saved ? "Unsave" : "Save", systemImage: place.saved ? "star.slash" : "star")
            }
            .tint(.yellow)
        }
    }

    private func pick(_ completion: MKLocalSearchCompletion) {
        run {
            let response = try await MKLocalSearch(request: MKLocalSearch.Request(completion: completion)).start()
            guard let item = response.mapItems.first else { throw RouteNavigator.PlaceError.notFound(completion.title) }
            await nav.navigate(to: item.placemark.coordinate, name: item.name ?? completion.title)
        }
    }

    private func go(_ text: String) {
        let t = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !t.isEmpty else { return }
        run { try await nav.navigate(to: t) }
    }

    private func run(_ action: @escaping () async throws -> Void) {
        Task {
            busy = true
            error = nil
            defer { busy = false }
            do {
                try await action()
                dismiss()
            } catch {
                self.error = error.localizedDescription
            }
        }
    }
}

/// Apple Maps' as-you-type suggestions.
@MainActor
@Observable
final class PlaceSearch: NSObject, MKLocalSearchCompleterDelegate {
    private(set) var results: [MKLocalSearchCompletion] = []
    @ObservationIgnored private let completer = MKLocalSearchCompleter()

    override init() {
        super.init()
        completer.delegate = self
        completer.resultTypes = [.address, .pointOfInterest]
    }

    func update(_ query: String, near: CLLocationCoordinate2D?) {
        let q = query.trimmingCharacters(in: .whitespaces)
        guard !q.isEmpty, !q.contains("://") else {
            completer.cancel()
            results = []
            return
        }
        if let near {
            completer.region = MKCoordinateRegion(center: near, latitudinalMeters: 30_000, longitudinalMeters: 30_000)
        }
        completer.queryFragment = q
    }

    nonisolated func completerDidUpdateResults(_ completer: MKLocalSearchCompleter) {
        let found = Array(completer.results.prefix(8))
        Task { @MainActor in self.results = found }
    }

    nonisolated func completer(_ completer: MKLocalSearchCompleter, didFailWithError error: Error) {
        Task { @MainActor in self.results = [] }
    }
}
