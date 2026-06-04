# Delta Plax Education Suite - backend image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for psycopg/cryptography wheels are bundled; keep image lean.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Application code, migrations and operational scripts.
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./alembic.ini
COPY scripts ./scripts

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Migrations + idempotent super-admin bootstrap, then serve (section 4.2).
ENTRYPOINT ["sh", "-c", "alembic upgrade head && python scripts/bootstrap_superadmin.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
