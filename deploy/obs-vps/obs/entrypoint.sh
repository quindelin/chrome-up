#!/usr/bin/env bash
# The obs-config volume is created root-owned; OBS and PulseAudio run as
# `obs` and must be able to write under ~/.config.
set -e
mkdir -p /home/obs/.config/obs-studio
chown -R obs:obs /home/obs/.config
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
