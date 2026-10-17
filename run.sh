#!/usr/bin/env bash
# Start HUDstream. Creates .venv on first run.
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
exec python -m server.main --config config.yaml "$@"
