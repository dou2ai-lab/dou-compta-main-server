# Run seed_roles.py inside the auth container (uses postgres:5432, same network as Postgres).
# From project root: .\infrastructure\seed-roles.ps1
# Requires: tables and tenant exist (run .\infrastructure\bootstrap-db.ps1 first on a fresh DB).

$ErrorActionPreference = "Stop"
$compose = "docker compose -f infrastructure/docker-compose.yml"
$dbUrl = "postgresql+asyncpg://dou_user:dou_password123@postgres:5432/dou_expense_audit"

Write-Host "Running seed_roles.py inside auth container (DB: postgres:5432)..." -ForegroundColor Cyan
& docker compose -f infrastructure/docker-compose.yml run --rm -e "SEED_DATABASE_URL=$dbUrl" auth python scripts/seed_roles.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Done." -ForegroundColor Green
