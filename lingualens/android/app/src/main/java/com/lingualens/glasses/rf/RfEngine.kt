package com.lingualens.glasses.rf

/**
 * Aggregates a firehose of advertisements into a stable list of emitters.
 *
 * Pure Kotlin and synchronous: [ingest] is called from the scanner thread and
 * [snapshot] from the UI. Callers own the concurrency (see RfScope).
 *
 * Two identities matter here and they are not the same thing:
 *   - the *track key*, which comes from the payload (iBeacon uuid/major/minor,
 *     Eddystone namespace/instance, service UUIDs). Stable across MAC rotation.
 *   - the *address*, which phones rotate every ~15 minutes. Emitters that only
 *     advertise an address therefore split into several tracks over a visit.
 *     Fixing that is a clustering problem, see docs/RF_SCOPE.md.
 */
class RfEngine(private val clock: () -> Long = { System.currentTimeMillis() }) {

    private val tracks = LinkedHashMap<String, Track>()

    /** Stop reporting an emitter this long after its last advertisement. */
    private val retainMs = 60_000L

    /** Hard cap so a busy shopping centre cannot grow this without bound. */
    private val maxTracks = 512

    private companion object {
        /** RSSI smoothing factor: 0 = frozen, 1 = no memory. */
        const val RSSI_ALPHA = 0.15
    }

    private val rssiAlpha = 0.15

    internal class Track(
        parsed: ParsedAdvertisement,
        adv: Advertisement,
        nowMs: Long
    ) {
        var kind: EmitterKind = parsed.kind
        var label: String = parsed.label
        var vendor: String? = parsed.vendor
        var txPower: Int? = parsed.txPower ?: adv.txPower
        var address: String = adv.address
        var isConnectable: Boolean = adv.isConnectable
        var staticAddress: Boolean = !VendorDb.isRandomAddress(adv.address)

        var hits: Int = 0
        var firstSeenMs: Long = nowMs
        var lastSeenMs: Long = nowMs
        var rssiEma: Double = adv.rssi.toDouble()

        /** (world azimuth, rssi) — the samples Bearing.fit consumes. */
        val points = ArrayDeque<Pair<Float, Float>>(Bearing.MAX_SAMPLES)
        val intervals = ArrayDeque<Long>(32)

        private var fit: Bearing.Fit = Bearing.EMPTY
        private var fitDirty = true

        fun update(adv: Advertisement, parsed: ParsedAdvertisement, nowMs: Long, headingDeg: Float?) {
            val gap = nowMs - lastSeenMs
            if (gap in 1..30_000) {
                intervals.addLast(gap)
                while (intervals.size > 32) intervals.removeFirst()
            }

            kind = parsed.kind
            label = parsed.label
            vendor = parsed.vendor
            txPower = parsed.txPower ?: adv.txPower
            address = adv.address
            isConnectable = adv.isConnectable
            staticAddress = !VendorDb.isRandomAddress(adv.address)

            lastSeenMs = nowMs
            rssiEma = if (hits == 0) adv.rssi.toDouble()
            else rssiEma + RSSI_ALPHA * (adv.rssi - rssiEma)
            hits++

            if (headingDeg != null) {
                points.addLast(Bearing.norm360(headingDeg) to adv.rssi.toFloat())
                while (points.size > Bearing.MAX_SAMPLES) points.removeFirst()
                fitDirty = true
            }
        }

        fun currentFit(): Bearing.Fit {
            if (fitDirty) {
                fit = Bearing.fit(points.toList())
                fitDirty = false
            }
            return fit
        }

        fun medianIntervalMs(): Long? {
            if (intervals.size < 3) return null
            val sorted = intervals.sorted()
            return sorted[sorted.size / 2]
        }

        fun toEmitter(headingDeg: Float?, nowMs: Long): Emitter {
            val f = currentFit()
            val verdict = Classifier.assess(this, nowMs)
            val relative = if (f.azimuthDeg != null && headingDeg != null) {
                Bearing.wrap180(f.azimuthDeg - headingDeg)
            } else null
            return Emitter(
                key = "", // filled by the caller, which owns the map key
                kind = kind,
                label = label,
                vendor = vendor,
                address = address,
                staticAddress = staticAddress,
                rssi = rssiEma.toInt(),
                distanceM = Bearing.distanceFromRssi(rssiEma.toInt(), txPower),
                azimuthDeg = f.azimuthDeg,
                relativeBearingDeg = relative,
                confidence = f.confidence,
                firstSeenMs = firstSeenMs,
                lastSeenMs = lastSeenMs,
                hits = hits,
                advIntervalMs = medianIntervalMs(),
                suspicion = verdict.suspicion,
                notes = verdict.notes
            )
        }
    }

    fun ingest(adv: Advertisement, headingDeg: Float?) {
        val now = clock()
        val parsed = BeaconParser.parse(adv)
        val track = tracks.getOrPut(parsed.key) { Track(parsed, adv, now) }
        track.update(adv, parsed, now, headingDeg)
        prune(now)
    }

    fun snapshot(headingDeg: Float?): RfSnapshot {
        val now = clock()
        val emitters = tracks.entries
            .filter { now - it.value.lastSeenMs <= retainMs }
            .map { (key, track) -> track.toEmitter(headingDeg, now).copy(key = key) }
            .sortedWith(compareByDescending<Emitter> { it.suspicion }.thenByDescending { it.rssi })
        return RfSnapshot(now, headingDeg, emitters, Classifier.siteNotes(emitters))
    }

    private var sincePrune = 0

    /** Drops stale tracks, then the weakest if we are over the cap. */
    private fun prune(now: Long) {
        // Rebuilding the map is O(n log n); a busy store delivers hundreds of
        // advertisements a second, so only do it occasionally.
        if (++sincePrune < 256 && tracks.size <= maxTracks) return
        sincePrune = 0
        val keep = tracks.entries
            .filter { now - it.value.lastSeenMs <= retainMs }
            .sortedWith(compareByDescending<Map.Entry<String, Track>> { it.value.rssiEma })
            .take(maxTracks)
        tracks.clear()
        keep.forEach { tracks[it.key] = it.value }
    }
}
