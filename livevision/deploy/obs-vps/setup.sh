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

# ---- NVIDIA GPU (G2 / L4): driver, Docker GPU runtime, a real X display -----
# OBS composites, encodes (NVENC) and renders the HUD's Chromium on the GPU.
# Without one (e2 machines) everything stays on the software path (Xvfb, x264).
GPU=0
if grep -qs 0x10de /sys/bus/pci/devices/*/vendor; then      # 0x10de = NVIDIA
  GPU=1
  if ! nvidia-smi >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ubuntu-drivers-common xserver-xorg-core
    # the full driver (GL + the Xorg module), not --gpgpu, which is compute only
    sudo DEBIAN_FRONTEND=noninteractive ubuntu-drivers install
    NEED_REBOOT=1
  fi
  if ! command -v nvidia-ctk >/dev/null; then
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
      | sudo gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
      | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
      | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
  fi
  if [ "${NEED_REBOOT:-0}" = 1 ]; then
    echo "NVIDIA driver installed: rebooting; boot.sh runs setup again on the way up"
    sudo reboot
    exit 0
  fi
  # an X server on the GPU with no monitor attached (data-centre GPUs have no
  # outputs): OBS and its Chromium draw here through the container's X socket
  BUS="$(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader | head -1)"    # 00000000:00:03.0
  IFS=':.' read -r _ b d f <<<"$BUS"
  BUSID="PCI:$((16#$b)):$((16#$d)):$((16#$f))"
  sudo tee /etc/X11/obs-xorg.conf >/dev/null <<XCONF
Section "ServerFlags"
    Option "AutoAddDevices" "False"
EndSection
Section "Device"
    Identifier "gpu0"
    Driver     "nvidia"
    BusID      "$BUSID"
    # headless: no monitor on a data-centre GPU. (UseDisplayDevice "None", the
    # old recipe, is rejected by current drivers: "not supported with virtual display")
    Option     "AllowEmptyInitialConfiguration" "True"
EndSection
Section "Screen"
    Identifier   "screen0"
    Device       "gpu0"
    DefaultDepth 24
    SubSection "Display"
        Depth   24
        Virtual 1920 1080
    EndSubSection
EndSection
XCONF
  sudo tee /etc/systemd/system/obs-xorg.service >/dev/null <<'UNIT'
[Unit]
Description=X server on the NVIDIA GPU for OBS (display :0, no monitor)
After=systemd-modules-load.service
[Service]
ExecStart=/usr/lib/xorg/Xorg :0 -ac -nolisten tcp -noreset -config /etc/X11/obs-xorg.conf
Restart=always
RestartSec=2
[Install]
WantedBy=multi-user.target
UNIT
  sudo systemctl daemon-reload
  sudo systemctl enable --now obs-xorg.service
  for _ in $(seq 1 25); do [ -S /tmp/.X11-unix/X0 ] && break; sleep 0.4; done
  [ -S /tmp/.X11-unix/X0 ] || { echo "GPU X server did not start:"; sudo journalctl -u obs-xorg -n 20 --no-pager; }
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
# where OBS streams its program (HUD + avatar). Default: back into MediaMTX
# as live/program, which autoclip restreams ("go live on twitch").
OUT_SERVER=rtmp://127.0.0.1:1935/live
OUT_KEY=program
OBS_AUTOSTREAM=1
ENV
fi
# older .env: OBS pointed at Twitch with no key -> the local program path
if grep -q '^OUT_SERVER=rtmp://live.twitch.tv/app$' .env && grep -q '^OUT_KEY=$' .env; then
  sed -i -e 's|^OUT_SERVER=.*|OUT_SERVER=rtmp://127.0.0.1:1935/live|' -e 's/^OUT_KEY=$/OUT_KEY=program/' \
    -e 's/^OBS_AUTOSTREAM=0$/OBS_AUTOSTREAM=1/' .env
fi
if ! grep -q '^AUTOCLIP_PASS_HASH=' .env; then
  # approval queue at https://$DOMAIN/autoclip/ behind basic auth. Single
  # quotes: the bcrypt hash is full of `$`, which compose would interpolate.
  PW="$(openssl rand -hex 12)"
  HASH="$(sudo docker run --rm caddy:2.8 caddy hash-password --plaintext "$PW")"
  cat >> .env <<ENV
# autoclip: clips + approval queue; "go live on <x>" reads the restream keys
AUTOCLIP_USER=clips
AUTOCLIP_PASSWORD=$PW
AUTOCLIP_PASS_HASH='$HASH'
AUTOCLIP_PUBLISH=dry_run
AUTOCLIP_LIVE_STREAMS=0
TWITCH_STREAM_KEY=
YOUTUBE_STREAM_KEY=
KICK_STREAM_KEY=
ENV
fi
# LinguaLens panel on stream: gcp.sh drops the Cloud Run link in ~/lingualens_url
grep -q '^LINGUALENS_URL=' .env || echo 'LINGUALENS_URL=' >> .env
if [ -s "${HOME:-/nonexistent}/lingualens_url" ]; then
  # escape sed's specials: the link is full of '&', which means "the match"
  LL="$(sed 's/[&|\\]/\\&/g' "$HOME/lingualens_url")"
  sed -i "s|^LINGUALENS_URL=.*|LINGUALENS_URL='${LL}'|" .env
fi
grep -q '^RUMBLE_URL=' .env || printf 'RUMBLE_URL=\nRUMBLE_STREAM_KEY=\n' >> .env

# GPU or not decides the compose files; compose reads COMPOSE_FILE from .env,
# so every `docker compose` (here, gcp.sh obs-reset, ...) picks it up
sed -i '/^COMPOSE_FILE=/d' .env
[ "$GPU" = 1 ] && echo 'COMPOSE_FILE=docker-compose.yml:docker-compose.gpu.yml' >> .env

# the IP is ephemeral: point the HTTPS hostname at whatever we got this boot
sed -i "s/^DOMAIN=.*/DOMAIN=${IP//./-}.sslip.io/" .env
set -a; . ./.env; set +a

OLD_MTX="$(cat mediamtx.yml 2>/dev/null || true)"
sed -e "s/__STREAM_KEY__/${STREAM_KEY}/" -e "s/__SRT_PASSPHRASE__/${SRT_PASSPHRASE}/" \
  mediamtx.yml.tmpl > mediamtx.yml
# compose does not recreate a container for a changed bind-mounted file
MTX_CHANGED=0; [ "$OLD_MTX" = "$(cat mediamtx.yml)" ] || MTX_CHANGED=1

# HUD config: the repo default, with vision reading the glasses feed back
# out of MediaMTX and progress kept in the data volume
python3 - "$STREAM_KEY" <<'PY'
import re, sys
key = sys.argv[1]
s = open("../../config.yaml").read()
feed = f"rtmp://127.0.0.1:1935/live/{key}"
s = re.sub(r"(?m)^(\s*source:) 0\b.*$", rf'\1 "{feed}"', s, count=1)
s = re.sub(r"(?m)^audio:\n", f'audio:\n  url: "{feed}"\n', s, count=1)
open("hud.yaml", "w").write(s)
PY

# autoclip config: the repo default with autoclip.vps.yaml on top; the two
# switches that let anything leave the box come from .env
python3 -c 'import yaml' 2>/dev/null || sudo apt-get install -y -qq python3-yaml >/dev/null
python3 - <<'PY'
import os, yaml
def merge(a, b):
    for k, v in b.items():
        a[k] = merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return a
cfg = merge(yaml.safe_load(open("../../autoclip.yaml")), yaml.safe_load(open("autoclip.vps.yaml")))
cfg["publish"]["mode"] = "live" if os.environ.get("AUTOCLIP_PUBLISH") == "live" else "dry_run"
cfg["live_streams"]["enabled"] = os.environ.get("AUTOCLIP_LIVE_STREAMS") == "1"
open("autoclip.yaml", "w").write("# generated by setup.sh - edit autoclip.vps.yaml / .env instead\n"
                                 + yaml.safe_dump(cfg, sort_keys=False))
PY

if [ "${SETUP_BUILD:-0}" = "1" ] || ! sudo docker image inspect obs-vps-obs >/dev/null 2>&1; then
  # deploy: (re)build. The disk is small on purpose, so build in two rounds,
  # each swapped in and its old image + build cache dropped before the next:
  # building all three at once next to the running images fills 15 GB. hud
  # and autoclip go together because they share the python+ffmpeg layers.
  prune() { sudo docker builder prune -af >/dev/null 2>&1 || true; sudo docker image prune -f >/dev/null 2>&1 || true; }
  prune
  for svcs in "obs" "hud autoclip"; do
    sudo docker compose build $svcs
    sudo docker compose up -d $svcs
    prune
  done
  sudo docker compose up -d
else
  # boot: no rebuild, just recreate whatever changed (Caddy's DOMAIN)
  sudo docker compose up -d
fi
[ "$MTX_CHANGED" = 1 ] && sudo docker compose restart mediamtx
sudo docker compose ps
