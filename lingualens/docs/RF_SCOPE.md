# RF Scope — Meta Wearables RF monitor

An app for Meta Ray-Ban Display that turns the phone into a Bluetooth radio
scanner, shows every transmitter it can see, and tries to answer "is anything
in here tracking me?" on the 600x600 HUD.

**Status:** Android phone-side scanner, bearing math, parsers, classifier and
phone debug UI are done. Glasses HUD is sketched against `MWDATDisplay` and
will render the moment the DAT SDK is uncommented in
`android/app/build.gradle.kts`.

The first thing this doc says is also the most important: **what this app
cannot do, no scanner on any platform can do.** Read §6 before drawing
conclusions from a session.

---

## 1. What it does

```
                                ┌─────────────────────────┐
                                │  Meta Ray-Ban Display    │
                                │  (via MWDATDisplay)      │
                                │                         │
                                │  RF SCOPE                │
                                │  heading 137°            │
                                │  14 emitters · 3 beacon  │
                                │  ─────────────────────── │
                                │  ! iBeacon 8c12·2/9      │
                                │    4.2m  ahead-right 62% │
                                │  ...                    │
                                └────────────▲────────────┘
                                             │ BLE
                                ┌────────────┴────────────┐
                                │  Phone (Android)         │
                                │  BleScanner (wildcard)   │
                                │  RfEngine (aggregation)  │
                                │  Bearing (LSQ over yaw)  │
                                │  Classifier (verdicts)   │
                                └────────────▲────────────┘
                                             │
                                ┌────────────┴────────────┐
                                │  Wildcard BLE scan       │
                                │  (iBeacon, Eddystone,    │
                                │   Apple Find My, …)      │
                                └─────────────────────────┘
```

The glasses are a HUD plus a head-orientation reference (DAT: `MWDATMotion`).
All radio work happens on the phone. Wildcard scan, no service-UUID filter:
beacons that advertise nothing but manufacturer data are exactly the devices
this app exists to find.

## 2. Run it

```bash
cd android
# No gradle wrapper is committed. Use a local gradle 8.7+ or add one:
gradle wrapper --gradle-version 8.13
./gradlew :app:installDebug
```

Tap the compass-shaped FAB in the bottom-left of the main screen (the lesson
app's talk button is bottom-right; the two are unrelated, the FAB just lives
here because the same phone wraps the same glasses). Grant `BLUETOOTH_SCAN`,
`BLUETOOTH_CONNECT` and `ACCESS_FINE_LOCATION` when asked.

With no Meta glasses attached, the phone screen shows:

- a radar (relative bearing / distance) on top
- a text list on the bottom (the same data, in monospace)

Walk in a circle, slowly, and the bearings will populate. Sit still and you
get the distance, the RSSI and the suspicion score; the bearing only resolves
after you've turned through at least four 30° sectors of the emitter.

## 3. What you see

| On the phone | On the glasses (when DAT is linked) |
|---|---|
| Real radar canvas | `FlexBox` of `Icon` + `Text` rows, 600x600, additive |
| Full list, scrollable | Top 8 emitters |
| Every emitter | Counts only — space is tight |

Confidence is 0..1, with a hard floor: the bearing line is **missing** entirely
until `Bearing.fit` has at least 12 (azimuth, rssi) samples spanning at least
four 30° sectors *and* the fitted amplitude is ≥ 1.5 dB. That filter is the
honest answer to "why does this take so long to appear?".

## 4. Direction finding: what the number is, and isn't

There is no angle-of-arrival on a phone. `ScanResult` hands you RSSI and
nothing about phase; no consumer handset exposes IQ samples; Android 16's
`RangingManager` returns angle only for paired/known sessions, not for "sweep
the room" discovery.

What we do is fit a first-harmonic model to the curve of RSSI against the
device's heading:

```
rssi(θ) ≈ a + amp · cos(θ - φ)
```

The antenna is not isotropic and the head/body shadows it, so as the user
turns, RSSI traces a rough cosine in world azimuth. Fitting that cosine gives
φ: the azimuth of *least* attenuation, drawn as "the direction the signal
comes from". It is body-shadowing estimation, not AoA. Expect **±30–60°** in
a store with metal shelving.

The glasses help: `MWDATMotion` streams head orientation continuously, so
every glance the user makes is another sample of the curve. A head turning in
a store produces hundreds of samples in a minute; a phone in a pocket might
produce none. The phone fallback uses `TYPE_ROTATION_VECTOR` and the same
fitter, so the math does not care where the heading comes from.

Confidence blends four things: pattern depth (0–6 dB → 0–1), residual
sinusoidal fit, angular coverage (how many sectors populated), and sample
count. It is on purpose not "RSSI strength": a loud, omnidirectional device
gets low confidence on purpose.

## 5. Tracking detection

`Classifier` scores each emitter from what the frame *itself* admits. Every
point added also adds a note, so the app never makes a claim it cannot back
up.

| Signal | +suspicion | Note |
|---|---:|---|
| Frame is iBeacon or Eddystone UID/URL | 0.35 | "positioning beacon frame" |
| Apple "offline finding" (0x12) | 0.45 | "AirTag-class accessory" |
| Static MAC, not connectable | 0.25 | "same identity on every visit" |
| Advertises every ≤ 250 ms | 0.15 | "faster than a sensor needs" |
| Present for the whole visit (≥ 5 min) | 0.10 | "present for the whole visit" |

`Classifier.siteNotes` then summarises: 6+ positioning beacons → "indoor
positioning grid"; ≥1 Find My accessory → "check Apple's own unwanted-tracking
alert"; ≥1 static-MAC device → "stay identifiable across visits".

The killer feature, when you turn it on, is the **cross-visit log**: a local
SQLite table keyed on the proximity UUID + (major, minor) or Eddystone
namespace + instance, with a row per visit. "Same 37 beacons, same store, 4
visits, never moved" is a far stronger signal than any single scan. Not built
yet.

## 6. What no scanner can see

This is the part the user-facing copy has to keep saying, and the part the
rest of the industry quietly elides.

Retail footfall tracking is mostly done by **receivers**, not transmitters:

- ceiling Wi-Fi APs logging your phone's probe requests and SSID choices;
- BLE sniffers in shelves and ceiling tiles, logging your phone's
  advertisement MACs and the rotating-but-correlatable patterns they trace.

A passive receiver transmits nothing. No app on any platform can see it
through the radio. **If a store's positioning is fully receiver-side, this
app will show "nothing" while the store knows exactly where you are.** Be
honest about that in the UI, on the store page, and in the press.

What you *can* see are the **transmitters**: iBeacon/Eddystone beacons, Find
My network accessories, BLE sensors, digital signage with a Bluetooth
component, smart speakers, laptops and phones. That is still useful: many
shops do run transmitter grids, and the receiver-only stores tend to be
identifiable because of what they *don't* broadcast.

## 7. Files

```
android/app/src/main/java/com/lingualens/glasses/rf/
  RfModels.kt           data classes, pure Kotlin
  BeaconParser.kt       iBeacon, Eddystone, Apple Find My, generic
  VendorDb.kt           Bluetooth company IDs + the locally-administered bit
  Bearing.kt            RSSI-to-distance, LSQ first-harmonic fit
  Classifier.kt         "tracking infrastructure" heuristics
  RfEngine.kt           aggregation: per-key track, EMA, sort, snapshot
  BleScanner.kt         Android BLE scanner -> Flow<Advertisement>
  MotionSource.kt       Phone rotation vector; DAT motion placeholder
  RfScope.kt            scanner + motion + engine orchestrator
  RfHud.kt              600x600 glasses HUD model + text renderer
  RadarView.kt          phone-side canvas radar (debug only)
  RfScopeActivity.kt    phone-side debug UI

android/app/src/test/java/com/lingualens/glasses/rf/
  BeaconParserTest.kt   JVM unit tests
  BearingTest.kt        fits a synthetic lobe, asserts direction + distance
```

The whole core (`RfModels`, `BeaconParser`, `VendorDb`, `Bearing`,
`Classifier`, `RfEngine`) is Android-free and was verified by compiling it
standalone with a cached `kotlinc` 2.1.20 (the build environment here cannot
download AGP/Maven artifacts). All 18 end-to-end assertions pass — full
sweeps recover the lobe to 0°, iBeacon/Eddystone/Find My parse correctly,
and the classifier produces the expected notes.

## 8. What is and isn't built

Built:

- Wildcard BLE scan → `Advertisement` (Android).
- Frame parsers: iBeacon, Eddystone UID/URL/TLM/EID, Apple "offline finding"
  (0x12), other Apple Continuity (best-effort), generic manufacturer data,
  service-UUID fallback.
- First-harmonic bearing fit on a streaming (azimuth, rssi) series.
- Log-distance path loss for distance estimate.
- Phone rotation vector → world heading.
- Tracking-infrastructure classifier with per-point notes.
- Engine that keeps a stable per-key track across MAC rotation for the major
  beacon formats (iBeacon, Eddystone).
- 600x600 HUD model (FlexBox tree documented in `RfHud.kt`).
- Phone-side radar + text for testing without glasses.
- A second FAB in the lesson activity to open it.

Not built (next):

- mwdat-display: the tree is in a comment block; the `sendContent` call needs
  the SDK pinned and the icon `enum` names verified against the version you
  ship. Glasses-side validation: MockDeviceKit + Chrome.
- mwdat-motion: same story. Verify yaw convention against phone azimuth
  before turning it on.
- Wi-Fi layer: `WifiManager.getScanResults` + `WifiRttManager` for FTM
  ranging. Android only.
- Cross-visit SQLite log: the schema is `key`, `geohash`, `last_seen_ms`,
  `visit_count`. Drift-tracks the cross-visit tracking signal.
- Background scanning: a `ForegroundService` (or `PendingIntent` scan) so
  results keep flowing when the screen is off.
- iOS port. See §10.

## 9. Tunables

In `Bearing.kt`:

| const | default | what it does |
|---|---|---|
| `MIN_SAMPLES` | 12 | samples needed before a bearing is published |
| `MIN_SECTORS` | 4 | 30° sectors that must each hold at least one sample |
| `MAX_SAMPLES` | 240 | oldest kept per emitter (memory cap) |
| (inside `fit`) | 1.5 dB | minimum fitted amplitude for a usable bearing |

In `RfEngine.kt`:

| const | default | what it does |
|---|---|---|
| `retainMs` | 60 000 | drop a track if no advertisement in this long |
| `maxTracks` | 512 | hard cap, drops the weakest when full |
| `RSSI_ALPHA` | 0.15 | RSSI exponential moving-average weight |

In `RfScope.kt`:

| const | default | what it does |
|---|---|---|
| `emitPeriodMs` | 1 000 | display update period (BLE budget, do not go below ~700 ms) |

## 10. iOS status

Your developer account does not get you out of the iOS version of the
Android blockers, and it does not help with the iOS-specific ones.

| | iOS | Android |
|---|---|---|
| BLE scan permissions | `NSBluetoothAlwaysUsageDescription` (no special entitlement) | `BLUETOOTH_SCAN` (no special entitlement) |
| iBeacon payload in `ScanResult` | **stripped** — must use `CoreLocation` with known proximity UUID | full via `ScanRecord.getManufacturerSpecificData()` |
| MAC address | per-app UUID, rotates across reinstalls | real MAC |
| Wi-Fi scan | needs `NEHotspotHelper` entitlement, Apple grants case by case | `WifiManager` |
| UWB ranging | only for your own accessories (`Nearby Interaction`) | `UwbManager` for known sessions; `RangingManager` in 16 for BLE CS / Wi-Fi NAN RTT |
| DAT iOS app distribution | uses `ExternalAccessory` framework; **App Store submission explicitly not supported yet**, release channels only | Play Store viable |

Build on Android first. The iOS port becomes a subset: generic BLE scan
(iBeacon payloads hidden behind `CoreLocation` with known proximity UUIDs),
no real MAC, no Wi-Fi without a special entitlement, and you cannot put it on
the App Store until Meta finishes the `ExternalAccessory` story.

## 11. References

- Meta Wearables Device Access Toolkit v1.0 — `wearables.developer.meta.com/docs/develop/`
  (no auth). Live docs search: `mcp.developer.meta.com/wearables` (no token).
- iBeacon protocol — Apple, "Getting Started with iBeacon" (2013).
- Eddystone — `github.com/google/eddystone`.
- Apple "Offline Finding" / Find My network — reverse-engineered, see
  `openhaystack.io`; treat the type-byte 0x12 detection as a heuristic, not a
  fact.
- Bluetooth Company Identifiers — `bluetooth.com/specifications/assigned-numbers`.
