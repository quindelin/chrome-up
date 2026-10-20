import Foundation
import simd

/// Spots punches in a wrist's linear acceleration (gravity removed, in g), for
/// the stream avatar (docs/BODY_TRACKING.md, "Punches").
///
/// A punch is a sharp spike: |a| crosses `threshold`, we keep the strongest
/// sample of that run and report it when the run ends (or after `maxRun`, so a
/// long spike isn't late). Then nothing until `refractory` has passed AND |a|
/// has dropped below `rearm`: the stop at full extension is a second, opposite
/// spike of the same punch and must not count again.
///
/// Kind, from the peak sample:
///   uppercut  mostly upward (against gravity)
///   straight  mostly along the forearm (jab / cross)
///   hook      mostly across it, or the wrist swinging fast about vertical
///
/// Identical copies: LiveVisionWatch/PunchDetector.swift (Watch, 100 Hz) and
/// LiveVisionApp/PunchDetector.swift (Neural Band, 60 Hz); the two targets
/// don't share a folder. Change both.
struct PunchDetector {
    struct Punch: Equatable {
        let kind: String          // straight | hook | uppercut
        let strength: Double      // 0...1 from the peak
        let peak: Double          // g
    }

    var threshold = 2.5           // g, peak a punch must reach
    var rearm = 1.2               // g, fall below this before the next one
    var refractory = 0.18         // s after a punch
    var maxRun = 0.08             // s, report a long spike this far in
    var full = 8.0                // g that counts as strength 1
    /// sensor axis along the forearm (Watch: x, crown to hand); nil if unknown
    var forearm: SIMD3<Double>?

    init(forearm: SIMD3<Double>? = nil) { self.forearm = forearm }

    private var best: (mag: Double, a: SIMD3<Double>, up: SIMD3<Double>, yawRate: Double)?
    private var runStart: Double?
    private var last = -Double.infinity
    private var armed = true

    /// - linear: acceleration without gravity, g, sensor frame
    /// - gravity: gravity in the sensor frame (points down), any scale
    /// - rotation: rotation rate, rad/s, sensor frame
    /// - t: seconds, any monotonic clock
    mutating func push(linear a: SIMD3<Double>, gravity: SIMD3<Double>,
                       rotation: SIMD3<Double>? = nil, at t: Double) -> Punch? {
        let mag = simd_length(a)
        if !armed {
            if mag < rearm, t - last >= refractory { armed = true }
            return nil
        }
        if mag >= threshold {
            if runStart == nil { runStart = t; best = nil }
            if best == nil || mag > best!.mag {
                let g = simd_length(gravity)
                let up = g > 1e-6 ? -gravity / g : SIMD3<Double>(repeating: 0)
                best = (mag, a, up, rotation.map { abs(simd_dot($0, up)) } ?? 0)
            }
            if t - runStart! < maxRun { return nil }
        } else if runStart == nil {
            return nil
        }
        // the spike is over (or long enough): report its peak
        guard let b = best else { runStart = nil; return nil }
        runStart = nil
        best = nil
        armed = false
        last = t
        return Punch(kind: Self.kind(b.a, mag: b.mag, up: b.up, yawRate: b.yawRate, forearm: forearm),
                     strength: min(1, max(0.2, 0.3 + 0.7 * (b.mag - threshold) / (full - threshold))),
                     peak: b.mag)
    }

    static func kind(_ a: SIMD3<Double>, mag: Double, up: SIMD3<Double>, yawRate: Double,
                     forearm: SIMD3<Double>?) -> String {
        let vertical = simd_dot(a, up)                       // + = upward
        if vertical > 0.55 * mag { return "uppercut" }
        if let f = forearm {
            let along = abs(simd_dot(a, simd_normalize(f)))
            if along >= 0.6 * mag { return "straight" }
            let across = (max(0, mag * mag - along * along - vertical * vertical)).squareRoot()
            if across > along || yawRate > 7 { return "hook" }
            return "straight"
        }
        return yawRate > 7 ? "hook" : "straight"             // ~400 deg/s about vertical
    }
}
