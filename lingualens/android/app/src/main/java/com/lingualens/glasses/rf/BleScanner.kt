package com.lingualens.glasses.rf

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothManager
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.content.pm.PackageManager
import android.os.SystemClock
import android.util.SparseArray
import androidx.core.content.ContextCompat
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Wildcard BLE scan. No service filter: beacons advertise nothing but
 * manufacturer data, so filtering by service UUID would miss exactly the
 * devices this app exists to find.
 *
 * Every advertisement is handed to [advertisements] as a plain [Advertisement]
 * so the parser stays Android-free.
 *
 * Known platform limits, none of which we can work around:
 *   - Android throttles starting a scan to ~5 per 30 s; hammering start/stop
 *     returns SCAN_FAILED_SCANNING_TOO_FREQUENTLY.
 *   - With no filter and the screen off, the platform will not deliver results.
 *     Background scanning needs a PendingIntent scan or a foreground service
 *     (not built yet, see docs/RF_SCOPE.md).
 *   - RSSI is all you get. No phase, no AoA.
 */
class BleScanner(private val context: Context) {

    sealed class State {
        object Idle : State()
        object Scanning : State()
        data class Failed(val reason: String) : State()
    }

    private val _state = MutableStateFlow<State>(State.Idle)
    val state: StateFlow<State> = _state.asStateFlow()

    private val _ads = MutableSharedFlow<Advertisement>(
        replay = 0,
        extraBufferCapacity = 512,
        onBufferOverflow = kotlinx.coroutines.channels.BufferOverflow.DROP_OLDEST
    )
    val advertisements: Flow<Advertisement> = _ads.asSharedFlow()

    private var scanner: BluetoothLeScanner? = null
    private val lastSentAt = HashMap<String, Long>()

    /** Per-device rate limit: we need samples over time, not every duplicate. */
    private val minIntervalMs = 200L

    private val callback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) = offer(result)
        override fun onBatchScanResults(results: MutableList<ScanResult>) = results.forEach(::offer)
        override fun onScanFailed(errorCode: Int) {
            _state.value = State.Failed(describe(errorCode))
        }
    }

    @SuppressLint("MissingPermission")
    fun start() {
        val missing = missingPermissions()
        if (missing.isNotEmpty()) {
            _state.value = State.Failed("Missing permission: ${missing.joinToString()}")
            return
        }

        val manager = context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
        val adapter = manager?.adapter
        if (adapter == null) {
            _state.value = State.Failed("No Bluetooth adapter")
            return
        }
        if (!adapter.isEnabled) {
            _state.value = State.Failed("Bluetooth is off")
            return
        }
        val le = adapter.bluetoothLeScanner
        if (le == null) {
            _state.value = State.Failed("LE scanner unavailable")
            return
        }

        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .setCallbackType(ScanSettings.CALLBACK_TYPE_ALL_MATCHES)
            .setReportDelay(0)
            .build()

        scanner = le
        le.startScan(null, settings, callback)
        _state.value = State.Scanning
    }

    @SuppressLint("MissingPermission")
    fun stop() {
        runCatching { scanner?.stopScan(callback) }
        scanner = null
        _state.value = State.Idle
    }

    private fun offer(result: ScanResult) {
        val address = runCatching { result.device?.address }.getOrNull() ?: ""
        val now = SystemClock.elapsedRealtime()
        if (now - (lastSentAt[address] ?: 0L) < minIntervalMs) return
        if (lastSentAt.size > 4096) lastSentAt.clear()
        lastSentAt[address] = now

        val adv = toAdvertisement(result, address)
        _ads.tryEmit(adv)
    }

    @Suppress("DEPRECATION")
    private fun toAdvertisement(result: ScanResult, address: String): Advertisement {
        val record = result.scanRecord

        val tx = record?.txPowerLevel?.takeIf { it != Int.MIN_VALUE }

        // A device may advertise several manufacturer records; prefer Apple,
        // which is where iBeacon lives.
        val manufacturers: SparseArray<ByteArray>? = record?.manufacturerSpecificData
        var manufacturerId: Int? = null
        var manufacturerData: ByteArray? = null
        if (manufacturers != null && manufacturers.size() > 0) {
            var index = 0
            for (i in 0 until manufacturers.size()) {
                if (manufacturers.keyAt(i) == 0x004C) { index = i; break }
            }
            manufacturerId = manufacturers.keyAt(index)
            manufacturerData = manufacturers.valueAt(index)
        }

        val uuids = record?.serviceUuids?.map { it.uuid.toString() } ?: emptyList()

        val serviceData = HashMap<String, ByteArray>()
        record?.serviceData?.let { map ->
            // ScanRecord.serviceData is a Map<ParcelUuid, ByteArray>, not a SparseArray
            for ((uuid, bytes) in map) serviceData[uuid.uuid.toString()] = bytes
        }

        return Advertisement(
            address = address,
            name = runCatching { result.device?.name }.getOrNull(),
            rssi = result.rssi,
            txPower = tx,
            isConnectable = runCatching { result.isConnectable }.getOrDefault(false),
            manufacturerId = manufacturerId,
            manufacturerData = manufacturerData,
            serviceUuids = uuids,
            serviceData = serviceData,
            seenAtMs = System.currentTimeMillis()
        )
    }

    fun missingPermissions(): List<String> =
        requiredPermissions().filter {
            ContextCompat.checkSelfPermission(context, it) != PackageManager.PERMISSION_GRANTED
        }

    companion object {
        /**
         * Android 12+ only returns scan results to an app holding a location
         * permission *unless* BLUETOOTH_SCAN is declared with
         * `android:usesPermissionFlags="neverForLocation"`. We deliberately do
         * not use that flag: mapping where signals come from is location work,
         * and we also want Wi-Fi scanning (which needs it) as a second layer.
         *
         * BLUETOOTH_CONNECT is requested defensively too — some platform
         * versions gate BluetoothDevice.getAddress() behind it even for scan
         * results, and losing the address costs us the static-MAC signal.
         */
        fun requiredPermissions(): Array<String> = arrayOf(
            Manifest.permission.BLUETOOTH_SCAN,
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.ACCESS_FINE_LOCATION
        )

        private fun describe(errorCode: Int): String = when (errorCode) {
            SCAN_FAILED_ALREADY_STARTED -> "Scan already started"
            SCAN_FAILED_APPLICATION_REGISTRATION_FAILED -> "App registration failed"
            SCAN_FAILED_INTERNAL_ERROR -> "Internal scan error"
            SCAN_FAILED_FEATURE_UNSUPPORTED -> "BLE scanning unsupported on this device"
            SCAN_FAILED_OUT_OF_HARDWARE_RESOURCES -> "Out of hardware scan resources"
            SCAN_FAILED_SCANNING_TOO_FREQUENTLY -> "Scanning too frequently (platform throttle)"
            else -> "Scan failed ($errorCode)"
        }

        private const val SCAN_FAILED_ALREADY_STARTED = 1
        private const val SCAN_FAILED_APPLICATION_REGISTRATION_FAILED = 2
        private const val SCAN_FAILED_INTERNAL_ERROR = 3
        private const val SCAN_FAILED_FEATURE_UNSUPPORTED = 4
        private const val SCAN_FAILED_OUT_OF_HARDWARE_RESOURCES = 5
        private const val SCAN_FAILED_SCANNING_TOO_FREQUENTLY = 6
    }
}
