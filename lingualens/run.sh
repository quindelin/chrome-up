#!/usr/bin/env bash
# Start LinguaLens. Creates .venv on first run.
#
#   ./run.sh          Mandarin  (HSK 1-6)   config.yaml
#   ./run.sh ja       Japanese  (JLPT N5-N1) config.ja.yaml
#   ./run.sh es       Spanish   (CEFR A1-)   config.es.yaml
set -euo pipefail
cd "$(dirname "$0")"

LANG_CODE="${1:-zh}"
case "$LANG_CODE" in
  zh|chinese|mandarin) CONFIG="config.yaml"; shift || true ;;
  japanese)            CONFIG="config.ja.yaml"; shift || true ;;
  spanish)             CONFIG="config.es.yaml"; shift || true ;;
  *)
    # any course with its own config: ./run.sh fr -> config.fr.yaml
    if [ -f "config.$LANG_CODE.yaml" ]; then CONFIG="config.$LANG_CODE.yaml"; shift || true
    else CONFIG="config.yaml"; fi ;;
esac

PY="${PYTHON:-python3.13}"
command -v "$PY" >/dev/null || PY=python3

if [ ! -d .venv ]; then
  echo "Creating virtualenv with $PY ..."
  "$PY" -m venv .venv
  ./.venv/bin/pip install --upgrade pip wheel -q
  ./.venv/bin/pip install -r requirements.txt
fi

source .venv/bin/activate
exec python -m server.main --config "$CONFIG" "$@"
