# ── Stage 1: dependency installer ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build deps in a separate layer so pip cache survives re-builds
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Pre-download the embedding model so the runtime image has it cached.
# The model is stored under /root/.cache/huggingface inside the builder,
# then copied across to the runtime stage to keep the final layer thin.
RUN python - <<'EOF'
from sentence_transformers import SentenceTransformer
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
EOF


# ── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Security: run as non-root
RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local
# Copy the pre-downloaded HuggingFace model cache
COPY --from=builder /root/.cache /home/app/.cache

# Copy application source (excludes everything in .dockerignore)
COPY --chown=app:app . .

USER app

EXPOSE 8000

# Liveness probe support: uvicorn exits non-zero on fatal errors
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
