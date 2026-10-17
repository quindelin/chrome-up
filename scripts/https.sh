#!/usr/bin/env bash
# Self-signed cert so an iPhone will hand over compass data.
# iOS refuses DeviceOrientation + Geolocation on plain http.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p certs

IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 127.0.0.1)"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem -days 365 \
  -subj "/CN=hudstream.local" \
  -addext "subjectAltName=DNS:hudstream.local,IP:${IP}"

cat <<TXT

certs/cert.pem + certs/key.pem created for ${IP}

  python -m server.main --ssl-cert certs/cert.pem --ssl-key certs/key.pem

Then on the iPhone:
  1. Open https://${IP}:8787/phone
  2. Tap "advanced" -> "continue to site" (self-signed warning)
  3. In Settings > General > VPN & Device Management, install/trust the profile
     if Safari still blocks the sensors.
TXT
