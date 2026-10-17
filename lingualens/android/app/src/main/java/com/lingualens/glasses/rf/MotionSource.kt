package com.lingualens.glasses.rf

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin

/**
 * Where is the user facing? Every bearing this app reports is relative to this.
 *
 * [PhoneMotionSource] is the fallback and works today. [DatMotionSource] is the
 * one that makes the feature good: MWDATMotion streams the *glasses'*
 * orientation, so the heading matches where the user is actually looking
 * (and the head turns far more often than a phone in a pocket, which means the
 * bearing fit converges much faster).
 */
interface MotionSource {
    fun start()
    fun stop()

    /** Degrees from magnetic north, 0..360. Null when unavailable. */
    fun headingDeg(): Float?
}

/**
 * Phone rotation vector -> compass heading.
 *
 * Uses TYPE_ROTATION_VECTOR when the device has it (fused, already compensated)
 * and falls back to accelerometer + magnetometer. Azimuth is smoothed as a
 * circular mean, because averaging raw degrees breaks at the 0/360 seam.
 *
 * Note: with the phone in a pocket or held at an angle the azimuth is still a
 * valid world-frame heading, which is all Bearing.fit needs. It does not need
 * to be the direction the user's nose points.
 */
class PhoneMotionSource(context: Context) : MotionSource, SensorEventListener {

    private val sensors = context.getSystemService(Context.SENSOR_SERVICE) as? SensorManager
    private val rotation = sensors?.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
    private val accel = sensors?.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    private val magnet = sensors?.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD)

    private val matrix = FloatArray(9)
    private val orientation = FloatArray(3)
    private val lastAccel = FloatArray(3)
    private val lastMag = FloatArray(3)

    private var sinMean = 0.0
    private var cosMean = 0.0
    private var primed = false

    private val alpha = 0.15f

    override fun start() {
        val s = sensors ?: return
        if (rotation != null) {
            s.registerListener(this, rotation, SensorManager.SENSOR_DELAY_UI)
        } else {
            if (accel != null) s.registerListener(this, accel, SensorManager.SENSOR_DELAY_UI)
            if (magnet != null) s.registerListener(this, magnet, SensorManager.SENSOR_DELAY_UI)
        }
    }

    override fun stop() {
        runCatching { sensors?.unregisterListener(this) }
        primed = false
    }

    override fun headingDeg(): Float? = if (primed) {
        Bearing.norm360(Math.toDegrees(atan2(sinMean, cosMean)).toFloat())
    } else null

    override fun onSensorChanged(event: SensorEvent) {
        when (event.sensor.type) {
            Sensor.TYPE_ROTATION_VECTOR -> {
                SensorManager.getRotationMatrixFromVector(matrix, event.values)
                publish(matrix)
            }
            Sensor.TYPE_ACCELEROMETER -> {
                System.arraycopy(event.values, 0, lastAccel, 0, 3)
                publishFromRaw()
            }
            Sensor.TYPE_MAGNETIC_FIELD -> {
                System.arraycopy(event.values, 0, lastMag, 0, 3)
                publishFromRaw()
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit

    private fun publishFromRaw() {
        if (lastAccel[0] == 0f && lastAccel[1] == 0f && lastAccel[2] == 0f) return
        if (lastMag[0] == 0f && lastMag[1] == 0f && lastMag[2] == 0f) return
        if (SensorManager.getRotationMatrix(matrix, null, lastAccel, lastMag)) publish(matrix)
    }

    private fun publish(rotationMatrix: FloatArray) {
        SensorManager.getOrientation(rotationMatrix, orientation)
        val azimuth = orientation[0].toDouble()
        if (!primed) {
            sinMean = sin(azimuth)
            cosMean = cos(azimuth)
            primed = true
        } else {
            sinMean += alpha * (sin(azimuth) - sinMean)
            cosMean += alpha * (cos(azimuth) - cosMean)
        }
    }
}

/**
 * The good one: head orientation from the glasses themselves.
 *
 * Not wired up — mwdat-motion is not linked in app/build.gradle.kts yet
 * (commented out with the rest of the DAT artifacts). When you pin the SDK,
 * replace the body with the real stream. Two things to verify first:
 *
 *   1. MWDATMotion has open reports of `sensorUnavailable` on some models
 *      (Oakley Meta Vanguard), so keep [PhoneMotionSource] as the fallback and
 *      prefer it whenever the glasses stream is empty.
 *   2. Check the yaw convention against the phone's azimuth: the bearing fit
 *      silently produces garbage if one is left-handed and the other is not.
 */
class DatMotionSource : MotionSource {

    override fun start() {
        // DAT: com.meta.wearable:mwdat-motion
        //   val session = Wearables.createSession(AutoDeviceSelector()).getOrThrow()
        //   val motion = session.addMotion(MotionConfiguration(sampleRate = ...)).getOrThrow()
        //   scope.launch {
        //       motion.orientation.collect { o -> publish(o.yawDegrees) }
        //   }
    }

    override fun stop() {
        // DAT: motion.stop(); session.removeMotion()
    }

    override fun headingDeg(): Float? = null
}
