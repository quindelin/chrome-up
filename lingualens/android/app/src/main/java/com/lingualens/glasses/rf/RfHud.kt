package com.lingualens.glasses.rf

import kotlin.math.roundToInt

/**
 * Turns a snapshot into something drawable on a 600x600 waveguide.
 *
 * The glasses display has no canvas: MWDATDisplay takes a declarative tree of
 * FlexBox / Text / Image / Button / Icon and each send replaces the whole
 * screen. So the HUD is a small number of rows plus one direction per row,
 * expressed with the built-in icon set — no sweeping radar animation, which
 * would neither fit the component model nor survive the BLE budget.
 *
 * [renderText] renders the same model as text, which is what the phone
 * activity shows and what you will use to sanity-check the numbers before
 * trusting them on glass.
 */
object RfHud {

    data class Row(
        val label: String,
        val kind: EmitterKind,
        val distanceM: Float?,
        /** 0 = ahead, positive = right. Null until the user has turned enough. */
        val relativeBearingDeg: Float?,
        val confidence: Float,
        val suspicion: Float,
        val sector: Int?
    )

    data class Model(
        val atMs: Long,
        val headingDeg: Float?,
        val total: Int,
        val beaconCount: Int,
        val rows: List<Row>,
        val notes: List<String>
    )

    fun build(snapshot: RfSnapshot, maxRows: Int = 8): Model {
        val rows = snapshot.emitters.take(maxRows).map { e ->
            Row(
                label = e.label,
                kind = e.kind,
                distanceM = e.distanceM,
                relativeBearingDeg = e.relativeBearingDeg,
                confidence = e.confidence,
                suspicion = e.suspicion,
                sector = sectorOf(e.relativeBearingDeg)
            )
        }
        return Model(
            atMs = snapshot.atMs,
            headingDeg = snapshot.headingDeg,
            total = snapshot.total,
            beaconCount = snapshot.emitters.count { it.kind.isPositioningInfrastructure },
            rows = rows,
            notes = snapshot.notes
        )
    }

    /** 8-way sector: 0 = ahead, then clockwise. */
    fun sectorOf(relativeBearingDeg: Float?): Int? {
        val r = relativeBearingDeg ?: return null
        return ((r / 45f).roundToInt() + 8) % 8
    }

    private val SECTOR_NAMES = arrayOf(
        "ahead", "ahead-right", "right", "behind-right",
        "behind", "behind-left", "left", "ahead-left"
    )

    fun sectorName(sector: Int?): String = sector?.let { SECTOR_NAMES[it] } ?: "unknown"

    /**
     * Cardinal icons only. The catalogue has no diagonal arrows, so odd
     * sectors get the nearest cardinal plus the text label.
     */
    fun sectorIconName(sector: Int?): String = when (sector) {
        0 -> "arrow-up-shallow-u"      // ahead
        2 -> "arrow-right"
        4 -> "arrow-down-shallow-u"    // behind
        6 -> "arrow-left"
        1 -> "arrow-up-shallow-u"
        3 -> "arrow-right"
        5 -> "arrow-down-shallow-u"
        7 -> "arrow-left"
        else -> "circle-8-rays-large"
    }

    fun renderText(m: Model): String = buildString {
        appendLine("RF SCOPE")
        appendLine(
            "heading ${m.headingDeg?.let { "${it.roundToInt()}°" } ?: "--"}   " +
                "${m.total} emitters   ${m.beaconCount} beacon"
        )
        appendLine("─".repeat(34))
        if (m.rows.isEmpty()) {
            appendLine("(nothing yet — turn slowly in a circle)")
        }
        for (r in m.rows) {
            val flag = if (r.suspicion >= 0.5f) "! " else "  "
            val dist = r.distanceM?.let { "%.1fm".format(it) } ?: "--"
            val dir = sectorName(r.sector)
            val conf = (r.confidence * 100).roundToInt()
            appendLine(
                "$flag${r.label.take(18).padEnd(18)} ${dist.padStart(6)} " +
                    "${dir.padEnd(12)} ${conf.toString().padStart(3)}%"
            )
        }
        if (m.notes.isNotEmpty()) {
            appendLine("─".repeat(34))
            m.notes.forEach { appendLine(it) }
        }
    }

    // ---------------------------------------------------------------------
    // DAT: the same model on the glasses.
    //
    // Once com.meta.wearable:mwdat-display is pinned, send this tree. Note that
    // sendContent() replaces the entire display and the glasses sleep after
    // ~20 s of inactivity, so send on change, not on a timer.
    //
    //   display.sendContent {
    //       flexBox(direction = Direction.COLUMN, gap = 8, paddingAll = 12) {
    //           text("RF SCOPE", style = TextStyle.HEADING)
    //           text("${m.total} emitters · ${m.beaconCount} beacon", style = TextStyle.META,
    //                color = TextColor.SECONDARY)
    //           for (r in m.rows) {
    //               flexBox(direction = Direction.ROW, gap = 8, crossAlignment = Alignment.CENTER) {
    //                   icon(name = IconName.valueOf(sectorIconName(r.sector)), style = IconStyle.FILLED)
    //                   flexBox(direction = Direction.COLUMN) {
    //                       text(r.label, style = TextStyle.BODY)
    //                       text("${r.kind.short} · ${r.distanceM ?: "--"}m · ${sectorName(r.sector)}",
    //                            style = TextStyle.META, color = TextColor.SECONDARY)
    //                   }
    //               }
    //           }
    //           m.notes.forEach { text(it, style = TextStyle.META, color = TextColor.SECONDARY) }
    //       }
    //   }
    //
    // IconName values above are illustrative: check the enum names in the
    // version you pin (docs/develop/dat/display-icons lists the catalogue).
    // ---------------------------------------------------------------------
}
