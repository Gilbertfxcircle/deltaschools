# =============================================================================
# Delta Plax Education Suite - one-shot LOCAL backend runner (Windows / PowerShell)
# -----------------------------------------------------------------------------
# Runs the API locally on SQLite. From the repo root:
#     .\run_local.ps1
#
# It creates a venv, installs the lightweight dev requirements, runs migrations,
# bootstraps the super admin, seeds demo data, and starts the API on :8000.
# Re-running is safe (idempotent).
# =============================================================================

$ErrorActionPreference = "Stop"

# Resolve repo root (this script's folder) and move into backend.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "backend")

Write-Host "==> Creating virtual environment (.venv)" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { python -m venv .venv }
. .\.venv\Scripts\Activate.ps1

Write-Host "==> Installing dev requirements (SQLite, no Postgres/queue)" -ForegroundColor Cyan
python -m pip install --upgrade pip | Out-Null
pip install -r requirements-dev.txt

# --- Local environment (SQLite) ---
New-Item -ItemType Directory -Force -Path "local_data" | Out-Null
$env:DATABASE_URL          = "sqlite+pysqlite:///./local_data/deltaplax.sqlite3"
$env:SECRET_KEY            = "dev-secret-key-change-me-1234567890"
$env:ENCRYPTION_KEY        = "dev-encryption-key-change-me-123456"
$env:DELTAPLAX_ADMIN_EMAIL = "admin@deltaplax.com"
$env:DELTAPLAX_ADMIN_PASSWORD = "DeltaPlax#2026"

Write-Host "==> Running migrations" -ForegroundColor Cyan
python -m alembic upgrade head

Write-Host "==> Bootstrapping super admin" -ForegroundColor Cyan
python ..\scripts\bootstrap_superadmin.py

Write-Host "==> Seeding demo data (school 'demo')" -ForegroundColor Cyan
python ..\scripts\seed_demo_data.py

Write-Host ""
Write-Host "==> Starting API at http://localhost:8000  (docs: /docs)" -ForegroundColor Green
Write-Host "    Demo logins (tenant 'demo'):" -ForegroundColor Green
Write-Host "      director@demo.deltaplax.com / Director#2026" -ForegroundColor Green
Write-Host "      teacher@demo.deltaplax.com  / Teacher#2026"  -ForegroundColor Green
Write-Host ""
python -m uvicorn app.main:app --reload
