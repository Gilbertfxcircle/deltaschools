# Running Delta Plax locally (SQLite)

This is the fastest way to run the whole system on your own machine with **no
PostgreSQL, Redis, or MinIO** required. It uses SQLite for storage.

## Prerequisites

- **Python 3.11 or 3.12 recommended.** (3.13/3.14 also work with
  `requirements-dev.txt`, which uses version ranges, but some libraries publish
  prebuilt wheels for the newest Python versions later than release - if an
  install fails on 3.14, install 3.12 and use that.)
- **Node.js 18+** for the frontend.

Check your version:
```bash
python --version
```

---

## Option A - one command (recommended)

From the repo root:

**Windows (PowerShell):**
```powershell
.\run_local.ps1
```

**macOS / Linux:**
```bash
chmod +x run_local.sh
./run_local.sh
```

This creates a venv, installs the lightweight dev dependencies, runs migrations,
creates the super admin, seeds a demo school, and starts the API at
**http://localhost:8000** (interactive docs at `/docs`).

---

## Option B - manual steps

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt          # <-- note: requirements-DEV.txt

mkdir local_data -Force
$env:DATABASE_URL="sqlite+pysqlite:///./local_data/deltaplax.sqlite3"
$env:SECRET_KEY="dev-secret-key-1234567890"
$env:ENCRYPTION_KEY="dev-encryption-key-123456789012"
$env:DELTAPLAX_ADMIN_EMAIL="admin@deltaplax.com"
$env:DELTAPLAX_ADMIN_PASSWORD="DeltaPlax#2026"

python -m alembic upgrade head
python ..\scripts\bootstrap_superadmin.py
python ..\scripts\seed_demo_data.py
python -m uvicorn app.main:app --reload
```

> Use `python -m alembic` / `python -m uvicorn` (not bare `alembic` / `uvicorn`).
> The bare commands only work if the venv's Scripts folder is on PATH; the
> `python -m` form always works inside the activated venv.

**macOS / Linux** is the same with `source .venv/bin/activate` and `export VAR=...`.

---

## Frontend (new terminal, repo root)

```bash
cd frontend
npm install

# Point the SPA at the seeded demo tenant on localhost:
#   (the backend derives the tenant from the subdomain in production; on
#    localhost there is no subdomain, so we set it explicitly)
printf "VITE_DEFAULT_TENANT=demo\nVITE_API_BASE_URL=/api/v1\n" > .env

npm run dev
```

Open **http://localhost:3000**.

### Demo logins (tenant `demo`)
| Role | Email | Password |
|---|---|---|
| Director | director@demo.deltaplax.com | Director#2026 |
| Teacher | teacher@demo.deltaplax.com | Teacher#2026 |

---

## Trying the API directly (Swagger at /docs)

Because every per-school route is tenant-scoped, when calling the API directly
you must send the tenant header:

```
X-Tenant-ID: demo
```

In Swagger UI, requests to `/api/v1/auth/login` etc. need this header. The
React app sends it automatically (from `VITE_DEFAULT_TENANT`).

---

## Common issues

| Symptom | Cause / fix |
|---|---|
| `No matching distribution found for psycopg-binary==...` | You used `requirements.txt` (full cloud stack) on a very new Python. Use **`requirements-dev.txt`**, or install Python 3.12. |
| `'alembic' is not recognized` / `'uvicorn' is not recognized` | The previous `pip install` failed, so nothing installed. Fix the install first, then use `python -m alembic` / `python -m uvicorn`. |
| `ModuleNotFoundError: No module named 'sqlalchemy'` | Same root cause - the install aborted. Re-run `pip install -r requirements-dev.txt` and confirm it finishes without an ERROR line. |
| A bcrypt version warning prints on first hash | Harmless (passlib + bcrypt 4.x cosmetic warning). Hashing still works. |
| Frontend shows "Tenant not identified" | Ensure `frontend/.env` has `VITE_DEFAULT_TENANT=demo` and restart `npm run dev`. |

---

## Running the tests

```bash
cd backend
# Pure-logic tests run with zero dependencies:
python -m unittest discover -s tests
# Full suite (incl. DB integration) once dev deps are installed:
python -m pytest
```
