// swift-tools-version:6.0
import PackageDescription

/// LinguaLensCore - the parts of the iOS app that are pure Swift and testable:
/// the server's state model, the HTTP + websocket client, the per-step
/// playback plan (what app.js does in maybeSpeak / maybeAdvance), 16 kHz WAV
/// encoding and the silence endpointer for hands-free recording.
///
/// The SwiftUI app (LinguaLensApp/, built by LinguaLens.xcodeproj) owns
/// AVFoundation playback, the lock screen controls and the Meta Wearables DAT
/// dependency. macOS is listed only so `swift test` runs on the Mac.
let package = Package(
    name: "LinguaLensCore",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "LinguaLensCore", targets: ["LinguaLensCore"])
    ],
    targets: [
        .target(name: "LinguaLensCore"),
        .testTarget(
            name: "LinguaLensCoreTests",
            dependencies: ["LinguaLensCore"],
            resources: [.copy("Fixtures")]
        ),
    ],
    swiftLanguageModes: [.v5]
)
