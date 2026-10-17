package com.lingualens.glasses.rf

/**
 * Manufacturer attribution and MAC hygiene.
 *
 * The Bluetooth company IDs below are the handful we are confident about.
 * Anything unknown returns null rather than a guess — extend the map from
 * bluetooth.com/specifications/assigned-numbers as you meet new beacons in the
 * wild. A wrong vendor label on a "you are being tracked" screen is worse than
 * no label.
 */
object VendorDb {

    private val MANUFACTURERS = mapOf(
        0x0006 to "Microsoft",
        0x004C to "Apple",
        0x0059 to "Nordic Semi",
        0x0075 to "Samsung",
        0x00E0 to "Google"
    )

    /** Bluetooth company identifier (the first two bytes of manufacturer data). */
    fun manufacturer(id: Int): String? = MANUFACTURERS[id]

    /**
     * True when the address is locally administered — i.e. randomised.
     *
     * Bit 1 of the most significant octet is the "locally administered" flag:
     *   xx:x2:xx:xx:xx:xx, xx:x6:xx, xx:xA:xx, xx:xE:xx  -> randomised
     * Phones rotate these every ~15 minutes; a static (globally administered)
     * address is what makes a device trackable across visits, so this single
     * bit is one of the strongest signals we have.
     */
    fun isRandomAddress(address: String): Boolean {
        val first = address.substringBefore(':')
        if (first.length != 2) return false
        val b = first.toIntOrNull(16) ?: return false
        return (b and 0x02) != 0
    }

    fun shortAddress(address: String): String =
        address.takeLast(5).replace(":", "")
}
