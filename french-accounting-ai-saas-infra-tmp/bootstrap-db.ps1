# Bootstrap a fresh Postgres DB: create tables, seed tenant/permissions/roles/users, then seed PRD roles.
# From project root: .\infrastructure\bootstrap-db.ps1
# Requires: postgres running; auth image built.

$ErrorActionPreference = "Stop"
$dbUrl = "postgresql+asyncpg://dou_user:dou_password123@postgres:5432/dou_expense_audit"

Write-Host "Step 1/3: Creating all tables (create_tables.py has full model set)..." -ForegroundColor Cyan
& docker compose -f infrastructure/docker-compose.yml run --rm -e "DATABASE_URL=$dbUrl" auth python create_tables.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nStep 2/3: Seeding data (tenant, permissions, roles, users)..." -ForegroundColor Cyan
& docker compose -f infrastructure/docker-compose.yml run --rm -e "DATABASE_URL=$dbUrl" -e "BOOTSTRAP_SKIP_CREATE=1" auth python scripts/seed_data.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nStep 3/3: Seeding PRD roles (admin, employee, approver, finance)..." -ForegroundColor Cyan
& docker compose -f infrastructure/docker-compose.yml run --rm -e "SEED_DATABASE_URL=$dbUrl" auth python scripts/seed_roles.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nDone. DB is bootstrapped." -ForegroundColor Green
