#!/usr/bin/env bash
# Seed OBS config from env on first run, then start OBS on the IRL scene.
set -euo pipefail
CFG="$HOME/.config/obs-studio"
if [ ! -f "$CFG/.seeded" ]; then
  mkdir -p "$CFG/basic/profiles/IRL" "$CFG/basic/scenes" "$CFG/plugin_config/obs-websocket"
  export STREAM_KEY SRT_PASSPHRASE OBS_WS_PASSWORD OUT_SERVER OUT_KEY
  for f in global.ini; do envsubst < /opt/obs-seed/$f > "$CFG/$f"; cp "$CFG/$f" "$CFG/user.ini"; done
  envsubst < /opt/obs-seed/basic.ini    > "$CFG/basic/profiles/IRL/basic.ini"
  envsubst < /opt/obs-seed/IRL.json     > "$CFG/basic/scenes/IRL.json"
  envsubst < /opt/obs-seed/websocket.json > "$CFG/plugin_config/obs-websocket/config.json"
  touch "$CFG/.seeded"
fi
# The stream output always follows .env (OUT_SERVER/OUT_KEY), so changing where
# OBS sends the program is an env edit + restart, not a re-seed. Default is
# MediaMTX live/program, which autoclip restreams to Twitch/YouTube on voice.
mkdir -p "$CFG/basic/profiles/IRL"
export OUT_SERVER="${OUT_SERVER:-rtmp://127.0.0.1:1935/live}" OUT_KEY="${OUT_KEY:-program}"
envsubst < /opt/obs-seed/service.json > "$CFG/basic/profiles/IRL/service.json"
# A headless box has nobody to click "launch in Safe Mode?": supervisord
# restarts are the crash handling, so drop OBS's unclean-shutdown marker.
rm -rf "$CFG/.sentinel"
ARGS=(--profile IRL --collection IRL --scene IRL --disable-shutdown-check --disable-updater)
[ "${OBS_AUTOSTREAM:-0}" = "1" ] && ARGS+=(--startstreaming)
exec obs "${ARGS[@]}"
