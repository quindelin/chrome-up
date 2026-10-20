# HUDstream server (overlay + phone bridge). Build context: repo root.
FROM python:3.12-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libportaudio2 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir "fastapi>=0.110" "uvicorn[standard]>=0.27" "numpy>=1.24" \
        "PyYAML>=6.0" "opencv-python-headless>=4.9" "sounddevice>=0.4.6" "httpx>=0.27"
COPY server/ ./server/
COPY overlay/ ./overlay/
COPY web/ ./web/
COPY config.yaml ./
ENV PYTHONUNBUFFERED=1
EXPOSE 8787
