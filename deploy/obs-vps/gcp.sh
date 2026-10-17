#!/usr/bin/env bash
# The IRL OBS box on Google Cloud, driven from your laptop.
#
#   ./gcp.sh up        create IP + firewall + VM, upload this repo, start the stack
#   ./gcp.sh deploy    re-upload the repo and rebuild (after code changes)
#   ./gcp.sh info      ingest URLs, keys, HUD URL
#   ./gcp.sh tunnel    open OBS (noVNC) at http://localhost:6080/vnc.html, websocket at :4455
#   ./gcp.sh obs-reset re-seed OBS from .env (after setting OUT_KEY)
#   ./gcp.sh stop      stop the VM - you stop paying for CPU (disk + IP still bill)
#   ./gcp.sh start     start it again (same IP)
#   ./gcp.sh ssh       shell on the VM
#   ./gcp.sh destroy   delete VM, IP and firewall rule
set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${PROJECT:-chrome-up-irl-e8d7}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-${REGION}-a}"
NAME="${NAME:-obs-irl}"
MACHINE="${MACHINE:-e2-standard-4}"     # 4 vCPU / 16 GB: OBS + Chromium + x264 720p30
DISK_GB="${DISK_GB:-30}"
G=(gcloud --project "$PROJECT" --quiet)
REMOTE="chrome_up"

ssh_() { "${G[@]}" compute ssh "$NAME" --zone "$ZONE" -- "$@"; }

upload() {
  local tgz; tgz="$(mktemp -t chrome_up.XXXX).tgz"
  # tracked files only: no venvs, no local secrets, no extracted game audio
  git -C ../.. archive --format=tar.gz -o "$tgz" HEAD
  "${G[@]}" compute scp --zone "$ZONE" "$tgz" "$NAME:~/chrome_up.tgz"
  # sfx you extracted yourself are gitignored; ship them separately if present
  if compgen -G "../../overlay/assets/sfx/*.[wom]*" >/dev/null; then
    "${G[@]}" compute scp --zone "$ZONE" ../../overlay/assets/sfx/*.{wav,ogg,mp3} "$NAME:~/" 2>/dev/null || true
  fi
  rm -f "$tgz"
  ssh_ "mkdir -p $REMOTE && tar -xzf chrome_up.tgz -C $REMOTE && \
        (mv -f ~/*.wav ~/*.ogg ~/*.mp3 $REMOTE/overlay/assets/sfx/ 2>/dev/null || true) && \
        bash $REMOTE/deploy/obs-vps/setup.sh"
}

case "${1:-help}" in
  up)
    "${G[@]}" compute addresses describe "$NAME-ip" --region "$REGION" >/dev/null 2>&1 \
      || "${G[@]}" compute addresses create "$NAME-ip" --region "$REGION"
    "${G[@]}" compute firewall-rules describe "$NAME-ingest" >/dev/null 2>&1 \
      || "${G[@]}" compute firewall-rules create "$NAME-ingest" --target-tags "$NAME" \
           --allow tcp:80,tcp:443,tcp:1935,udp:8890 --description "IRL ingest + HUD https"
    if ! "${G[@]}" compute instances describe "$NAME" --zone "$ZONE" >/dev/null 2>&1; then
      "${G[@]}" compute instances create "$NAME" --zone "$ZONE" \
        --machine-type "$MACHINE" --tags "$NAME" \
        --image-family ubuntu-2404-lts-amd64 --image-project ubuntu-os-cloud \
        --boot-disk-size "${DISK_GB}GB" --boot-disk-type pd-balanced \
        --address "$NAME-ip"
      echo "waiting for ssh..."
      for _ in $(seq 1 30); do ssh_ true 2>/dev/null && break; sleep 5; done
    fi
    upload
    "$0" info
    ;;
  deploy)  upload ;;
  info)
    ssh_ "cd $REMOTE/deploy/obs-vps && . ./.env && IP=\$(curl -fsS -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip) && cat <<TXT

  phone/glasses ingest (pick one):
    SRT  (use this on cellular)  srt://\$IP:8890?streamid=publish:live/\$STREAM_KEY&passphrase=\$SRT_PASSPHRASE
    RTMP                         rtmp://\$IP:1935/live/\$STREAM_KEY

  phone sensor page (HTTPS)      https://\$DOMAIN/phone
  OBS UI                         ./gcp.sh tunnel  ->  http://localhost:6080/vnc.html
  obs-websocket (via tunnel)     ws://localhost:4455  password \$OBS_WS_PASSWORD
  OBS streams to                 \${OUT_SERVER:-unset}  key \${OUT_KEY:+set}\${OUT_KEY:-NOT SET}
TXT"
    ;;
  tunnel)
    echo "OBS: http://localhost:6080/vnc.html   websocket: ws://localhost:4455   (Ctrl-C to close)"
    "${G[@]}" compute ssh "$NAME" --zone "$ZONE" -- -N -L 6080:127.0.0.1:6080 -L 4455:127.0.0.1:4455
    ;;
  obs-reset)
    ssh_ "cd $REMOTE/deploy/obs-vps && sudo docker compose down obs && sudo docker volume rm obs-vps_obs-config && sudo docker compose up -d obs"
    ;;
  stop)    "${G[@]}" compute instances stop "$NAME" --zone "$ZONE" ;;
  start)   "${G[@]}" compute instances start "$NAME" --zone "$ZONE" ;;
  ssh)     shift; ssh_ "$@" ;;
  destroy)
    "${G[@]}" compute instances delete "$NAME" --zone "$ZONE" || true
    "${G[@]}" compute addresses delete "$NAME-ip" --region "$REGION" || true
    "${G[@]}" compute firewall-rules delete "$NAME-ingest" || true
    ;;
  *) sed -n '2,13p' "$0" ;;
esac
