# Kural Headless OpenAI-compatible Whisper Transcription Server
# Multi-stage container build targeting Linux (AMD64)
# Exposes loopback HTTP API (POST /v1/audio/transcriptions, GET /v1/models, GET /health)

FROM python:3.12-slim AS runtime

# Install ffmpeg for audio decoding and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pinned uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /bin/uv

# Create non-root user and group
RUN groupadd -g 10001 kural && \
    useradd -u 10001 -g kural -s /bin/bash -m kural

WORKDIR /app

# Copy project files and manifests
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY kural ./kural

# Install server dependencies into system python
RUN uv pip install --system --no-cache ".[server]"

# Setup directories and non-root user permissions
RUN mkdir -p /home/kural/.cache && chown -R kural:kural /home/kural

USER kural
ENV HOME=/home/kural
ENV HF_HOME=/home/kural/.cache/huggingface
ENV PYTHONUNBUFFERED=1

EXPOSE 7777

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://127.0.0.1:7777/health || exit 1

ENTRYPOINT ["kural", "--serve"]
CMD ["--host", "0.0.0.0", "--port", "7777"]
