// swift-tools-version:6.0
import PackageDescription

/// LinguaLensCore - the parts of the wrapper that are pure Swift and testable:
/// networking, 16 kHz WAV capture, haptics.
///
/// The SwiftUI app target (LinguaLensApp) lives in the Xcode project next to
/// this package; it owns the Meta Wearables DAT dependency because SPM
/// resolution of mwdat-* requires the Meta package repository.
let package = Package(
    name: "LinguaLensCore",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "LinguaLensCore", targets: ["LinguaLensCore"])
    ],
    targets: [
        .target(name: "LinguaLensCore")
    ]
)
