#!/bin/bash
# GCE startup-script: runs as root on every boot. Re-runs setup.sh, which
# re-points the HTTPS hostname at this boot's IP and (re)starts the stack.
# On the very first boot the repo is not uploaded yet, so this does nothing.
# startup-scripts run as root with no HOME; setup.sh reads files the deploy
# left in the deploying user's home (e.g. ~/lingualens_url)
for s in /home/*/chrome_up/deploy/obs-vps/setup.sh; do
  [ -f "$s" ] || continue
  owner="$(stat -c %U "$s")"
  # as the deploying user, not root: files setup.sh writes (mediamtx.yml,
  # hud.yaml, autoclip.yaml) must stay writable by the next ./gcp.sh deploy.
  # setup.sh sudo's for what needs root (GCE users have passwordless sudo).
  sudo -u "$owner" -H bash "$s" > /var/log/obs-irl-setup.log 2>&1
done
exit 0
