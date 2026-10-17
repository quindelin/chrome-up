package com.lingualens.glasses

import android.annotation.SuppressLint
import android.content.Context
import android.media.AudioDeviceInfo
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioRecord
import android.media.MediaRecorder
import kotlinx.coroutines.*
import java.io.ByteArrayOutputStream

/**
 * Captures one utterance as 16 kHz / 16-bit mono PCM WAV - exactly what both
 * scorers want (Azure Speech and iFlytek ISE).
 *
 * On Ray-Ban Display the glasses microphones are a Bluetooth HFP device. Per
 * Meta's guide (dat/microphones-and-speakers) we pick the TYPE_BLUETOOTH_SCO
 * communication device and switch the AudioManager to MODE_IN_COMMUNICATION,
 * so you speak through the glasses instead of holding the phone. If the
 * glasses are not connected we fall back to the phone mic.
 *
 * HFP is 8 kHz mono and beamformed to the wearer's voice. We still ask
 * AudioRecord for 16 kHz (Android upsamples), but there is nothing above
 * 4 kHz in it - fricatives (s / sh / x, し / す) score lower than on the
 * phone mic. [usingGlassesMic] says which one the last take came from.
 * HFP also drops the glasses speaker to 8 kHz for as long as it is active,
 * so routing is released as soon as the take ends.
 */
class AudioCapture(
    context: Context,
    private val onLevel: ((Float) -> Unit)? = null,
) {
    private val audioManager = context.getSystemService(AudioManager::class.java)

    /** True when the current/last take was routed to the glasses mic. */
    var usingGlassesMic = false
        private set

    companion object {
        const val SAMPLE_RATE = 16000
        private const val CHANNEL = AudioFormat.CHANNEL_IN_MONO
        private const val ENCODING = AudioFormat.ENCODING_PCM_16BIT
    }

    private var recorder: AudioRecord? = null
    private var job: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val pcmSink = ByteArrayOutputStream()

    var isRecording = false
        private set

    /** Records until [stop] is called (or [maxSeconds] elapses) and returns WAV bytes. */
    @SuppressLint("MissingPermission")
    fun start(maxSeconds: Int = 12) {
        if (isRecording) return
        usingGlassesMic = routeToGlasses()
        val minBuf = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL, ENCODING)
        recorder = AudioRecord(
            // VOICE_COMMUNICATION follows the communication device (HFP)
            if (usingGlassesMic) MediaRecorder.AudioSource.VOICE_COMMUNICATION
            else MediaRecorder.AudioSource.MIC,
            SAMPLE_RATE,
            CHANNEL,
            ENCODING,
            maxOf(minBuf, SAMPLE_RATE * 2)
        )
        recorder?.startRecording()
        isRecording = true

        pcmSink.reset()
        val sink = pcmSink
        val buffer = ShortArray(1024)
        val deadline = System.currentTimeMillis() + maxSeconds * 1000L
        job = scope.launch {
            while (isActive && isRecording && System.currentTimeMillis() < deadline) {
                val read = recorder?.read(buffer, 0, buffer.size) ?: break
                if (read <= 0) continue
                for (i in 0 until read) {
                    val s = buffer[i]
                    sink.write(s.toInt() and 0xFF)
                    sink.write((s.toInt() shr 8) and 0xFF)
                }
                if (onLevel != null) {
                    var sum = 0.0
                    for (i in 0 until read) sum += (buffer[i] * buffer[i]).toDouble()
                    withContext(Dispatchers.Main) {
                        onLevel?.invoke((Math.sqrt(sum / read) / 32768.0).toFloat())
                    }
                }
            }
        }
    }

    /** Stops capture and returns a complete WAV file (with header). */
    fun stop(): ByteArray? {
        if (!isRecording) return null
        isRecording = false
        job?.cancel()
        recorder?.apply { stop(); release() }
        recorder = null
        releaseRoute()
        val pcm = pcmSink.toByteArray()
        return if (pcm.isEmpty()) null else wav(pcm)
    }

    private fun routeToGlasses(): Boolean {
        val sco = audioManager.availableCommunicationDevices
            .firstOrNull { it.type == AudioDeviceInfo.TYPE_BLUETOOTH_SCO } ?: return false
        audioManager.mode = AudioManager.MODE_IN_COMMUNICATION
        return audioManager.setCommunicationDevice(sco)
    }

    private fun releaseRoute() {
        if (!usingGlassesMic) return
        audioManager.clearCommunicationDevice()
        audioManager.mode = AudioManager.MODE_NORMAL
    }

    private fun wav(pcm: ByteArray): ByteArray {
        val total = pcm.size
        val out = ByteArrayOutputStream(44 + total)
        fun le(value: Int, size: Int) {
            for (i in 0 until size) out.write((value shr (8 * i)) and 0xFF)
        }
        out.write("RIFF".toByteArray()); le(36 + total, 4); out.write("WAVE".toByteArray())
        out.write("fmt ".toByteArray()); le(16, 4); le(1, 2); le(1, 2)
        le(SAMPLE_RATE, 4); le(SAMPLE_RATE * 2, 4); le(2, 2); le(16, 2)
        out.write("data".toByteArray()); le(total, 4)
        out.write(pcm)
        return out.toByteArray()
    }
}
