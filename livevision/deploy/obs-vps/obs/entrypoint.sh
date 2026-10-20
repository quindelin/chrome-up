#!/usr/bin/env bash
# The obs-config volume is created root-owned; OBS and PulseAudio run as
# `obs` and must be able to write under ~/.config.
set -e
# A restarted container (every VM reboot) keeps /tmp, so Xvfb finds the last
# boot's lock, decides display :99 is taken and exits; OBS then can't open a
# display and supervisord gives up on both. Nothing is running yet: clear it.
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
mkdir -p /home/obs/.config/obs-studio
chown -R obs:obs /home/obs/.config
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
