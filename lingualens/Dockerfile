# LinguaLens server for Cloud Run (deploy/lingualens/deploy.sh).
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY server/ ./server/
COPY config.yaml config.ja.yaml ./
ENV PYTHONUNBUFFERED=1
# Cloud Run sets PORT; LINGUALENS_STATE / LINGUALENS_KEY come from the deploy
CMD ["python", "-m", "server.main", "--host", "0.0.0.0"]
