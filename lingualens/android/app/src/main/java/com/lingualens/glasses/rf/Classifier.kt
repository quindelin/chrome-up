package com.lingualens.glasses.rf

/**
 * "Does this look like tracking infrastructure?"
 *
 * These are heuristics over what a transmitter *admits about itself*, not
 * detections of surveillance. The scoring is deliberately visible to the user
 * (every point added also adds a note) so the app never makes a claim it cannot
 * back up.
 *
 * The one thing no scanner can do, repeated here because it is the most common
 * misunderstanding of this whole idea: retail footfall tracking is usually done
 * by *receivers* — ceiling APs and BLE sniffers logging your phone's probe
 * requests and advertisement MACs. They transmit nothing. This classifier sees
 * transmitters only.
 */
object Classifier {

    data class Verdict(val suspicion: Float, val notes: List<String>)

    // internal: Track is an internal implementation detail of RfEngine
    internal fun assess(track: RfEngine.Track, nowMs: Long): Verdict {
        var score = 0f
        val notes = ArrayList<String>()

        if (track.kind.isPositioningInfrastructure) {
            score += 0.35f
            notes += "positioning beacon frame (iBeacon / Eddystone)"
        }

        if (track.kind == EmitterKind.FIND_MY) {
            score += 0.45f
            notes += "Apple Find My 'offline finding' frame (AirTag-class)"
        }

        if (track.staticAddress && !track.isConnectable) {
            score += 0.25f
            notes += "static MAC — same identity on every visit"
        }

        val interval = track.medianIntervalMs()
        if (interval != null && interval <= 250L) {
            score += 0.15f
            notes += "advertising every ${interval}ms — faster than a sensor needs"
        }

        if (nowMs - track.firstSeenMs > 300_000L) {
            score += 0.10f
            notes += "present for the whole visit"
        }

        return Verdict(score.coerceIn(0f, 1f), notes)
    }

    /** Observations about the site as a whole, shown under the emitter list. */
    fun siteNotes(emitters: List<Emitter>): List<String> {
        if (emitters.isEmpty()) {
            return listOf(
                "No transmitters in range.",
                "Reminder: passive receivers (ceiling APs, BLE sniffers) emit " +
                    "nothing — no scanner on any platform can see them."
            )
        }

        val notes = ArrayList<String>()
        val beacons = emitters.count { it.kind.isPositioningInfrastructure }
        if (beacons >= 6) {
            notes += "$beacons positioning beacons in range — a grid like this is an " +
                "indoor positioning deployment."
        } else if (beacons == 0) {
            notes += "No positioning beacons in range."
        }

        val findMy = emitters.count { it.kind == EmitterKind.FIND_MY }
        if (findMy > 0) {
            notes += "$findMy Find My accessory/accessories nearby — check Apple's own " +
                "unwanted-tracking alert before trusting this."
        }

        val staticMacs = emitters.count { it.staticAddress }
        if (staticMacs > 0) {
            notes += "$staticMacs device(s) use a static MAC, so they stay " +
                "identifiable across visits."
        }
        return notes
    }
}
