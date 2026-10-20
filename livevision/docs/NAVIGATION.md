# Navigation: Apple Maps turn-by-turn → compass (and lens)

```
Control tab › Choose destination (Apple Maps suggestions, saved, recent, a link)
Apple Maps › Share › LiveVision          (share extension → App Group)
livevision://navigate?to=<link or place> (Shortcuts, links)
   │  RouteNavigator (companion, MapKit)
   │    resolve: share-link coordinates, else MKLocalSearch near you
   │    route:   MKDirections (walking default, or driving)
   │    follow:  SensorBridge GPS projected onto the route line
   ▼
wss://<host>/ws/phone  {"route": {...}}   ~1/s moving, every 4 s standing still
   ▼
server/navigation.py  set_phone_route() → tick() → nav_state (source "apple")
   ▼
overlay  compass quest marker = next maneuver · "Turn left onto Market St 120 m"
                                                 "FERRY BUILDING 1.4 KM · 18 MIN"
```

## Picking a destination

iOS doesn't let other apps read the route Apple Maps is navigating, so
LiveVision routes on its own (same Apple Maps data, via MapKit). Three ways to
hand it a place:

- **Search** (Control › Navigation › Choose destination,
  `DestinationSearchView.swift`): as-you-type suggestions from
  `MKLocalSearchCompleter` biased to 30 km around you, a Paste button for a
  copied maps link, and **Saved** / **Recent** places (the last 10, swipe
  right to star one, left to remove). Walking / Driving sits at the top.
- **Share from Apple Maps** (`LiveVisionShare/`, an app extension): open a
  place, Share, LiveVision, Navigate on the HUD. The extension can't open the
  app, so it writes `{text, transport, ts}` to the App Group
  (`LIVEVISION_APP_GROUP`, `group.com.chromeup.livevision`) and posts the
  Darwin notification `com.chromeup.livevision.nav-inbox`. A running
  LiveVision (it keeps running in the background while the glasses stream)
  starts the route at once; otherwise `NavInbox` picks it up when the app
  becomes active (shares older than 30 min are dropped). Works from Google
  Maps, Safari and Messages too (any link or text).
- **URL**: `livevision://navigate?to=<percent-encoded link or place>`, e.g.
  from a Shortcut.

Everything ends in `RouteNavigator.navigate(to:)`: Apple Maps first, the HUD
server's own geocoding (Nominatim, straight-line marker) if MapKit can't place it.

If you change the bundle id in `Secrets.xcconfig`, change
`LIVEVISION_APP_GROUP` with it; both targets' entitlements read it.

## The phone (`companion/ios/LiveVisionApp/RouteNavigator.swift`)

- **Resolving.** An Apple Maps share link's coordinates (`coordinate=`, `ll=`,
  `daddr=`; Google's `@lat,lon` and `q=lat,lon` too). A short link
  (`maps.apple/p/…`) is fetched and the redirect's URL parsed. Anything without
  coordinates is searched by its `name=` / `q=` / `address=` (or the typed
  text) with `MKLocalSearch`, in a 30 km region around you. The place also goes
  to `POST /api/destination` as the server's fallback objective.
- **Routing.** `MKDirections`, transport from the Control tab's picker
  (Walking / Driving; MapKit has no transit steps). The step polylines become
  one line; each step's instruction is the maneuver at the start of its
  polyline; the last instruction ("The destination is on your left") is pinned
  to the end. The turn kind (`left`, `slight_right`, `uturn`, `arrive`, …) comes
  from the geometry, not the text, since MapKit localizes instructions.
- **Following.** Every GPS fix is projected onto the line (searching forward
  from the last segment, so a route that doubles back doesn't skip ahead). The
  next maneuver is the first turn more than 3 m ahead; its distance is along
  the route, not as the crow flies. ETA = MapKit's travel time scaled by the
  distance left.
- **Rerouting.** Two good fixes (accuracy < 50 m) more than **40 m** off the
  line, at most every 8 s → a new `MKDirections` from where you are.
- **Arrival.** Within 15 m of the end: one `arrived` message (the HUD's arrival
  banner), then after 10 s the destination clears on both sides.
- GPS comes from SensorBridge's own CLLocationManager (no second one): the
  "GPS (navigation)" toggle must be on. In your pocket it keeps running while
  the glasses stream, like the other sensors.

## The message

```json
{"route": {
  "active": true,
  "instruction": "Turn left onto Market St",
  "step_distance": 120,
  "maneuver": {"lat": 37.7755, "lon": -122.418, "bearing": 61.5, "type": "left"},
  "next_instruction": "Turn right onto 3rd St",
  "remaining_m": 1400,
  "eta_s": 1080,
  "destination": {"name": "Ferry Building", "lat": 37.7955, "lon": -122.3937},
  "transport": "walking",
  "status": "apple maps"
}}
```

`{"route": {"active": false}}` hands back to the server (Clear, or the phone
stopped navigating). `{"route": {"active": false, "arrived": true, ...}}` is the
arrival.

## The server (`server/navigation.py`)

`set_phone_route()` keeps the latest message; while it is younger than
`navigation.phone_fresh_s` (15 s) `tick()` returns it shaped for the compass
and the server's OSRM fetches pause. Between messages the bearing is re-aimed
from the latest GPS fix (same socket) to the maneuver point; the distance stays
the phone's along-route figure. Stale → the old behaviour (OSRM steps, manual
`/api/route` steps, or straight at the destination).

`nav_state` with a phone route:

```json
{"active": true, "source": "apple",
 "objective": {"name": "Ferry Building", "bearing": 61.5, "distance": 120,
               "step": "Turn left onto Market St", "icon": "diamond",
               "mode": "apple", "maneuver": "left"},
 "next": "Turn right onto 3rd St",
 "destination": {"name": "Ferry Building", "distance": 1400, "eta": 1080},
 "transport": "walking", "status": "apple maps"}
```

Test without a phone: `POST /api/route` with the same `{"route": {...}}` body
(it must be re-posted within 15 s to stay fresh), or send it on `/ws/phone`.
`tests/smoke.py` → "apple maps phone route".

## The lens (`LensRouter.swift`, optional)

Control tab → Navigation → **Directions on glasses**. The glasses allow one DAT
session and one Display per session, and the camera stream and the
teleprompter already share `GlassesStreamer.deviceSession`. So the Display
belongs to `LensRouter`; the teleprompter and the directions are its clients
and it composes one screen (each send replaces the whole view):

| on the lens | shows |
|---|---|
| directions only | compass strip (cardinals turning with the phone's heading, gold quest marker on the next maneuver, its distance), the instruction, "Ferry Building · 1.4 km · 18 min" |
| teleprompter only | the script page, as before |
| both | one line "120 m · Turn left onto Market St" with a turn icon, above the script page |

- The compass strip is a 600×130 PNG drawn on the phone (line art on black:
  black is transparent on the additive display). It is redrawn only when the
  heading moves ≥ 3° or the route progresses, and the router sends at most one
  screen every 0.4 s with one in flight, so the camera stream keeps its
  Bluetooth. **Compass on the lens** off = an arrow icon (relative to where you
  face) and the distance as text instead.
- The screen is re-sent every 12 s (the lens dims after 20 s without a send).
- Swipes on the Neural Band still turn script pages; the directions need no
  input.
- The heading is the phone's compass. With the phone in a pocket it follows
  your hips, not your head; the HUD's compass on the stream uses the same
  heading.
