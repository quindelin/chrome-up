import CoreVideo
import Foundation
import os
import simd
import Vision

/// Where your hands are, from the glasses camera: Apple Vision's hand pose on
/// the decoded POV frames, turned into head-relative metres for the avatar
/// (x = your right, y = up, z = forward from your face; server/body.py).
///
/// The camera is on your head, so its view *is* head-relative. Depth comes
/// from apparent size: an adult wrist-to-middle-knuckle span is ~9 cm, so how
/// wide it looks gives how far away it is, with no calibration step. The field
/// of view isn't published for the Ray-Ban Display camera; it's a setting
/// (Settings.cameraHFOV), checked once by holding a hand at arm's length.
final class HandTracker: @unchecked Sendable {
    struct Hand: Sendable { var x, y, z, conf: Double }

    /// Called on the main actor with the hands seen in one frame.
    var onHands: (@MainActor @Sendable ([String: Hand]) -> Void)?

    private let queue = DispatchQueue(label: "hands.vision", qos: .userInitiated)
    private let state = OSAllocatedUnfairLock(initialState: (busy: false, last: 0.0))
    private let interval = 1.0 / 8              // ~8 Hz: enough to follow a hand, cheap on the ANE
    private static let spanMetres = 0.09        // wrist -> middle-finger knuckle

    /// From MediaPump's frame hook (DAT's thread). Drops frames while busy.
    func push(_ pixels: CVPixelBuffer) {
        let now = ProcessInfo.processInfo.systemUptime
        let go = state.withLock { s -> Bool in
            guard !s.busy, now - s.last >= interval else { return false }
            s.busy = true; s.last = now
            return true
        }
        guard go else { return }
        let hfov = Settings.cameraHFOV
        queue.async { [weak self] in
            defer { self?.state.withLock { $0.busy = false } }
            guard let self else { return }
            let hands = Self.detect(pixels, hfovDegrees: hfov)
            let cb = self.onHands
            Task { @MainActor in cb?(hands) }
        }
    }

    private static func detect(_ pixels: CVPixelBuffer, hfovDegrees: Double) -> [String: Hand] {
        let request = VNDetectHumanHandPoseRequest()
        request.maximumHandCount = 2
        // the glasses stream portrait frames upright
        let handler = VNImageRequestHandler(cvPixelBuffer: pixels, orientation: .up, options: [:])
        do { try handler.perform([request]) } catch { return [:] }

        let w = Double(CVPixelBufferGetWidth(pixels)), h = Double(CVPixelBufferGetHeight(pixels))
        guard w > 0, h > 0 else { return [:] }
        let tanH = tan(hfovDegrees * .pi / 360)
        let tanV = tanH * h / w                  // same focal length, taller frame
        var out: [String: Hand] = [:]

        for obs in request.results ?? [] {
            guard let wrist = try? obs.recognizedPoint(.wrist),
                  let knuckle = try? obs.recognizedPoint(.middleMCP),
                  wrist.confidence > 0.3, knuckle.confidence > 0.3 else { continue }
            // Vision points are normalized, origin bottom-left
            let dx = (knuckle.location.x - wrist.location.x) * w
            let dy = (knuckle.location.y - wrist.location.y) * h
            let spanFrac = hypot(dx, dy) / w     // span as a fraction of the frame width
            guard spanFrac > 0.01 else { continue }
            let z = min(max(spanMetres / (2 * tanH * spanFrac), 0.15), 0.9)
            // aim at the palm: halfway between wrist and knuckle
            let u = (wrist.location.x + knuckle.location.x) / 2
            let v = (wrist.location.y + knuckle.location.y) / 2
            let x = (u - 0.5) * 2 * z * tanH
            let y = (v - 0.5) * 2 * z * tanV
            // Vision's chirality is which hand it is (not which side of the
            // image), so a right hand crossing to the left still reads right
            let side: String
            switch obs.chirality {
            case .left: side = "left"
            case .right: side = "right"
            default: side = u < 0.5 ? "left" : "right"
            }
            let conf = Double(min(wrist.confidence, knuckle.confidence))
            if let prev = out[side], prev.conf >= conf { continue }
            out[side] = Hand(x: x, y: y, z: z, conf: conf)
        }
        return out
    }
}
