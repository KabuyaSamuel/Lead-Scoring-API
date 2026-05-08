# ─────────────────────────────────────────────
# Stage 1: Builder (train model)
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY scripts/ ./scripts/

RUN python scripts/train_model.py


# ─────────────────────────────────────────────
# Stage 2: Runtime (production)
# ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Install dependencies cleanly in runtime (safer than copying site-packages)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy model + app
COPY --from=builder /app/lead_model.pkl .
COPY app/ ./app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

# NO EXPOSE needed for Render (keeps it clean)

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]