package com.lingualens.glasses.rf

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class BeaconParserTest {

    private fun baseAdv(
        manufacturerId: Int? = null,
        manufacturerData: ByteArray? = null,
        serviceData: Map<String, ByteArray> = emptyMap(),
        serviceUuids: List<String> = emptyList(),
        address: String = "AA:BB:CC:11:22:33"
    ) = Advertisement(
        address = address,
        name = null,
        rssi = -60,
        txPower = -59,
        isConnectable = false,
        manufacturerId = manufacturerId,
        manufacturerData = manufacturerData,
        serviceUuids = serviceUuids,
        serviceData = serviceData,
        seenAtMs = 1_700_000_000_000L
    )

    @Test
    fun parses_iBeacon_payload() {
        val data = ByteArray(23)
        data[0] = 0x02                             // iBeacon type
        data[1] = 0x15                             // length
        for (i in 0 until 16) data[2 + i] = (i * 17 + 3).toByte()   // proximity uuid
        data[18] = 0x10; data[19] = 0x00           // major = 4096
        data[20] = 0x00; data[21] = 0x42           // minor = 66
        data[22] = -59                             // calibrated tx power at 1m (signed)

        val parsed = BeaconParser.parse(baseAdv(manufacturerId = 0x004C, manufacturerData = data))

        assertEquals(EmitterKind.IBEACON, parsed.kind)
        assertEquals("Apple", parsed.vendor)
        assertEquals(-59, parsed.txPower)
        assertTrue("key should carry uuid/major/minor", parsed.key.startsWith("ibeacon:"))
        assertTrue("major/minor should be in the key", parsed.key.endsWith(":4096:66"))
        assertEquals("66", parsed.extras["minor"])
    }

    @Test
    fun parses_eddystone_uid() {
        val frame = ByteArray(18)
        frame[0] = 0x00                              // UID frame
        frame[1] = -20                               // tx power at 0m (signed)
        for (i in 0 until 10) frame[2 + i] = (0xA0 + i).toByte()   // namespace
        for (i in 0 until 6) frame[12 + i] = (0xB0 + i).toByte()   // instance

        val adv = baseAdv(serviceData = mapOf("0000feaa-0000-1000-8000-00805f9b34fb" to frame))
        val parsed = BeaconParser.parse(adv)

        assertEquals(EmitterKind.EDDYSTONE_UID, parsed.kind)
        assertEquals("Google", parsed.vendor)
        assertEquals(-20, parsed.txPower)
        assertTrue(parsed.key.startsWith("eddy-uid:"))
    }

    @Test
    fun parses_eddystone_url() {
        val frame = byteArrayOf(
            0x10,                                   // URL frame
            -20,                                    // tx power
            0x02,                                   // "http://"
            'e'.code.toByte(), 'x'.code.toByte(), 'a'.code.toByte(),
            0x07                                    // ".com" (suffix table index 7)
        )
        val adv = baseAdv(serviceData = mapOf("0000feaa-0000-1000-8000-00805f9b34fb" to frame))
        val parsed = BeaconParser.parse(adv)

        assertEquals(EmitterKind.EDDYSTONE_URL, parsed.kind)
        assertEquals("http://exa.com", parsed.label)
    }

    @Test
    fun parses_apple_findmy() {
        // 0x12 0x19 is the "offline finding" frame carried by AirTag-class
        // accessories. The trailing payload does not matter here; we only need
        // the parser to tag the frame as FIND_MY.
        val data = byteArrayOf(0x12, 0x19) + ByteArray(22)
        val parsed = BeaconParser.parse(baseAdv(manufacturerId = 0x004C, manufacturerData = data))

        assertEquals(EmitterKind.FIND_MY, parsed.kind)
        assertEquals("Apple", parsed.vendor)
    }

    @Test
    fun parses_generic_manufacturer_data() {
        val data = byteArrayOf(0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08)
        val parsed = BeaconParser.parse(baseAdv(manufacturerId = 0x0059, manufacturerData = data))

        assertEquals(EmitterKind.GENERIC_BEACON, parsed.kind)
        assertEquals("Nordic Semi", parsed.vendor)
        assertTrue(parsed.key.startsWith("man:89:"))
    }

    @Test
    fun falls_back_to_service_uuids() {
        val parsed = BeaconParser.parse(
            baseAdv(serviceUuids = listOf("0000180f-0000-1000-8000-00805f9b34fb"))
        )

        assertEquals(EmitterKind.CONNECTABLE_DEVICE, parsed.kind)
        assertTrue(parsed.key.startsWith("svc:"))
    }

    @Test
    fun detects_random_vs_static_address() {
        assertTrue("locally administered bit set", VendorDb.isRandomAddress("4A:BB:CC:11:22:33"))
        assertTrue("globally administered", !VendorDb.isRandomAddress("A4:BB:CC:11:22:33"))
    }
}
