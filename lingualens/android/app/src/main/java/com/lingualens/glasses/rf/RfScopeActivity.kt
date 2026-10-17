package com.lingualens.glasses.rf

import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.lingualens.glasses.R
import kotlinx.coroutines.launch

/**
 * RF Scope on the phone: the same snapshot the glasses would get, drawn with a
 * canvas and as text.
 *
 * Run this first, with no glasses involved. If the bearings here do not survive
 * a walk around a room, they will not survive a store, and there is no point
 * putting them on glass yet.
 *
 * How to read it: walk normally and slowly turn your head (or the phone) in a
 * circle. A bearing appears only after a device has been seen across at least
 * four 30-degree sectors — before that the row shows "unknown" on purpose,
 * rather than a number it cannot support.
 */
class RfScopeActivity : AppCompatActivity() {

    private lateinit var scope: RfScope

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { begin() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_rf)

        val radar = findViewById<RadarView>(R.id.radar)
        val list = findViewById<android.widget.TextView>(R.id.list)

        scope = RfScope(BleScanner(this), PhoneMotionSource(this))

        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                scope.snapshot.collect { snapshot ->
                    radar.emitters = snapshot.emitters
                    list.text = RfHud.renderText(RfHud.build(snapshot))
                }
            }
        }

        val missing = BleScanner.requiredPermissions().filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missing.isEmpty()) begin() else permissionLauncher.launch(missing.toTypedArray())
    }

    private fun begin() {
        scope.start(lifecycleScope)
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                scope.scannerState.collect { state ->
                    if (state is BleScanner.State.Failed) {
                        findViewById<android.widget.TextView>(R.id.list).text =
                            "Scanner stopped: ${state.reason}"
                    }
                }
            }
        }
    }

    override fun onDestroy() {
        scope.stop()
        super.onDestroy()
    }
}
