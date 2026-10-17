#!/usr/bin/env bash
# Runs ON the VM (gcp.sh copies the repo up and calls this). Idempotent.
#   - installs Docker
#   - writes .env with fresh secrets on first run (never overwritten)
#   - renders mediamtx.yml + hud.yaml, then docker compose up
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
fi

IP="$(curl -fsS -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)"

if [ ! -f .env ]; then
  umask 077
  cat > .env <<ENV
# generated $(date -u +%F) - keep private
DOMAIN=${IP//./-}.sslip.io
STREAM_KEY=$(openssl rand -hex 12)
SRT_PASSPHRASE=$(openssl rand -hex 16)
OBS_WS_PASSWORD=$(openssl rand -hex 12)
# where OBS streams to; fill in, then: ./gcp.sh obs-reset
OUT_SERVER=rtmp://live.twitch.tv/app
OUT_KEY=
OBS_AUTOSTREAM=0
ENV
fi
# the IP is ephemeral: point the HTTPS hostname at whatever we got this boot
sed -i "s/^DOMAIN=.*/DOMAIN=${IP//./-}.sslip.io/" .env
set -a; . ./.env; set +a

sed -e "s/__STREAM_KEY__/${STREAM_KEY}/" -e "s/__SRT_PASSPHRASE__/${SRT_PASSPHRASE}/" \
  mediamtx.yml.tmpl > mediamtx.yml

# HUD config: the repo default, with vision reading the glasses feed back
# out of MediaMTX and progress kept in the data volume
python3 - "$STREAM_KEY" <<'PY'
import re, sys
key = sys.argv[1]
s = open("../../config.yaml").read()
s = re.sub(r"(?m)^(\s*source:) 0\b.*$", rf'\1 "rtmp://127.0.0.1:1935/live/{key}"', s, count=1)
open("hud.yaml", "w").write(s)
PY

sudo docker compose up -d --build
# the disk is small on purpose: drop build cache and replaced images
sudo docker builder prune -af >/dev/null 2>&1 || true
sudo docker image prune -f >/dev/null 2>&1 || true
sudo docker compose ps
