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
import com.meta.wearable.dat.core.voiceinvocations.VoiceInvocationsStream
import com.meta.wearable.dat.core.voiceinvocations.startVoiceInvocationsStream
import com.meta.wearable.dat.core.voiceinvocations.types.actions.LaunchApp
import com.meta.wearable.dat.display.Display
import com.meta.wearable.dat.display.addDisplay
import com.meta.wearable.dat.display.removeDisplay
import com.meta.wearable.dat.display.types.DisplayState
import com.meta.wearable.dat.display.views.ButtonStyle
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
    private var lastCard: GlassesCard? = null

    /** A button on the glasses was pressed: "repeat", "playPause" or "next". */
    var onCommand: ((String) -> Unit)? = null

    /** "Hey Meta, start LinguaLens": the lesson is back on the glasses. */
    var onVoiceLaunch: (() -> Unit)? = null
    private var voice: VoiceInvocationsStream? = null

    /** Call once per process, before anything else touches DAT. */
    fun connect() {
        Wearables.initialize(context)
        listenForVoice()
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

    /**
     * Put the lesson on the glasses, or back on them after it was closed
     * there (leaving to do something else, or a call). DAT's Android display
     * has no start(), so a stopped display is removed and added again; a
     * session that has ended is started fresh.
     */
    fun showOnGlasses() {
        val s = session ?: return startDisplay()
        if (_displayActive.value) { lastCard?.let { send(it) }; return }
        displayJob?.cancel(); displayJob = null
        display?.let { s.removeDisplay() }
        display = null
        attachDisplay(s)
    }

    /** The Start / Stop label follows the native glasses-mic recording. */
    fun setPlaying(on: Boolean) {
        val card = (lastCard ?: GlassesCard(target = " ")).copy(playing = on)
        lastCard = card
        send(card)
    }

    /**
     * "Hey Meta, start LinguaLens" brings the lesson back from the glasses.
     * Needs the Voice Invocation permission for this app in the Wearables
     * Developer Center; until then the stream opens and never fires.
     */
    private fun listenForVoice() {
        if (voice != null) return
        val stream = try {
            Wearables.startVoiceInvocationsStream(AutoDeviceSelector())
        } catch (t: Throwable) {
            Log.w(TAG, "voice invocations unavailable", t); return
        }
        voice = stream
        scope.launch(onError) {
            stream.invocations.collect { invocation ->
                if (invocation is LaunchApp) {
                    showOnGlasses()
                    onVoiceLaunch?.invoke()
                    launch(Dispatchers.IO + onError) { invocation.responseHandle.sendSuccess(null) }
                }
            }
        }
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
                        if (st == DisplayState.STARTED) lastCard?.let { send(it) }
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

    /** Older pages that only know the three-field line. */
    fun showLine(target: String, reading: String, english: String) =
        showCard(GlassesCard(target = target, reading = reading, english = english))

    /**
     * Draw the server's card for the current step. A no-op unless native
     * display mode is running - in Web App mode the page already shows it.
     */
    fun showCard(card: GlassesCard) {
        if (card == lastCard) return
        lastCard = card
        send(card)
    }

    private fun send(card: GlassesCard) {
        val d = display ?: return
        if (!_displayActive.value) return
        scope.launch(Dispatchers.IO + onError) {
            // Primary colour only: SECONDARY is close to invisible on the
            // waveguide, and it was hiding the pinyin and the English.
            d.sendContent {
                flexBox(direction = Direction.COLUMN, gap = 10) {
                    flexBox(direction = Direction.COLUMN, padding = 24, gap = 8, background = FlexBoxBackground.CARD) {
                        if (card.header.isNotBlank()) text(card.header, style = TextStyle.META)
                        if (card.cue.isNotBlank()) text(card.cue, style = TextStyle.BODY)
                        text(card.target.ifBlank { " " }, style = TextStyle.HEADING)
                        if (card.reading.isNotBlank()) text(card.reading, style = TextStyle.BODY)
                        if (card.english.isNotBlank()) text(card.english, style = TextStyle.BODY)
                        if (card.footer.isNotBlank()) text(card.footer, style = TextStyle.META)
                    }
                    // the phone's controls, on the glasses
                    flexBox(direction = Direction.ROW, gap = 8) {
                        button(label = "Redo", style = ButtonStyle.OUTLINE,
                            onClick = { onCommand?.invoke("repeat") })
                        button(label = if (card.playing) "Stop" else "Start", style = ButtonStyle.PRIMARY,
                            onClick = { onCommand?.invoke("playPause") })
                        button(label = "Skip", style = ButtonStyle.OUTLINE,
                            onClick = { onCommand?.invoke("next") })
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
