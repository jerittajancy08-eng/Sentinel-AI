# ─────────────────────────────────────────────
# Sentinel AI — Backend (FastAPI Investigation Gateway)
# ─────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# System deps (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY agents/ ./agents/
COPY core/ ./core/
COPY api/ ./api/
COPY data/ ./data/

# Defaults — override at deploy time via App Service Application Settings
ENV SENTINEL_MOCK_MODE=true \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Azure App Service for Containers sets $PORT; default to 8000 locally
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
