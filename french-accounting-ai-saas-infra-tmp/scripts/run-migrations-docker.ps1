# Run migrations via Docker (works around Windows localhost->container auth issues)
# Usage: .\scripts\run-migrations-docker.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath

Write-Host "Running migrations via Docker (container network)..." -ForegroundColor Cyan
docker run --rm --network infrastructure_dou-network `
  -e DATABASE_URL=postgresql://dou_user:dou_password123@postgres:5432/dou_expense_audit `
  -v "${projectRoot}\backend\scripts:/app/scripts" `
  -v "${projectRoot}\backend\migrations:/app/migrations" `
  -w /app python:3.12-slim `
  bash -c "pip install -q asyncpg python-dotenv && python scripts/run_all_migrations.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nMigrations completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nMigrations failed." -ForegroundColor Red
    exit 1
}
