# OnAir — iOS companion for the IRL stack

Are we live, and is the VPS healthy? OnAir polls the streaming VM
(`deploy/obs-vps`) every 5 s while it is open and shows:

- **Headline**: LIVE on <platforms> / program up on the VPS / glasses only / ready / offline
- **Feeds**: glasses → VPS ingest and OBS's composited program (HUD), with bitrate and uptime
- **Restream**: one toggle per platform — the same thing as saying "go live on twitch"
- **Clips**: autoclip's approval queue (opens the HTTPS page), clip count, publish mode
- **VPS**: CPU load, memory, disk, uptime

Everything comes from one authenticated call, `GET https://<host>/autoclip/api/autoclip/stack`
(`autoclip/stack.py`), behind the same Caddy basic auth as the approval page.

## Run it

```bash
cd deploy/obs-vps
./gcp.sh start
./gcp.sh static-ip     # once: the IP (and so the app's host) stops changing
./gcp.sh companion     # writes companion/ios/Config/Secrets.xcconfig
open ../../companion/ios/OnAir.xcodeproj
```

Or type the host, user and password on the app's Settings screen.

A stopped VM shows as **Offline**: the app can't start or stop the VM.
