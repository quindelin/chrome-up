#!/usr/bin/env bash
# Seed OBS config from env on first run, then start OBS on the IRL scene.
set -euo pipefail
CFG="$HOME/.config/obs-studio"
if [ ! -f "$CFG/.seeded" ]; then
  mkdir -p "$CFG/basic/profiles/IRL" "$CFG/basic/scenes" "$CFG/plugin_config/obs-websocket"
  export STREAM_KEY SRT_PASSPHRASE OBS_WS_PASSWORD OUT_SERVER OUT_KEY
  for f in global.ini; do envsubst < /opt/obs-seed/$f > "$CFG/$f"; cp "$CFG/$f" "$CFG/user.ini"; done
  envsubst < /opt/obs-seed/basic.ini    > "$CFG/basic/profiles/IRL/basic.ini"
  envsubst < /opt/obs-seed/service.json > "$CFG/basic/profiles/IRL/service.json"
  envsubst < /opt/obs-seed/IRL.json     > "$CFG/basic/scenes/IRL.json"
  envsubst < /opt/obs-seed/websocket.json > "$CFG/plugin_config/obs-websocket/config.json"
  touch "$CFG/.seeded"
fi
ARGS=(--profile IRL --collection IRL --scene IRL --disable-shutdown-check --disable-updater)
[ "${OBS_AUTOSTREAM:-0}" = "1" ] && ARGS+=(--startstreaming)
exec obs "${ARGS[@]}"
