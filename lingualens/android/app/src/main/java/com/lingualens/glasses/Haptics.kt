package com.lingualens.glasses

import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.content.Context

/**
 * Haptics for the menu. On Ray-Ban Display the Neural Band / glasses give
 * their own feedback; this covers the phone-side vibration so the interaction
 * feels the same whichever surface you are using.
 */
class Haptics(context: Context) {
    private val vibrator: Vibrator? =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        }

    /** kind matches app.js: tick | select | back | pass | fail */
    fun play(kind: String) {
        val vibrator = vibrator ?: return
        val (ms, amplitude) = when (kind) {
            "select" -> 30 to 160
            "back" -> 20 to 110
            "pass" -> 60 to 200
            "fail" -> 90 to 255
            else -> 12 to 80
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createOneShot(ms.toLong(), amplitude))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(ms.toLong())
        }
    }
}
