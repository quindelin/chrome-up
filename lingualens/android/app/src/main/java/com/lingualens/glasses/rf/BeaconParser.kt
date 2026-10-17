package com.lingualens.glasses.rf

/**
 * Advertisement frame parsers.
 *
 * Pure Kotlin: [BeaconParser.parse] takes primitives, so a unit test can feed it
 * byte arrays without an Android framework (see BeaconParserTest).
 *
 * Two things here are reverse-engineered rather than documented by Apple and
 * are marked INFERRED — verify them against a live capture before you rely on
 * them for anything a user would act on.
 */
object BeaconParser {

    private const val APPLE = 0x004C

    // iBeacon: Apple manufacturer data, type 0x02, length 0x15, then the payload.
    private const val IBEACON_TYPE = 0x02
    private const val IBEACON_LENGTH = 0x15

    // Eddystone lives in the 0xFEAA service.
    private const val EDDYSTONE_SERVICE = "0000feaa"

    // Apple Continuity (INFERRED type bytes, see header).
    private const val CONTINUITY_OFFLINE_FINDING = 0x12

    private val URL_PREFIXES = arrayOf("http://www.", "https://www.", "http://", "https://")
    private val URL_SUFFIXES = arrayOf(
        ".com/", ".org/", ".edu/", ".net/", ".info/", ".biz/", ".gov/",
        ".com", ".org", ".edu", ".net", ".info", ".biz", ".gov"
    )

    fun parse(adv: Advertisement): ParsedAdvertisement {
        parseEddystone(adv)?.let { return it }
        parseApple(adv)?.let { return it }
        return parseGeneric(adv)
    }

    // ---- Eddystone -------------------------------------------------------

    private fun parseEddystone(adv: Advertisement): ParsedAdvertisement? {
        val frame = adv.serviceData.entries
            .firstOrNull { isEddystone(it.key) }?.value
            ?: return null
        if (frame.isEmpty()) return null

        return when (frame[0].toInt() and 0xff) {
            0x00 -> { // UID
                if (frame.size < 18) return null
                val tx = frame[1].toInt()
                val ns = frame.copyOfRange(2, 12).hex()
                val inst = frame.copyOfRange(12, 18).hex()
                ParsedAdvertisement(
                    kind = EmitterKind.EDDYSTONE_UID,
                    key = "eddy-uid:$ns:$inst",
                    label = "Eddystone ${ns.take(8)}·${inst.take(6)}",
                    vendor = "Google",
                    txPower = tx,
                    extras = mapOf("namespace" to ns, "instance" to inst)
                )
            }
            0x10 -> { // URL
                if (frame.size < 4) return null
                val url = decodeEddystoneUrl(frame)
                ParsedAdvertisement(
                    kind = EmitterKind.EDDYSTONE_URL,
                    key = "eddy-url:$url",
                    label = url,
                    vendor = "Google",
                    txPower = frame[1].toInt()
                )
            }
            0x20 -> ParsedAdvertisement( // TLM (telemetry: battery, uptime, counters)
                kind = EmitterKind.EDDYSTONE_TLM,
                key = "eddy-tlm:${adv.address}",
                label = "Eddystone telemetry",
                vendor = "Google",
                txPower = adv.txPower
            )
            0x30 -> ParsedAdvertisement(
                kind = EmitterKind.EDDYSTONE_EID,
                key = "eddy-eid:${frame.copyOfRange(1, minOf(9, frame.size)).hex()}",
                label = "Eddystone EID",
                vendor = "Google",
                txPower = adv.txPower
            )
            else -> null
        }
    }

    private fun isEddystone(serviceUuid: String): Boolean {
        val u = serviceUuid.lowercase()
        return u.startsWith(EDDYSTONE_SERVICE) || u == "feaa"
    }

    private fun decodeEddystoneUrl(frame: ByteArray): String {
        val prefixCode = frame[2].toInt() and 0xff
        val prefix = URL_PREFIXES.getOrElse(prefixCode) { "http://" }
        return buildString {
            append(prefix)
            for (i in 3 until frame.size) {
                val b = frame[i].toInt() and 0xff
                when {
                    b < URL_SUFFIXES.size -> append(URL_SUFFIXES[b])
                    b in 0x20..0x7e -> append(b.toChar())
                    else -> append('?')
                }
            }
        }
    }

    // ---- Apple -----------------------------------------------------------

    private fun parseApple(adv: Advertisement): ParsedAdvertisement? {
        if (adv.manufacturerId != APPLE) return null
        val data = adv.manufacturerData ?: return null
        if (data.isEmpty()) return null

        // iBeacon: 0x02 0x15 <16-byte uuid> <major> <minor> <tx power at 1m>
        if (data.size >= 23 &&
            (data[0].toInt() and 0xff) == IBEACON_TYPE &&
            (data[1].toInt() and 0xff) == IBEACON_LENGTH
        ) {
            val uuid = data.uuidString(2)
            val major = data.u16be(18)
            val minor = data.u16be(20)
            val tx = data[22].toInt()
            return ParsedAdvertisement(
                kind = EmitterKind.IBEACON,
                key = "ibeacon:$uuid:$major:$minor",
                label = "iBeacon ${uuid.take(8)}·$major/$minor",
                vendor = "Apple",
                txPower = tx,
                extras = mapOf("uuid" to uuid, "major" to "$major", "minor" to "$minor")
            )
        }

        val subtype = data[0].toInt() and 0xff
        if (subtype == CONTINUITY_OFFLINE_FINDING) {
            // INFERRED: 0x12 0x19 is the "offline finding" frame carried by
            // AirTag and Find My network accessories. Apple rotates details and
            // an accessory near its owner does not emit it at all, so treat a
            // hit as "worth a second look", not as proof.
            return ParsedAdvertisement(
                kind = EmitterKind.FIND_MY,
                key = "findmy:${adv.address}",
                label = "Find My accessory",
                vendor = "Apple",
                txPower = adv.txPower,
                extras = mapOf("continuity_type" to "12")
            )
        }

        return ParsedAdvertisement(
            kind = EmitterKind.APPLE_CONTINUITY,
            key = "apple:$subtype:${adv.address}",
            label = "Apple Continuity (0x${subtype.hex2()})",
            vendor = "Apple",
            txPower = adv.txPower,
            extras = mapOf("continuity_type" to subtype.toString(16))
        )
    }

    // ---- everything else -------------------------------------------------

    private fun parseGeneric(adv: Advertisement): ParsedAdvertisement {
        val id = adv.manufacturerId
        val data = adv.manufacturerData

        if (id != null && data != null && data.isNotEmpty()) {
            val vendor = VendorDb.manufacturer(id)
            // Keyed on the manufacturer id + a prefix of the payload: the tail
            // usually carries counters that change every frame.
            return ParsedAdvertisement(
                kind = EmitterKind.GENERIC_BEACON,
                key = "man:$id:${data.copyOfRange(0, minOf(8, data.size)).hex()}",
                label = vendor?.let { "$it beacon" } ?: "Beacon 0x${id.hex4()}",
                vendor = vendor,
                txPower = adv.txPower
            )
        }

        if (adv.serviceUuids.isNotEmpty()) {
            val uuids = adv.serviceUuids.sorted()
            return ParsedAdvertisement(
                kind = EmitterKind.CONNECTABLE_DEVICE,
                key = "svc:${uuids.joinToString(",")}",
                label = adv.name ?: uuids.first().take(8),
                vendor = null,
                txPower = adv.txPower
            )
        }

        return ParsedAdvertisement(
            kind = EmitterKind.UNKNOWN,
            key = "addr:${adv.address}",
            label = adv.name ?: adv.address,
            vendor = null,
            txPower = adv.txPower
        )
    }
}

// ---- byte helpers (file-private) ------------------------------------------

private const val HEX_DIGITS = "0123456789abcdef"

internal fun ByteArray.hex(): String = buildString(size * 2) {
    for (b in this@hex) {
        val v = b.toInt() and 0xff
        append(HEX_DIGITS[v shr 4])
        append(HEX_DIGITS[v and 0x0f])
    }
}

internal fun ByteArray.u16be(offset: Int): Int =
    ((this[offset].toInt() and 0xff) shl 8) or (this[offset + 1].toInt() and 0xff)

internal fun ByteArray.uuidString(offset: Int): String {
    val h = copyOfRange(offset, offset + 16).hex()
    return "${h.substring(0, 8)}-${h.substring(8, 12)}-${h.substring(12, 16)}-" +
        "${h.substring(16, 20)}-${h.substring(20, 32)}"
}

internal fun Int.hex4(): String = (this and 0xffff).toString(16).padStart(4, '0')
internal fun Int.hex2(): String = (this and 0xff).toString(16).padStart(2, '0')
