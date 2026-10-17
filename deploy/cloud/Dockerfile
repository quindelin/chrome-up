# Build context is the repo root so we can COPY autoclip/ + autoclip.yaml + requirements.txt.
# Build with:  docker build -f deploy/cloud/Dockerfile -t autoclip:latest .

FROM python:3.12-slim

# ffmpeg with libass for burned-in captions + the audio filters we use.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Deps first so this layer caches when only autoclip/ changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir \
        "fastapi>=0.110" \
        "uvicorn[standard]>=0.27" \
        "numpy>=1.24" \
        "PyYAML>=6.0" \
        "pydantic>=2.0" \
        "faster-whisper>=1.0" \
        "Pillow>=10.0" \
        "websocket-client>=1.6"

# App
COPY autoclip/ ./autoclip/
COPY autoclip.yaml ./
RUN mkdir -p var/autoclip/incoming

ENV PYTHONUNBUFFERED=1
# Sensible defaults for transcription; faster-whisper auto-detects CPU cores.
ENV WHISPER_MODEL=base
ENV OMP_NUM_THREADS=4

EXPOSE 8899

CMD ["python", "-m", "autoclip", "loop", "--every", "30"]
