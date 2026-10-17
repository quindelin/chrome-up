package com.lingualens.glasses.rf

import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.floor
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.pow
import kotlin.math.sin

/**
 * Bearing maths. Pure Kotlin, unit tested in BearingTest.
 *
 * READ THIS BEFORE TRUSTING A NUMBER.
 *
 * There is no angle-of-arrival on a phone. `ScanResult` hands you RSSI and
 * nothing about phase, and no consumer handset exposes IQ samples, so "which
 * direction is it coming from" cannot be measured the way a proper AoA receiver
 * measures it.
 *
 * What we can measure is *asymmetry*. The antenna is not isotropic and the
 * head/body shadows it, so as the user turns, RSSI traces a rough cosine in
 * world azimuth:
 *
 *     rssi(theta) ~= a + amp * cos(theta - phi)
 *
 * Fitting that first harmonic by least squares gives phi: the azimuth of least
 * attenuation, which is what we draw as "the direction the signal comes from".
 * It is an estimate built from body shadow and antenna pattern, not AoA. In a
 * store full of metal shelving expect +/-30-60 degrees at best.
 *
 * The glasses make this better than a phone-only app: MWDATMotion reports head
 * orientation continuously, so every glance the user makes is another sample of
 * the curve without asking them to do anything.
 */
object Bearing {

    /** Below this many (azimuth, rssi) samples we refuse to publish a bearing. */
    const val MIN_SAMPLES = 12

    /** Below this many populated 30-degree sectors, the fit is under-determined. */
    const val MIN_SECTORS = 4

    /** Oldest samples kept per emitter. */
    const val MAX_SAMPLES = 240

    /** Assumed RSSI at 1 m when a frame carries no calibrated TX power. */
    private const val DEFAULT_TX_POWER = -59

    data class Fit(
        /** World azimuth of the strongest direction. Null until the user turns enough. */
        val azimuthDeg: Float?,
        /** Depth of the fitted pattern in dB. 0 means there is no directional info at all. */
        val amplitudeDb: Float,
        /** 0..1 */
        val confidence: Float,
        val samples: Int,
        val sectorsCovered: Int
    )

    val EMPTY = Fit(null, 0f, 0f, 0, 0)

    /**
     * Log-distance path loss. Indoors this is a "same aisle / not" number: the
     * exponent is a guess and multipath moves it by metres.
     */
    fun distanceFromRssi(
        rssi: Int,
        txPower: Int?,
        pathLossExponent: Double = 2.4
    ): Float? {
        val tx = (txPower ?: DEFAULT_TX_POWER).toDouble()
        if (tx < -110.0 || tx > 20.0) return null
        if (rssi >= 0) return null
        val d = 10.0.pow((tx - rssi) / (10.0 * pathLossExponent))
        return d.toFloat().coerceIn(0.3f, 80f)
    }

    /** @param points (world azimuth in degrees, rssi in dBm) */
    fun fit(points: List<Pair<Float, Float>>): Fit {
        if (points.isEmpty()) return EMPTY

        val sectors = HashSet<Int>()
        var n = 0
        var sy = 0.0
        var sc = 0.0
        var ss = 0.0
        var syc = 0.0
        var sys = 0.0
        var scc = 0.0
        var sss = 0.0
        var scs = 0.0

        for ((azimuth, rssi) in points) {
            val a = norm360(azimuth)
            sectors.add(floor(a / 30f).toInt())
            val t = Math.toRadians(a.toDouble())
            val c = cos(t)
            val s = sin(t)
            n++
            sy += rssi
            sc += c
            ss += s
            syc += rssi * c
            sys += rssi * s
            scc += c * c
            sss += s * s
            scs += c * s
        }

        // normal equations for [a, Bc, Bs] with basis [1, cos, sin]
        val a = arrayOf(
            doubleArrayOf(n.toDouble(), sc, ss),
            doubleArrayOf(sc, scc, scs),
            doubleArrayOf(ss, scs, sss)
        )
        val b = doubleArrayOf(sy, syc, sys)
        val x = solve3(a, b) ?: return Fit(null, 0f, 0f, n, sectors.size)

        val bc = x[1]
        val bs = x[2]
        val amp = hypot(bc, bs).toFloat()
        val azimuth = norm360(Math.toDegrees(atan2(bs, bc)).toFloat())

        // residual, to separate "a real lobe" from noise
        var rss = 0.0
        for ((azimuthDeg, rssi) in points) {
            val t = Math.toRadians(norm360(azimuthDeg).toDouble())
            val predicted = x[0] + bc * cos(t) + bs * sin(t)
            val r = rssi - predicted
            rss += r * r
        }
        val rms = kotlin.math.sqrt(rss / n)

        val ampScore = (amp / 6.0).coerceIn(0.0, 1.0)
        val shapeScore = (1.0 - rms / max(amp.toDouble(), 1.0)).coerceIn(0.0, 1.0)
        val coverage = (sectors.size / 12.0).coerceIn(0.0, 1.0)
        val countScore = (n / 48.0).coerceIn(0.0, 1.0)
        val confidence = (0.40 * ampScore + 0.25 * shapeScore + 0.20 * coverage + 0.15 * countScore)
            .toFloat().coerceIn(0f, 1f)

        val usable = n >= MIN_SAMPLES && sectors.size >= MIN_SECTORS && amp >= 1.5f
        return Fit(
            azimuthDeg = if (usable) azimuth else null,
            amplitudeDb = amp,
            confidence = if (usable) confidence else 0f,
            samples = n,
            sectorsCovered = sectors.size
        )
    }

    /** Wrap to (-180, 180]. Positive means "to your right". */
    fun wrap180(deg: Float): Float {
        var d = deg % 360f
        if (d > 180f) d -= 360f
        if (d <= -180f) d += 360f
        return d
    }

    fun norm360(deg: Float): Float {
        var d = deg % 360f
        if (d < 0f) d += 360f
        return d
    }

    private fun solve3(m: Array<DoubleArray>, rhs: DoubleArray): DoubleArray? {
        for (col in 0..2) {
            var pivot = col
            for (r in col + 1..2) if (abs(m[r][col]) > abs(m[pivot][col])) pivot = r
            if (abs(m[pivot][col]) < 1e-9) return null
            if (pivot != col) {
                val tmp = m[col]; m[col] = m[pivot]; m[pivot] = tmp
                val t = rhs[col]; rhs[col] = rhs[pivot]; rhs[pivot] = t
            }
            for (r in col + 1..2) {
                val f = m[r][col] / m[col][col]
                if (f == 0.0) continue
                for (c in col..2) m[r][c] -= f * m[col][c]
                rhs[r] -= f * rhs[col]
            }
        }
        val out = DoubleArray(3)
        for (r in 2 downTo 0) {
            var s = rhs[r]
            for (c in r + 1..2) s -= m[r][c] * out[c]
            out[r] = s / m[r][r]
        }
        return out
    }
}
