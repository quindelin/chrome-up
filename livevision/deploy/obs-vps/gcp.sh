#!/usr/bin/env bash
# The IRL OBS box on Google Cloud, driven from your laptop.
#
#   ./gcp.sh up        create firewall + VM, upload this repo, start the stack
#   ./gcp.sh deploy    re-upload the repo and rebuild (after code changes)
#   ./gcp.sh info      ingest URLs, keys, HUD URL
#   ./gcp.sh tunnel    open OBS (noVNC) at http://localhost:6080/vnc.html, websocket at :4455
#   ./gcp.sh obs-reset re-seed OBS scenes/settings from .env (loses UI edits)
#   ./gcp.sh stop      stop the VM - only the 15 GB disk bills (~$0.60/mo)
#   ./gcp.sh start     start it again and print the (new) ingest URLs
#   ./gcp.sh ssh       shell on the VM
#   ./gcp.sh static-ip keep this boot's IP for good (the companion app's host)
#   ./gcp.sh companion write the LiveVision iOS app's Secrets.xcconfig from the VM
#                      (host, approval login, glasses stream key + SRT passphrase)
#   ./gcp.sh env K [V] set K=V in the VM's .env and apply it (no V: prompts, hidden;
#                      several names: asks for each, applies once)
#   ./gcp.sh control-deploy  deploy the start/stop/status function LiveVision uses
#   ./gcp.sh destroy   delete VM, IP and firewall rule
#
# The external IP is ephemeral by default, so it changes on every start and
# a stopped VM costs nothing for it. The HTTPS hostname (<ip>.sslip.io) is
# refreshed on each boot. STATIC_IP=1 ./gcp.sh up reserves a fixed IP instead
# (~$7.30/mo while stopped) so the phone settings never change; on an existing
# VM, ./gcp.sh static-ip promotes the running IP to a reserved one.
set -euo pipefail
cd "$(dirname "$0")"

PROJECT="${PROJECT:-chrome-up-irl-e8d7}"
REGION="${REGION:-us-central1}"
ZONE="${ZONE:-${REGION}-a}"
NAME="${NAME:-obs-irl}"
# n1-standard-8 + one NVIDIA T4 (~$0.75-0.80/h running): OBS composites,
# encodes (NVENC 1080p) and renders the HUD on the GPU. The newer L4
# (MACHINE=g2-standard-8 ACCELERATOR=, ~$0.85/h) was out of stock in every US
# zone in Oct 2026. Without a GPU (MACHINE=e2-standard-8 ACCELERATOR=,
# ~$0.27/h) the software path saturated 8 cores.
MACHINE="${MACHINE:-n1-standard-8}"
DISK_GB="${DISK_GB:-40}"                 # OS + NVIDIA driver + images
DISK_TYPE="${DISK_TYPE:-pd-balanced}"    # G2 machines don't take pd-standard
# ACCELERATOR=nvidia-tesla-t4: attach a GPU to an N1 machine (the T4 fallback
# when L4s are out of stock: MACHINE=n1-standard-8 ACCELERATOR=nvidia-tesla-t4)
ACCELERATOR="${ACCELERATOR-nvidia-tesla-t4}"   # ACCELERATOR= (empty) for none
# RESTORE_ENV=<file>: a saved deploy/obs-vps/.env to start a new VM with (same
# stream key, passwords and approval login as the VM it replaces)
STATIC_IP="${STATIC_IP:-0}"
G=(gcloud --project "$PROJECT" --quiet)
REMOTE="chrome_up"

# keepalives: a dropped connection fails fast instead of hanging
ssh_() { "${G[@]}" compute ssh "$NAME" --zone "$ZONE" -- -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o ConnectTimeout=20 "$@"; }
scp_() { "${G[@]}" compute scp --zone "$ZONE" --scp-flag=-oServerAliveInterval=15 \
           --scp-flag=-oServerAliveCountMax=3 --scp-flag=-oConnectTimeout=20 "$@"; }

upload() {
  local tgz; tgz="$(mktemp -t chrome_up.XXXX).tgz"
  # tracked files only: no venvs, no local secrets, no extracted game audio.
  # Just the livevision/ tree, at the top of the archive, so the VM keeps the
  # layout it has always had (~/chrome_up/deploy/obs-vps/setup.sh, which the
  # boot script runs) after the repo split into livevision/ and lingualens/.
  # From the repo root: run from inside livevision/, HEAD:livevision is an
  # empty tree, and every deploy after the split uploaded a 45-byte archive.
  git -C "$(git rev-parse --show-toplevel)" archive --format=tar.gz -o "$tgz" HEAD:livevision
  if ! tar -tzf "$tgz" | grep -qx 'deploy/obs-vps/setup.sh'; then
    echo "refusing to deploy: the archive has no deploy/obs-vps/setup.sh" >&2
    rm -f "$tgz"; return 1
  fi
  scp_ "$tgz" "$NAME:~/chrome_up.tgz"
  # boot.sh lives in the VM's metadata (copied at create time): keep it current
  "${G[@]}" compute instances add-metadata "$NAME" --zone "$ZONE" --metadata-from-file startup-script=boot.sh >/dev/null
  if [ -n "${RESTORE_ENV:-}" ]; then
    scp_ "$RESTORE_ENV" "$NAME:~/restore.env"
    # only into a VM that has no .env yet: never overwrite a live one
    ssh_ "mkdir -p $REMOTE/deploy/obs-vps && { [ -f $REMOTE/deploy/obs-vps/.env ] || install -m 600 ~/restore.env $REMOTE/deploy/obs-vps/.env; } && rm -f ~/restore.env"
  fi
  # the LinguaLens panel's URL (Cloud Run, read-only stream view), if deployed
  local ll
  ll="$(../../../lingualens/deploy/deploy.sh url 2>/dev/null | sed -n 's/^ *OBS browser source *\(https[^ ]*\).*/\1/p' || true)"
  if [ -n "$ll" ]; then
    ssh_ "printf '%s' '$ll&view=stream' > ~/lingualens_url"
  fi
  # sfx you extracted yourself are gitignored; ship them separately if present
  if compgen -G "../../overlay/assets/sfx/*.[wom]*" >/dev/null; then
    scp_ ../../overlay/assets/sfx/*.{wav,ogg,mp3} "$NAME:~/" 2>/dev/null || true
  fi
  rm -f "$tgz"
  # setup runs detached on the VM, so a dropped SSH session cannot kill it
  ssh_ "mkdir -p $REMOTE && tar -xzf chrome_up.tgz -C $REMOTE && \
        (mv -f ~/*.wav ~/*.ogg ~/*.mp3 $REMOTE/overlay/assets/sfx/ 2>/dev/null || true) && \
        (SETUP_BUILD=1 nohup bash $REMOTE/deploy/obs-vps/setup.sh > ~/setup.log 2>&1 < /dev/null &)"
  wait_setup
}

wait_setup() {
  # one connection that waits on the VM (polling every 20 s over a fresh SSH
  # each time added minutes, and a sleeping laptop kept it looping); if the
  # connection drops, reconnect and keep waiting - setup runs under nohup
  echo "setup running on the VM (log: ~/setup.log)..."
  for _ in $(seq 1 40); do
    ssh_ "while pgrep -f '[d]eploy/obs-vps/setup.sh' >/dev/null; do sleep 2; done; tail -n 8 ~/setup.log" \
      2>/dev/null && return 0
    sleep 5
  done
  echo "lost the VM while waiting; setup keeps running there (./gcp.sh ssh tail ~/setup.log)" >&2
}

case "${1:-help}" in
  up)
    ADDR=()
    if [ "$STATIC_IP" = "1" ]; then
      "${G[@]}" compute addresses describe "$NAME-ip" --region "$REGION" >/dev/null 2>&1 \
        || "${G[@]}" compute addresses create "$NAME-ip" --region "$REGION"
      ADDR=(--address "$NAME-ip")
    fi
    "${G[@]}" compute firewall-rules describe "$NAME-ingest" >/dev/null 2>&1 \
      || "${G[@]}" compute firewall-rules create "$NAME-ingest" --target-tags "$NAME" \
           --allow tcp:80,tcp:443,tcp:1935,udp:8890 --description "IRL ingest + HUD https"
    if ! "${G[@]}" compute instances describe "$NAME" --zone "$ZONE" >/dev/null 2>&1; then
      GPU_FLAGS=()
      # GPU VMs can't live-migrate: they stop for host maintenance and restart
      case "$MACHINE" in g2-*|a2-*|a3-*) GPU_FLAGS=(--maintenance-policy TERMINATE --restart-on-failure) ;; esac
      [ -n "$ACCELERATOR" ] && GPU_FLAGS=(--accelerator "type=$ACCELERATOR,count=1" --maintenance-policy TERMINATE --restart-on-failure)
      "${G[@]}" compute instances create "$NAME" --zone "$ZONE" \
        --machine-type "$MACHINE" --tags "$NAME" ${GPU_FLAGS[@]+"${GPU_FLAGS[@]}"} \
        --image-family ubuntu-2404-lts-amd64 --image-project ubuntu-os-cloud \
        --boot-disk-size "${DISK_GB}GB" --boot-disk-type "$DISK_TYPE" \
        --metadata-from-file startup-script=boot.sh ${ADDR[@]+"${ADDR[@]}"}
      echo "waiting for ssh..."
      for _ in $(seq 1 30); do ssh_ true 2>/dev/null && break; sleep 5; done
    fi
    upload
    "$0" info
    ;;
  deploy)  upload ;;
  info)
    # DOMAIN is derived from the live IP, not .env, which may lag a fresh boot
    ssh_ "cd $REMOTE/deploy/obs-vps && . ./.env && IP=\$(curl -fsS -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip) && cat <<TXT

  phone/glasses ingest (pick one):
    SRT  (use this on cellular)  srt://\$IP:8890?streamid=publish:live/\$STREAM_KEY&passphrase=\$SRT_PASSPHRASE
    RTMP                         rtmp://\$IP:1935/live/\$STREAM_KEY

  phone sensor page (HTTPS)      https://\${IP//./-}.sslip.io/phone
  OBS UI                         ./gcp.sh tunnel  ->  http://localhost:6080/vnc.html
  obs-websocket (via tunnel)     ws://localhost:4455  password \$OBS_WS_PASSWORD
  OBS streams to                 \${OUT_SERVER:-unset}/\${OUT_KEY:-?}
  clip approvals (HTTPS)         https://\${IP//./-}.sslip.io/autoclip/   user \$AUTOCLIP_USER  password \$AUTOCLIP_PASSWORD
  autoclip                       publish \${AUTOCLIP_PUBLISH:-dry_run}  restream \$([ \"\${AUTOCLIP_LIVE_STREAMS:-0}\" = 1 ] && echo on || echo off)  (edit .env, then ./gcp.sh deploy)
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
  start)
    "${G[@]}" compute instances start "$NAME" --zone "$ZONE"
    for _ in $(seq 1 30); do ssh_ true 2>/dev/null && break; sleep 5; done
    "$0" info
    ;;
  static-ip)
    # promote the ephemeral IP in use to a reserved one: same address, kept
    # across stop/start (the companion app and phone settings never change)
    IP="$("${G[@]}" compute instances describe "$NAME" --zone "$ZONE" \
          --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
    [ -n "$IP" ] || { echo "no external IP: ./gcp.sh start first" >&2; exit 1; }
    "${G[@]}" compute addresses describe "$NAME-ip" --region "$REGION" >/dev/null 2>&1 \
      || "${G[@]}" compute addresses create "$NAME-ip" --region "$REGION" --addresses "$IP"
    echo "reserved $IP -> https://${IP//./-}.sslip.io (fixed from now on)"
    ;;
  companion)
    # LiveVision (companion/ios) build settings: host, approval-page login, and
    # the glasses ingest (stream key + SRT passphrase)
    OUT=../../companion/ios/Config/Secrets.xcconfig
    # lines that only live on this laptop survive the rewrite (TikTok client key)
    KEEP="$(grep -E '^TIKTOK_' "$OUT" 2>/dev/null || true)"
    ssh_ "cd $REMOTE/deploy/obs-vps && . ./.env && IP=\$(curl -fsS -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip) && \
          printf '// written by deploy/obs-vps/gcp.sh companion - keep private\nLIVEVISION_HOST = %s.sslip.io\nLIVEVISION_USER = %s\nLIVEVISION_PASSWORD = %s\nLIVEVISION_STREAM_KEY = %s\nLIVEVISION_SRT_PASSPHRASE = %s\n' \"\${IP//./-}\" \"\$AUTOCLIP_USER\" \"\$AUTOCLIP_PASSWORD\" \"\$STREAM_KEY\" \"\$SRT_PASSPHRASE\"" 2>/dev/null \
      | grep -E '^(//|LIVEVISION_)' > "$OUT.tmp" && mv "$OUT.tmp" "$OUT" && chmod 600 "$OUT"
    # VM start/stop (./gcp.sh control-deploy): host only, "//" is an xcconfig comment
    if [ -f .control-token ]; then
      URL="$("${G[@]}" run services describe "$NAME-control" --region "$REGION" --format='value(status.url)' 2>/dev/null || true)"
      [ -n "$URL" ] && printf 'LIVEVISION_CONTROL_HOST = %s\nLIVEVISION_CONTROL_TOKEN = %s\n' "${URL#https://}" "$(cat .control-token)" >> "$OUT"
    fi
    [ -n "$KEEP" ] && printf '%s\n' "$KEEP" >> "$OUT"
    grep -E "LIVEVISION_(HOST|CONTROL_HOST)" "$OUT"
    ;;
  control-deploy)
    # Cloud Run function that can see / start / stop the VM while it is off.
    # Its service account may only manage this one VM; calls need the token.
    SA="$NAME-control@$PROJECT.iam.gserviceaccount.com"
    [ -f .control-token ] || (umask 077; openssl rand -hex 24 > .control-token)
    "${G[@]}" iam service-accounts describe "$SA" >/dev/null 2>&1 \
      || "${G[@]}" iam service-accounts create "$NAME-control" --display-name "LiveVision VM start/stop"
    "${G[@]}" compute instances add-iam-policy-binding "$NAME" --zone "$ZONE" \
      --member "serviceAccount:$SA" --role roles/compute.instanceAdmin.v1 >/dev/null
    # starting a VM that runs as a service account needs actAs on that account
    VMSA="$("${G[@]}" compute instances describe "$NAME" --zone "$ZONE" --format='value(serviceAccounts[0].email)')"
    [ -n "$VMSA" ] && "${G[@]}" iam service-accounts add-iam-policy-binding "$VMSA" \
      --member "serviceAccount:$SA" --role roles/iam.serviceAccountUser >/dev/null
    "${G[@]}" run deploy "$NAME-control" --source control --function control \
      --base-image python312 --region "$REGION" --allow-unauthenticated \
      --service-account "$SA" --max-instances 1 --memory 256Mi \
      --set-env-vars "PROJECT=$PROJECT,ZONE=$ZONE,NAME=$NAME,CONTROL_TOKEN=$(cat .control-token)"
    echo "now ./gcp.sh companion (VM running) to put it in the app's Secrets.xcconfig"
    ;;
  env)
    # ./gcp.sh env TWITCH_STREAM_KEY          asks for the value (hidden; never
    #                                         in argv or shell history)
    # ./gcp.sh env KICK_CLIENT_ID KICK_CLIENT_SECRET KICK_REFRESH_TOKEN
    #                                         asks for each, applies once
    # ./gcp.sh env AUTOCLIP_PUBLISH live      sets one value as given
    shift
    KEYS=("$@"); VALS=()
    if [ $# -eq 2 ] && ! [[ "$2" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then KEYS=("$1"); VALS=("$2"); fi
    [ ${#KEYS[@]} -gt 0 ] || { echo "usage: ./gcp.sh env NAME [value] | NAME NAME ..." >&2; exit 1; }
    for K in "${KEYS[@]}"; do
      [[ "$K" =~ ^[A-Z_][A-Z0-9_]*$ ]] || { echo "not a variable name: $K" >&2; exit 1; }
    done
    if [ ${#VALS[@]} -eq 0 ]; then
      for K in "${KEYS[@]}"; do read -rsp "$K: " V; echo; VALS+=("$V"); done
    fi
    # names and values go over stdin (NUL-separated), not the remote command
    # line; setup runs under nohup so a dropped connection doesn't stop it
    { for i in "${!KEYS[@]}"; do printf '%s\0%s\0' "${KEYS[$i]}" "${VALS[$i]}"; done; } | ssh_ "cd $REMOTE/deploy/obs-vps && python3 -c '
import sys
parts = sys.stdin.buffer.read().decode().split(chr(0))[:-1]
new = dict(zip(parts[0::2], parts[1::2]))
lines = open(\".env\").read().splitlines()
out = [l for l in lines if l.split(\"=\", 1)[0] not in new]
out += [k + \"=\" + v for k, v in new.items()]
open(\".env\", \"w\").write(\"\\n\".join(out) + \"\\n\")
' && (nohup bash ~/$REMOTE/deploy/obs-vps/setup.sh > ~/setup.log 2>&1 < /dev/null &)"
    echo "${KEYS[*]} set on the VM; applying..."
    wait_setup
    ;;
  ssh)     shift; ssh_ "$@" ;;
  destroy)
    "${G[@]}" compute instances delete "$NAME" --zone "$ZONE" || true
    "${G[@]}" compute addresses delete "$NAME-ip" --region "$REGION" || true
    "${G[@]}" compute firewall-rules delete "$NAME-ingest" || true
    "${G[@]}" run services delete "$NAME-control" --region "$REGION" || true
    ;;
  *) sed -n '2,17p' "$0" ;;
esac
