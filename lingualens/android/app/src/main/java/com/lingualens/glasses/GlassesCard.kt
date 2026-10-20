package com.lingualens.glasses

import org.json.JSONObject

/**
 * One screen for the glasses, decided by the server for every step kind
 * (engine.glasses_card in server/engine.py): a recall shows its English cue
 * rather than a bare line, and the line you just passed comes back in full.
 */
data class GlassesCard(
    val header: String = "",
    val cue: String = "",
    val target: String = "",
    val reading: String = "",
    val english: String = "",
    val footer: String = "",
    /** Recording in progress: the Start / Stop button reads "Stop". */
    val playing: Boolean = false,
) {
    companion object {
        fun parse(json: String): GlassesCard = try {
            val o = JSONObject(json)
            GlassesCard(
                header = o.optString("header"),
                cue = o.optString("cue"),
                target = o.optString("target"),
                reading = o.optString("reading"),
                english = o.optString("english"),
                footer = o.optString("footer"),
                playing = o.optBoolean("playing"),
            )
        } catch (e: Exception) {
            GlassesCard(target = " ")
        }
    }
}
