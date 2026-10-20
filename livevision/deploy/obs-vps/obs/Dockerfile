# Headless OBS Studio: Xvfb display, OBS from the official PPA (includes the
# browser source), x11vnc + noVNC so you can open the OBS UI through an SSH
# tunnel. Seeded on first start with a profile, the IRL scene and obs-websocket.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends software-properties-common gpg-agent ca-certificates \
 && add-apt-repository -y ppa:obsproject/obs-studio \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
        obs-studio xvfb x11vnc novnc websockify supervisor dbus-x11 pulseaudio \
        fonts-dejavu fonts-noto-cjk gettext-base openssl \
 && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash obs
COPY seed/ /opt/obs-seed/
COPY supervisord.conf /etc/supervisor/conf.d/obs.conf
COPY start.sh /usr/local/bin/start-obs
COPY entrypoint.sh /usr/local/bin/obs-entrypoint
RUN chmod +x /usr/local/bin/start-obs /usr/local/bin/obs-entrypoint \
 && mkdir -p /home/obs/.config/obs-studio && chown -R obs:obs /home/obs/.config
ENV DISPLAY=:99
CMD ["/usr/local/bin/obs-entrypoint"]
