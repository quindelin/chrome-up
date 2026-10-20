#!/usr/bin/env bash
# Seed OBS config from env on first run, then start OBS on the IRL scene.
set -euo pipefail
CFG="$HOME/.config/obs-studio"
if [ ! -f "$CFG/.seeded" ]; then
  mkdir -p "$CFG/basic/profiles/IRL" "$CFG/basic/scenes" "$CFG/plugin_config/obs-websocket"
  export STREAM_KEY SRT_PASSPHRASE OBS_WS_PASSWORD OUT_SERVER OUT_KEY LINGUALENS_URL
  for f in global.ini; do envsubst < /opt/obs-seed/$f > "$CFG/$f"; cp "$CFG/$f" "$CFG/user.ini"; done
  envsubst < /opt/obs-seed/basic.ini    > "$CFG/basic/profiles/IRL/basic.ini"
  envsubst < /opt/obs-seed/IRL.json     > "$CFG/basic/scenes/IRL.json"
  envsubst < /opt/obs-seed/websocket.json > "$CFG/plugin_config/obs-websocket/config.json"
  touch "$CFG/.seeded"
fi
# Scenes seeded before the blurred background existed get it added (once:
# hide or retune it in OBS and that sticks). "Glasses Blur" is a nested scene
# holding the same Glasses source cover-scaled to the canvas, blurred by stock
# filters (area downscale, bicubic upscale) and dimmed, so it fills the side
# bars behind the sharp camera without decoding the stream twice.
SCENE="$CFG/basic/scenes/IRL.json"
if [ -f "$SCENE" ] && command -v jq >/dev/null; then
  jq --slurpfile seed /opt/obs-seed/IRL.json '
    if any(.sources[]; .name == "Glasses Blur") or (any(.sources[]; .name == "Glasses") | not) then . else
      (.sources[] | select(.name == "Glasses") | .uuid) as $cam
      | ($seed[0].sources[] | select(.name == "Glasses Blur")) as $blur
      | ($seed[0].sources[] | select(.name == "IRL") | .settings.items[] | select(.name == "Glasses Blur")) as $item
      | .sources |= map(if .name == "IRL"
          then .settings.id_counter += 1 | .settings.items = [$item + {id: .settings.id_counter}] + .settings.items
          else . end)
      | .sources += [$blur | .settings.items[0].source_uuid = $cam]
      | .scene_order += [{name: "Glasses Blur"}]
    end' "$SCENE" > "$SCENE.tmp" && [ -s "$SCENE.tmp" ] && mv "$SCENE.tmp" "$SCENE" || rm -f "$SCENE.tmp"
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
# supervisord starts xvfb first but does not wait for it: give the display a
# moment to appear rather than failing fast and burning the restart budget
SOCK="/tmp/.X11-unix/X${DISPLAY#:}"
for _ in $(seq 1 50); do [ -S "$SOCK" ] && break; sleep 0.2; done

# Encoder, output size and browser rendering follow the hardware on every
# start (not just the first seed), so a VM that gains or loses its GPU is right.
#   GPU:      NVENC, 1080p, HUD Chromium on the GPU
#   no GPU:   x264 veryfast, 720p, Chromium in software
# Override with OUT_WIDTH / OUT_HEIGHT / OUT_FPS / OUT_KBPS in .env.
ini_set() {   # file section key value
  awk -v sec="[$2]" -v key="$3" -v val="$4" '
    $0 == sec { insec = 1; print; next }
    /^\[/ && insec { if (!done) print key "=" val; done = 1; insec = 0 }
    insec && index($0, key "=") == 1 { if (!done) print key "=" val; done = 1; next }
    { print }
    END { if (!done) { if (!insec) print sec; print key "=" val } }' "$1" > "$1.tmp" && mv "$1.tmp" "$1"
}
PROFILE="$CFG/basic/profiles/IRL/basic.ini"
if [ "${OBS_GPU:-0}" = "1" ]; then
  W="${OUT_WIDTH:-1920}"; H="${OUT_HEIGHT:-1080}"; KBPS="${OUT_KBPS:-6000}"
  ini_set "$PROFILE" SimpleOutput StreamEncoder nvenc
  ini_set "$PROFILE" SimpleOutput NVENCPreset2 p5            # quality end of NVENC's p1-p7
  HWACCEL=true
else
  W="${OUT_WIDTH:-1280}"; H="${OUT_HEIGHT:-720}"; KBPS="${OUT_KBPS:-4500}"
  ini_set "$PROFILE" SimpleOutput StreamEncoder x264
  HWACCEL=false
fi
ini_set "$PROFILE" Video OutputCX "$W"
ini_set "$PROFILE" Video OutputCY "$H"
ini_set "$PROFILE" Video FPSCommon "${OUT_FPS:-30}"
ini_set "$PROFILE" SimpleOutput VBitrate "$KBPS"
for f in "$CFG/user.ini" "$CFG/global.ini"; do [ -f "$f" ] && ini_set "$f" General BrowserHWAccel "$HWACCEL"; done
echo "obs: gpu=${OBS_GPU:-0} display=$DISPLAY encoder=$(grep '^StreamEncoder=' "$PROFILE" | cut -d= -f2) ${W}x${H}@${OUT_FPS:-30} ${KBPS} kbps browser-hwaccel=$HWACCEL"
# --startstreaming tries once: if MediaMTX (the local RTMP target) isn't
# listening yet - boot order isn't guaranteed - the stream just stops. Wait.
case "${OUT_SERVER:-}" in rtmp://127.0.0.1:*|rtmp://localhost:*)
  PORT="$(echo "$OUT_SERVER" | sed -E 's#^rtmp://[^:/]+:([0-9]+).*#\1#')"
  for _ in $(seq 1 120); do (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null && break; sleep 0.5; done ;;
esac
ARGS=(--profile IRL --collection IRL --scene IRL --disable-shutdown-check --disable-updater)
[ "${OBS_AUTOSTREAM:-0}" = "1" ] && ARGS+=(--startstreaming)
exec obs "${ARGS[@]}"
