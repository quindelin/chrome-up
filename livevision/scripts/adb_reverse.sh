#!/usr/bin/env bash
# Let an Android phone reach this box as localhost over USB.
# Useful when the phone is on a guest wifi / AP-isolated network.
set -euo pipefail
PORT="${1:-8787}"
adb reverse "tcp:${PORT}" "tcp:${PORT}" && \
  echo "phone can now open http://localhost:${PORT}/phone"
