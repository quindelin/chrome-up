package com.lingualens.glasses.rf

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View
import kotlin.math.cos
import kotlin.math.sin

/**
 * Phone-side radar, for validating the pipeline without glasses on your face.
 *
 * The glasses display cannot draw this (no canvas in MWDATDisplay), so treat it
 * as a debug view: it is the fastest way to see whether a bearing is plausible
 * while you walk around a room.
 *
 * Dot placement: angle is the relative bearing (up = straight ahead), radius is
 * distance. Colour is suspicion (green -> red), opacity is confidence, so an
 * untrustworthy bearing is literally faint.
 */
class RadarView(context: Context, attrs: AttributeSet?) : View(context, attrs) {

    var emitters: List<Emitter> = emptyList()
        set(value) {
            field = value
            invalidate()
        }

    /** Distance at the outer ring, metres. */
    var rangeM: Float = 20f

    private val ring = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        color = Color.rgb(60, 120, 70)
        strokeWidth = 1.5f
    }
    private val cross = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        color = Color.rgb(40, 90, 50)
        strokeWidth = 1f
    }
    private val aheadMarker = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.rgb(120, 255, 150)
        style = Paint.Style.FILL
    }
    private val dot = Paint(Paint.ANTI_ALIAS_FLAG)
    private val halo = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val cx = width / 2f
        val cy = height / 2f
        val r = (minOf(width, height) / 2f) - 12f
        if (r <= 0) return

        for (i in 1..3) canvas.drawCircle(cx, cy, r * i / 3f, ring)
        canvas.drawLine(cx - r, cy, cx + r, cy, cross)
        canvas.drawLine(cx, cy - r, cx, cy + r, cross)

        // "ahead" tick at the top
        canvas.drawCircle(cx, cy - r, 4f, aheadMarker)

        for (e in emitters) {
            val rel = e.relativeBearingDeg ?: continue
            val dist = (e.distanceM ?: rangeM).coerceIn(0f, rangeM)
            val rad = Math.toRadians(rel.toDouble())
            val rr = r * (dist / rangeM)
            val x = cx + (sin(rad) * rr).toFloat()
            val y = cy - (cos(rad) * rr).toFloat()

            val hue = 120f * (1f - e.suspicion)
            val alpha = (60 + 195 * e.confidence).toInt().coerceIn(40, 255)
            val color = Color.HSVToColor(floatArrayOf(hue, 0.85f, 1f))

            halo.color = color
            halo.strokeWidth = 2f
            canvas.drawCircle(x, y, 9f, halo)

            dot.color = Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color))
            canvas.drawCircle(x, y, 3.5f + 4f * e.suspicion, dot)
        }
    }
}
