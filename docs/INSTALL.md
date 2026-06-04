# Installation Guide — Delta Plax Education Suite

Covers the three deployment models from the brief: **Cloud (SaaS)**,
**Local (offline)**, and **Hybrid**.

---

## 0. Prerequisites

- Docker + Docker Compose (for the cloud stack)
- Python 3.11+ (for local/dev without Docker)
- A strong Super Admin password (the bootstrap refuses weak ones)

---

## 1. Cloud (SaaS) deployment

```bash
# 1. Clone
git clone https://github.com/Gilbertfxcircle/deltaschools.git
cd deltaschools

# 2. Configure environment
cp .env.example .env
# Edit .env — set at minimum:
#   SECRET_KEY, ENCRYPTION_KEY, DELTAPLAX_ADMIN_EMAIL, DELTAPLAX_ADMIN_PASSWORD
# Generate keys:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"   # SECRET_KEY
#   python -c "import secrets; print(secrets.token_urlsafe(32))"   # ENCRYPTION_KEY

# 3. Build and start the stack (API, Postgres, Redis, MinIO, Nginx)
docker compose -f docker/docker-compose.yml up -d --build
```

On first boot the API container entrypoint runs **`alembic upgrade head`** then
**`python scripts/bootstrap_superadmin.py`** automatically (section 4.2), so the
global schema, audit trigger and Super Admin account are created for you.

```bash
# 4. (Optional) verify bootstrap ran — it is idempotent
docker exec deltaplax_api python scripts/bootstrap_superadmin.py
#   -> [SKIP] Super admin 'admin@deltaplax.com' already exists.

# 5. (Optional) seed demo data
docker exec deltaplax_api python scripts/seed_demo_data.py

# 6. Health check
curl http://localhost/health
```

### DNS / tenant routing

Point `*.deltaplax.com` and `admin.deltaplax.com` at the Nginx host. Nginx maps
`stmarys.deltaplax.com` → `X-Tenant-ID: stmarys` (see
`docker/nginx/deltaplax.conf`); `admin.` and the apex are tenantless. Terminate
TLS at Nginx and force HTTP→HTTPS in production.

---

## 2. Local / dev (without Docker)

```bash
cp .env.example .env
# For a fully local install, use SQLite:
#   DATABASE_URL=sqlite+pysqlite:///./local_data/deltaplax.sqlite3

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head
DELTAPLAX_ADMIN_PASSWORD='Str0ng#Pass!' python ../scripts/bootstrap_superadmin.py
python ../scripts/seed_demo_data.py        # optional

uvicorn app.main:app --reload              # http://127.0.0.1:8000/docs
```

With SQLite, schemas are not used; the audit immutability trigger is installed
in the SQLite dialect, so audit records are still tamper-proof.

---

## 3. Hybrid

Run the local server (section 2 / the EXE) at each school and point
`CLOUD_SYNC_URL` at the cloud API. The Sync Engine (planned) pushes queued local
writes and pulls cloud updates every `SYNC_POLL_SECONDS`, resolving conflicts via
the approval workflow rather than overwriting.

---

## 4. Verifying the security "laws"

```bash
cd backend
python -m unittest discover -s tests -v     # 61 tests, no third-party deps
```

This proves, among others, that a malicious tenant id cannot produce an unsafe
schema, that the Super Admin cannot be granted protected-write permissions, and
that a SQLite-backed audit row rejects UPDATE/DELETE.

---

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `DELTAPLAX_ADMIN_PASSWORD env variable is required` | Set it in `.env` / the container env before bootstrap. |
| `Weak DELTAPLAX_ADMIN_PASSWORD` | Use ≥10 chars with upper, lower, digit and symbol. |
| `Tenant not identified` (HTTP 400) | Call a tenant subdomain or send `X-Tenant-ID`; `/auth`, `/admin`, `/institutions` are tenantless. |
| Alembic can't find the DB | `DATABASE_URL` is read from settings/env, not `alembic.ini`. |
