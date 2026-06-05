#!/usr/bin/env bash
# =============================================================================
# Delta Plax Education Suite - one-shot LOCAL backend runner (macOS / Linux)
# -----------------------------------------------------------------------------
# Runs the API locally on SQLite. From the repo root:
#     ./run_local.sh
#
# Creates a venv, installs the lightweight dev requirements, runs migrations,
# bootstraps the super admin, seeds demo data, and starts the API on :8000.
# Re-running is safe (idempotent).
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/backend"

echo "==> Creating virtual environment (.venv)"
[ -d .venv ] || python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing dev requirements (SQLite, no Postgres/queue)"
python -m pip install --upgrade pip >/dev/null
pip install -r requirements-dev.txt

# --- Local environment (SQLite) ---
mkdir -p local_data
export DATABASE_URL="sqlite+pysqlite:///./local_data/deltaplax.sqlite3"
export SECRET_KEY="dev-secret-key-change-me-1234567890"
export ENCRYPTION_KEY="dev-encryption-key-change-me-123456"
export DELTAPLAX_ADMIN_EMAIL="admin@deltaplax.com"
export DELTAPLAX_ADMIN_PASSWORD="DeltaPlax#2026"

echo "==> Running migrations"
python -m alembic upgrade head

echo "==> Bootstrapping super admin"
python ../scripts/bootstrap_superadmin.py

echo "==> Seeding demo data (school 'demo')"
python ../scripts/seed_demo_data.py

echo ""
echo "==> Starting API at http://localhost:8000  (docs: /docs)"
echo "    Demo logins (tenant 'demo'):"
echo "      director@demo.deltaplax.com / Director#2026"
echo "      teacher@demo.deltaplax.com  / Teacher#2026"
echo ""
python -m uvicorn app.main:app --reload
