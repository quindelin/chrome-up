package com.lingualens.glasses

import android.app.Activity
import android.content.Context
import android.util.Log
import com.meta.wearable.dat.core.Wearables
import com.meta.wearable.dat.core.selectors.AutoDeviceSelector
import com.meta.wearable.dat.core.session.DeviceSession
import com.meta.wearable.dat.core.session.DeviceSessionState
import com.meta.wearable.dat.core.types.LinkState
import com.meta.wearable.dat.core.types.RegistrationState
import com.meta.wearable.dat.display.Display
import com.meta.wearable.dat.display.addDisplay
import com.meta.wearable.dat.display.removeDisplay
import com.meta.wearable.dat.display.types.DisplayState
import com.meta.wearable.dat.display.views.Direction
import com.meta.wearable.dat.display.views.FlexBoxBackground
import com.meta.wearable.dat.display.views.TextColor
import com.meta.wearable.dat.display.views.TextStyle
import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

/**
 * Bridge to the Meta Wearables Device Access Toolkit (DAT 1.0.1).
 *
 * The lesson normally runs as the Web App on the glasses (server/web), and
 * this wrapper only owns the microphone. DAT adds two optional things:
 *
 *   1. registration + device presence     -> mwdat-core
 *   2. a native display mode              -> mwdat-display
 *
 * Native display mode is opt-in because a DAT display session takes
 * exclusive control of the glasses display: while it runs, the Web App is
 * not visible. Each sendContent() replaces the whole screen, the glasses keep
 * no state, and a two-finger temple tap (Back) ends the session - all per
 * https://wearables.developer.meta.com/docs/develop/dat/display-overview
 *
 * Microphone access does not go through DAT at all: it is Bluetooth HFP,
 * handled in AudioCapture.
 */
class GlassesBridge(private val context: Context) {

    enum class Status { UNREGISTERED, DISCONNECTED, CONNECTED }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val onError = CoroutineExceptionHandler { _, t -> Log.e(TAG, "DAT failure", t) }

    private val _status = MutableStateFlow(Status.UNREGISTERED)
    val status: StateFlow<Status> = _status

    private val _deviceName = MutableStateFlow<String?>(null)
    val deviceName: StateFlow<String?> = _deviceName

    private val _displayActive = MutableStateFlow(false)
    val displayActive: StateFlow<Boolean> = _displayActive

    private var registered = false
    private var session: DeviceSession? = null
    private var display: Display? = null
    private var sessionJob: Job? = null
    private var displayJob: Job? = null
    private var lastLine: Triple<String, String, String>? = null

    /** Call once per process, before anything else touches DAT. */
    fun connect() {
        Wearables.initialize(context)
        scope.launch(onError) {
            Wearables.registrationState.collect { state ->
                registered = state == RegistrationState.REGISTERED
                if (!registered) _status.value = Status.UNREGISTERED
            }
        }
        scope.launch(onError) {
            Wearables.devices.collect { ids ->
                if (ids.isEmpty()) {
                    _deviceName.value = null
                    _status.value = if (registered) Status.DISCONNECTED else Status.UNREGISTERED
                }
                for (id in ids) {
                    scope.launch(onError) {
                        Wearables.devicesMetadata[id]?.collect { device ->
                            if (device.linkState == LinkState.CONNECTED) {
                                _deviceName.value = device.name
                                _status.value = Status.CONNECTED
                            }
                        }
                    }
                }
            }
        }
    }

    /** One-time: deep-links to the Meta AI app, which returns via lingualens:// */
    fun register(activity: Activity) {
        if (!registered) Wearables.startRegistration(activity)
    }

    /**
     * Take over the glasses display and draw lines natively instead of the
     * Web App. The user must start this explicitly (Meta's display model).
     */
    fun startDisplay() {
        if (session != null) return
        Wearables.createSession(AutoDeviceSelector()).fold(
            onSuccess = { s ->
                session = s
                sessionJob = scope.launch(onError) {
                    s.state.collect { st ->
                        when (st) {
                            DeviceSessionState.STARTED -> attachDisplay(s)
                            DeviceSessionState.STOPPED -> cleanup()
                            else -> {}
                        }
                    }
                }
                s.start()
            },
            onFailure = { error, _ -> Log.e(TAG, "createSession: ${error.description}") },
        )
    }

    private fun attachDisplay(s: DeviceSession) {
        if (display != null) return
        s.addDisplay().fold(
            onSuccess = { d ->
                display = d
                displayJob = scope.launch(onError) {
                    d.state.collect { st ->
                        _displayActive.value = st == DisplayState.STARTED
                        // The display can restart after a disconnect or a wake;
                        // the glasses keep nothing, so send the current line again.
                        if (st == DisplayState.STARTED) lastLine?.let { (a, b, c) -> showLine(a, b, c) }
                    }
                }
            },
            onFailure = { error, _ -> Log.e(TAG, "addDisplay: ${error.description}") },
        )
    }

    fun stopDisplay() {
        session?.removeDisplay()
        session?.stop()
        cleanup()
    }

    private fun cleanup() {
        displayJob?.cancel(); displayJob = null
        sessionJob?.cancel(); sessionJob = null
        display = null
        session = null
        _displayActive.value = false
    }

    /**
     * Mirror the current line onto the glasses. A no-op unless native display
     * mode is running - in Web App mode the page already shows it.
     */
    fun showLine(target: String, reading: String, english: String) {
        lastLine = Triple(target, reading, english)
        val d = display ?: return
        if (!_displayActive.value) return
        scope.launch(Dispatchers.IO + onError) {
            d.sendContent {
                flexBox(direction = Direction.COLUMN, gap = 12) {
                    flexBox(padding = 24, background = FlexBoxBackground.CARD) {
                        if (reading.isNotBlank()) text(reading, style = TextStyle.META, color = TextColor.SECONDARY)
                        text(target, style = TextStyle.HEADING)
                        if (english.isNotBlank()) text(english, style = TextStyle.BODY, color = TextColor.SECONDARY)
                    }
                }
            }.fold(
                onSuccess = {},
                onFailure = { error, _ -> Log.e(TAG, "sendContent: ${error.description}") },
            )
        }
    }

    fun haptic(kind: String) {
        // DAT exposes no haptics API for the glasses or the Neural Band, so
        // feedback stays on the phone.
        Haptics(context).play(kind)
    }

    private companion object {
        const val TAG = "LinguaLensDAT"
    }
}
