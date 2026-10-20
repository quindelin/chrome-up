#!/usr/bin/env bash
# autoclip — rolling-buffer clip agent.
#   ./run_autoclip.sh doctor    # check ffmpeg / OBS / deps
#   ./run_autoclip.sh run       # one cycle
#   ./run_autoclip.sh loop      # keep watching and clipping
#   ./run_autoclip.sh serve     # REST + OpenAPI
#   ./run_autoclip.sh mcp       # MCP stdio server (for agents)
#
# Cloud mode (phone → RTMP → autoclip):
#   ./run_autoclip.sh cloud              # uses source.mode=rtmp from .env
#   RTMP_STREAM_KEY=... ./run_autoclip.sh cloud
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3.13}"
command -v "$PY" >/dev/null || PY=python3

if [ ! -d .venv ]; then
  echo "Creating virtualenv with $PY ..."
  "$PY" -m venv .venv
  ./.venv/bin/pip install --upgrade pip wheel -q
  ./.venv/bin/pip install -r requirements.txt
fi

source .venv/bin/activate

if ! command -v ffmpeg >/dev/null; then
  echo "ffmpeg is required.  Install it with:  brew install ffmpeg" >&2
fi

# Cloud mode: source RTMP, loop forever, log to stderr.
if [ "${1:-}" = "cloud" ]; then
  : "${RTMP_URL:=rtmp://127.0.0.1:1935/live}"
  : "${RTMP_STREAM_KEY:=glasses}"
  : "${EVERY_SECONDS:=30}"
  export AUTOCLIP_SOURCE_MODE=rtmp
  exec python -m autoclip loop --every "$EVERY_SECONDS"
fi

exec python -m autoclip "$@"
