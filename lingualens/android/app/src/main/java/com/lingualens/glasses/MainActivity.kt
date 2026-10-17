package com.lingualens.glasses

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.lingualens.glasses.rf.RfScopeActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * LinguaLens on Ray-Ban Display.
 *
 * The whole lesson UI is the 600x600 web app served by the LinguaLens server.
 * This Activity is the wrapper that a web app cannot be: it owns the
 * microphone, the vibration motor and (through DAT) the glasses themselves.
 *
 * Input mapping, so a Neural Band gesture reaches the same code path as a tap:
 *   swipe up / down  -> ArrowUp / ArrowDown (menu navigation)
 *   tap              -> Enter  (select, or hold-to-talk start)
 *   swipe back       -> Escape (back out of the menu)
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var client: LessonClient
    private lateinit var capture: AudioCapture
    private lateinit var bridge: GlassesBridge

    private val serverUrl: String
        get() = getSharedPreferences("lingualens", MODE_PRIVATE)
            .getString("server_url", DEFAULT_URL) ?: DEFAULT_URL

    private val clientId: String
        get() = getSharedPreferences("lingualens", MODE_PRIVATE)
            .getString("client_id", "glasses") ?: "glasses"

    // RECORD_AUDIO for the mic; BLUETOOTH_CONNECT so DAT and HFP can reach the glasses
    private val permissions = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { granted ->
        if (granted[Manifest.permission.RECORD_AUDIO] == true) bindMic()
        if (granted[Manifest.permission.BLUETOOTH_CONNECT] == true) bridge.connect()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        client = LessonClient(serverUrl, clientId)
        capture = AudioCapture(this)
        bridge = GlassesBridge(this)

        web = findViewById(R.id.web)
        web.webViewClient = WebViewClient()
        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
            cacheMode = WebSettings.LOAD_NO_CACHE
        }
        // lets app.js call window.LinguaLensHaptics.play("select")
        web.addJavascriptInterface(object : Any() {
            @JavascriptInterface
            fun play(kind: String) = runOnUiThread { bridge.haptic(kind) }
        }, "LinguaLensHaptics")
        // lets app.js mirror each line onto the glasses in native display mode
        web.addJavascriptInterface(object : Any() {
            @JavascriptInterface
            fun showLine(target: String, reading: String, english: String) =
                bridge.showLine(target, reading, english)
            @JavascriptInterface
            fun register() = runOnUiThread { bridge.register(this@MainActivity) }
            @JavascriptInterface
            fun startDisplay() = runOnUiThread { bridge.startDisplay() }
            @JavascriptInterface
            fun stopDisplay() = runOnUiThread { bridge.stopDisplay() }
        }, "LinguaLensGlasses")

        web.loadUrl("$serverUrl/?client_id=$clientId")

        val needed = listOf(Manifest.permission.RECORD_AUDIO, Manifest.permission.BLUETOOTH_CONNECT)
            .filter { ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED }
        if (Manifest.permission.RECORD_AUDIO !in needed) bindMic()
        if (Manifest.permission.BLUETOOTH_CONNECT !in needed) bridge.connect()
        if (needed.isNotEmpty()) permissions.launch(needed.toTypedArray())

        // The "rf" FAB opens the phone-side RF scope: same data the glasses
        // HUD will eventually consume, with a real canvas so the bearing math
        // can be validated without hardware. See docs/RF_SCOPE.md.
        findViewById<FloatingActionButton>(R.id.rf).setOnClickListener {
            startActivity(Intent(this, RfScopeActivity::class.java))
        }
    }

    private fun bindMic() {
        val button = findViewById<FloatingActionButton>(R.id.talk)
        button.setOnTouchListener { _, event ->
            when (event.action) {
                android.view.MotionEvent.ACTION_DOWN -> {
                    capture.start()
                    bridge.haptic("select")
                    true
                }
                android.view.MotionEvent.ACTION_UP -> {
                    val wav = capture.stop()
                    if (wav != null) send(wav)
                    true
                }
                else -> false
            }
        }
    }

    /** Called by a Neural Band tap too - see README "haptic actions". */
    fun startTalking() {
        if (capture.isRecording) return
        capture.start()
        bridge.haptic("select")
    }

    fun stopTalking() {
        if (!capture.isRecording) return
        capture.stop()?.let { send(it) }
    }

    private fun send(wav: ByteArray) {
        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                runCatching { client.submit(wav) }.getOrNull()
            }
            result ?: return@launch
            val passed = result.optBoolean("passed", false)
            bridge.haptic(if (passed) "pass" else "fail")
            // the websocket in the page will repaint; nudge it in case it slept
            web.evaluateJavascript("if(window.ws&&ws.readyState===1){ws.send('ping')}", null)
        }
    }

    companion object {
        // replace with your HTTPS host before shipping to the glasses
        private const val DEFAULT_URL = "http://10.0.0.10:8899"
    }
}
