# autoclip on the streaming VPS (clip pipeline + approval API). Build context: repo root.
FROM python:3.12-slim
# same first layer as hud/Dockerfile, so the two images share python + ffmpeg
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libportaudio2 \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
# av<19: faster-whisper passes av.open(metadata_errors=), which PyAV 19 dropped
# no opencv: privacy blur stays off here (it would add ~200 MB to a 15 GB disk)
RUN pip install --no-cache-dir "fastapi>=0.110" "uvicorn[standard]>=0.27" "numpy>=1.24" \
        "PyYAML>=6.0" "pydantic>=2.0" "faster-whisper>=1.0" "Pillow>=10.0" "websocket-client>=1.6" \
        "av<19"
COPY autoclip/ ./autoclip/
COPY autoclip.yaml ./
ENV PYTHONUNBUFFERED=1 \
    HF_HOME=/app/var/hf \
    OMP_NUM_THREADS=2
EXPOSE 8899
# nice 15: OBS's x264 and Chromium always win the CPU; autoclip gets the rest
CMD ["nice", "-n", "15", "python", "-m", "autoclip", "--config", "config.vps.yaml", "serve", "--loop"]
