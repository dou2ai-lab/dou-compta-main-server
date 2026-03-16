# Apply trust auth to running Postgres (fixes InvalidPasswordError from Windows host)
# Run after: docker compose up -d
# Usage: .\scripts\fix-postgres-auth.ps1

Write-Host "Applying trust auth to Postgres container..." -ForegroundColor Cyan

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$pgHbaPath = Join-Path $projectRoot "infrastructure\pg_hba.conf"

# Check if container exists
$exists = docker inspect dou-postgres 2>$null
if (-not $exists) {
    Write-Host "Container dou-postgres not found. Start it first: cd infrastructure; docker compose up -d" -ForegroundColor Red
    exit 1
}

# Replace entire pg_hba.conf (default 127.0.0.1 rule requires password and matches first)
docker cp $pgHbaPath dou-postgres:/tmp/pg_hba.conf
docker exec dou-postgres sh -c "cp /tmp/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf"

# Reload Postgres config (no restart needed)
docker exec dou-postgres psql -U dou_user -d dou_expense_audit -c "SELECT pg_reload_conf();"

Write-Host "`nTrust auth applied. Try signup again." -ForegroundColor Green
