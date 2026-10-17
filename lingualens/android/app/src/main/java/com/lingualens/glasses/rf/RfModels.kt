package com.lingualens.glasses.rf

/**
 * RF Scope — data model.
 *
 * Deliberately free of Android imports so the whole classification / bearing
 * pipeline can be unit tested on the JVM (see app/src/test).
 *
 * The honest scope of this model, stated once so no call site over-claims:
 * it describes *transmitters*. Anything that only listens (a ceiling Wi-Fi AP
 * logging probe requests, a BLE sniffer in a shelf) emits nothing and is
 * invisible to every API on the platform. See docs/RF_SCOPE.md.
 */

enum class EmitterKind {
    /** Apple iBeacon frame — the protocol most retail beacon grids speak. */
    IBEACON,

    EDDYSTONE_UID,
    EDDYSTONE_URL,
    EDDYSTONE_TLM,
    EDDYSTONE_EID,

    /** Apple "offline finding" frame — AirTag / Find My network accessory. */
    FIND_MY,

    /** Some other Apple Continuity frame (handoff, AirDrop, AirPods, nearby). */
    APPLE_CONTINUITY,

    /** Advertises manufacturer data we could not attribute to a beacon format. */
    GENERIC_BEACON,

    /** Advertises only service UUIDs — phones, watches, earbuds, laptops. */
    CONNECTABLE_DEVICE,

    UNKNOWN;

    /** Frames whose whole purpose is "know where things are". */
    val isPositioningInfrastructure: Boolean
        get() = this == IBEACON || this == EDDYSTONE_UID || this == EDDYSTONE_URL

    /** Short badge for the 600x600 display, which has very little room. */
    val short: String
        get() = when (this) {
            IBEACON -> "beacon"
            EDDYSTONE_UID, EDDYSTONE_URL, EDDYSTONE_TLM, EDDYSTONE_EID -> "eddystone"
            FIND_MY -> "find-my"
            APPLE_CONTINUITY -> "apple"
            GENERIC_BEACON -> "ble"
            CONNECTABLE_DEVICE -> "device"
            UNKNOWN -> "?"
        }
}

/**
 * One raw advertisement, normalised so the parser never touches Android types.
 */
data class Advertisement(
    val address: String,
    val name: String?,
    val rssi: Int,
    val txPower: Int?,
    val isConnectable: Boolean,
    val manufacturerId: Int?,
    val manufacturerData: ByteArray?,
    val serviceUuids: List<String>,
    val serviceData: Map<String, ByteArray>,
    val seenAtMs: Long
)

/** What [BeaconParser] made of an [Advertisement]. */
data class ParsedAdvertisement(
    val kind: EmitterKind,
    /** Stable identity across advertisements and across MAC randomisation, where possible. */
    val key: String,
    val label: String,
    val vendor: String?,
    /** Calibrated RSSI at 1 metre, if the frame carries one. */
    val txPower: Int?,
    val extras: Map<String, String> = emptyMap()
)

/**
 * One tracked transmitter, after aggregation.
 *
 * [azimuthDeg] is a world-frame compass direction; [relativeBearingDeg] is the
 * same thing expressed against where the user is currently facing
 * (0 = straight ahead, positive = to the right).
 */
data class Emitter(
    val key: String,
    val kind: EmitterKind,
    val label: String,
    val vendor: String?,
    val address: String,
    /** False = the address is randomised, so this device cannot be re-identified tomorrow. */
    val staticAddress: Boolean,
    /** Smoothed RSSI, dBm. */
    val rssi: Int,
    /** Log-distance estimate. Indoor accuracy is roughly "same room / not". */
    val distanceM: Float?,
    /** World azimuth of the least-attenuated direction; null until the user turns enough. */
    val azimuthDeg: Float?,
    val relativeBearingDeg: Float?,
    /** 0..1 — how much we trust [relativeBearingDeg]. */
    val confidence: Float,
    val firstSeenMs: Long,
    val lastSeenMs: Long,
    val hits: Int,
    /** Median advertisement interval, milliseconds. Fast = asset tracker / RTLS tag. */
    val advIntervalMs: Long?,
    /** 0..1 — "this looks like tracking infrastructure". See Classifier. */
    val suspicion: Float,
    val notes: List<String>
)

data class RfSnapshot(
    val atMs: Long,
    /** Where the user is facing, degrees from magnetic north. Null = no motion sensor. */
    val headingDeg: Float?,
    val emitters: List<Emitter>,
    val notes: List<String> = emptyList()
) {
    val total: Int get() = emitters.size

    companion object {
        fun empty(atMs: Long = 0L) =
            RfSnapshot(atMs, null, emptyList(), listOf("Starting scan…"))
    }
}
