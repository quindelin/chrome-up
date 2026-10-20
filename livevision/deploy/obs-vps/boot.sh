#!/bin/bash
# GCE startup-script: runs as root on every boot. Re-runs setup.sh, which
# re-points the HTTPS hostname at this boot's IP and (re)starts the stack.
# On the very first boot the repo is not uploaded yet, so this does nothing.
for s in /home/*/chrome_up/deploy/obs-vps/setup.sh; do
  [ -f "$s" ] && USER=root bash "$s" > /var/log/obs-irl-setup.log 2>&1
done
exit 0
