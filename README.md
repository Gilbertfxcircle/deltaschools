# Delta Plax Education Suite

Multi-tenant, offline-capable School Management ERP for institutions across East
Africa (Uganda, South Sudan, Kenya, Tanzania, Rwanda).

> © 2026–2035 Delta Plax Technologies. All rights reserved.

This repository currently contains the **backend foundation** — the
architecturally and security-critical core that the rest of the product
(frontend, mobile, installer) builds on. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design and
[`docs/INSTALL.md`](docs/INSTALL.md) for setup.

## What is implemented

| Area | Status |
|---|---|
| Multi-tenancy (schema-per-tenant) with injection-safe schema resolution | ✅ |
| RBAC + permission matrix; Super Admin "forbidden writes" guard | ✅ |
| Immutable audit log (frozen domain object + DB trigger: PostgreSQL **and** SQLite) | ✅ |
| Super Admin bootstrap script (pre-created, never registered) | ✅ |
| Approval workflow state machine for protected-data changes | ✅ |
| Module (feature-flag) system + nav gating | ✅ |
| Auth: bcrypt, JWT (15-min access / 7-day refresh), TOTP MFA, lockout policy | ✅ |
| AES-256-GCM field encryption at rest | ✅ |
| Audit service wired into writes (institution/student/approval) | ✅ |
| Offline Sync Engine (queue push/pull + conflict→approval) | ✅ |
| Local EXE server entrypoint + installer scaffolding (PyInstaller + Inno Setup) | ✅ |
| FastAPI app: tenant middleware, routers, response envelope | ✅ |
| Alembic migration (global schema + audit trigger) + tenant provisioning | ✅ |
| Docker Compose (API, Postgres, Redis, MinIO, Nginx subdomain routing) | ✅ |
| Unit tests for every "law" (70 tests; 67 run with zero deps, 3 DB integration) | ✅ |

## Not yet implemented (planned next)

Frontend (React/Vite), Flutter mobile app, full Windows EXE build (the installer
scripts are scaffolded; building requires Windows + PyInstaller/Inno Setup),
Celery task wiring, AI features, and the remaining per-school domain modules
(library, hostel, transport, payroll UI, LMS, etc.). The per-school ORM currently
models a representative core; remaining tables follow the same pattern via new
migrations.

## Project layout

```
backend/        FastAPI application, models, migrations, tests
  app/core/     Pure, framework-free domain "laws" (tenant, rbac, modules, audit, ...)
  app/domain/   Pure domain logic (approval state machine, sync conflict rule)
  app/db/       Engine, tenant-scoped sessions, schema provisioning
  app/models/   SQLAlchemy 2.0 models (global + per-school)
  app/services/ Audit service + offline Sync Engine
  app/api/      Routers, dependencies (auth/RBAC guards)
  app/local_server.py  Offline EXE entrypoint (provision + sync engine)
  alembic/      Migrations (incl. audit immutability trigger)
  tests/        Unit tests (stdlib-runnable + pytest integration)
scripts/        bootstrap_superadmin.py, seed_demo_data.py
docker/         docker-compose.yml, Nginx tenant routing
installer/      PyInstaller spec + Inno Setup script (Windows EXE)
docs/           ARCHITECTURE.md, INSTALL.md, API.md
Makefile        Developer tasks (install/migrate/run/test/...)
.env.example    All required environment variables
```

## Quick start (dev)

```bash
cp .env.example .env          # fill in secrets
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
DELTAPLAX_ADMIN_PASSWORD='Str0ng#Pass!' python ../scripts/bootstrap_superadmin.py
uvicorn app.main:app --reload
```

## Running the tests

The domain "laws" are pure Python and run with **no third-party dependencies**:

```bash
cd backend
python -m unittest discover -s tests      # 67 tests run with no deps; 3 DB tests skip
# or, once requirements are installed:
pytest                                     # full suite incl. DB integration tests
```
