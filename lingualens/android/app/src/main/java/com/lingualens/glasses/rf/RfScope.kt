package com.lingualens.glasses.rf

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch

/**
 * Wires the scanner, the motion source and the engine together.
 *
 * The scan rate is hundreds of advertisements per second in a store and every
 * `sendContent()` on the glasses costs a full layout over BLE, so the snapshot
 * is published on a slow tick and nothing downstream is expected to keep up
 * with the raw firehose.
 */
class RfScope(
    private val scanner: BleScanner,
    private val motion: MotionSource
) {

    private val engine = RfEngine()

    private val _snapshot = MutableStateFlow(RfSnapshot.empty())
    val snapshot: StateFlow<RfSnapshot> = _snapshot.asStateFlow()

    val scannerState: StateFlow<BleScanner.State> = scanner.state

    private var job: Job? = null

    /** How often the display is offered a new frame. Do not go below ~700 ms. */
    var emitPeriodMs = 1_000L

    fun start(scope: CoroutineScope) {
        if (job?.isActive == true) return
        scanner.start()
        motion.start()
        job = scope.launch(Dispatchers.Default) {
            val ingest = launch {
                scanner.advertisements.collect { adv -> engine.ingest(adv, motion.headingDeg()) }
            }
            val emit = launch {
                while (isActive) {
                    delay(emitPeriodMs)
                    _snapshot.value = engine.snapshot(motion.headingDeg())
                }
            }
            joinAll(ingest, emit)
        }
    }

    fun stop() {
        job?.cancel()
        job = null
        scanner.stop()
        motion.stop()
    }
}
