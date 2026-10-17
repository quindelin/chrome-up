package com.lingualens.glasses.rf

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.cos

class BearingTest {

    /** A synthetic emitter at 90 degrees: rssi = base + amp*cos(theta - 90). */
    private fun sweep(
        trueAzimuth: Float,
        amplitudeDb: Float = 8f,
        baseDb: Float = -70f,
        stepDeg: Int = 10,
        count: Int = 36
    ): List<Pair<Float, Float>> {
        val points = ArrayList<Pair<Float, Float>>(count)
        var theta = 0f
        repeat(count) {
            val rad = Math.toRadians((theta - trueAzimuth).toDouble())
            points += theta to (baseDb + amplitudeDb * cos(rad).toFloat())
            theta += stepDeg
        }
        return points
    }

    @Test
    fun recovers_the_direction_of_the_lobe() {
        val fit = Bearing.fit(sweep(trueAzimuth = 90f))

        val azimuth = fit.azimuthDeg
        assertNotNull("a full sweep must produce a bearing", azimuth)
        val err = kotlin.math.abs(Bearing.wrap180(azimuth!! - 90f))
        assertTrue("bearing error was $err degrees", err < 5f)
        assertTrue("confidence was ${fit.confidence}", fit.confidence > 0.6f)
        assertEquals(12, fit.sectorsCovered)
    }

    @Test
    fun finds_a_beacon_on_the_other_side_too() {
        val fit = Bearing.fit(sweep(trueAzimuth = 250f))
        assertNotNull(fit.azimuthDeg)
        val err = kotlin.math.abs(Bearing.wrap180(fit.azimuthDeg!! - 250f))
        assertTrue("bearing error was $err degrees", err < 5f)
    }

    @Test
    fun refuses_a_bearing_when_the_user_has_not_turned() {
        // every sample in the same 30-degree sector: no angular information
        val narrow = (0..11).map { i ->
            (i * 2f) to (-70f + 8f * cos(Math.toRadians((i * 2f) - 90.0)).toFloat())
        }
        val fit = Bearing.fit(narrow)

        assertNull("must not publish a bearing from one sector", fit.azimuthDeg)
        assertEquals(0f, fit.confidence, 0.001f)
    }

    @Test
    fun refuses_a_bearing_from_too_few_samples() {
        val fit = Bearing.fit((0..5).map { i -> (i * 60f) to -70f })
        assertNull(fit.azimuthDeg)
    }

    @Test
    fun flat_signal_yields_no_direction() {
        // a device with no directional signature at all
        val flat = (0..35).map { i -> (i * 10f) to -70f }
        val fit = Bearing.fit(flat)

        assertTrue("amplitude should be ~0", fit.amplitudeDb < 0.5f)
        assertNull(fit.azimuthDeg)
    }

    @Test
    fun distance_is_sane_at_one_metre() {
        // txPower -59 at 1m, seeing -59 -> ~1m
        val d = Bearing.distanceFromRssi(-59, -59)
        assertNotNull(d)
        assertTrue("distance was $d", d!! > 0.9f && d < 1.1f)
    }

    @Test
    fun distance_grows_as_signal_drops() {
        val near = Bearing.distanceFromRssi(-60, -59)
        val far = Bearing.distanceFromRssi(-85, -59)
        assertNotNull(near)
        assertNotNull(far)
        assertTrue("far should exceed near", far!! > near!!)
    }

    @Test
    fun relative_bearing_is_positive_to_the_right() {
        // emitter due south (180), user facing east (90) -> on the right
        assertEquals(90f, Bearing.wrap180(180f - 90f), 0.001f)
        // emitter due north (0), user facing east (90) -> on the left
        assertEquals(-90f, Bearing.wrap180(0f - 90f), 0.001f)
    }
}
