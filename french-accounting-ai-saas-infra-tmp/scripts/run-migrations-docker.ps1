# Run migrations via Docker (works around Windows localhost->container auth issues)
# Usage: .\scripts\run-migrations-docker.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
# Backend is sibling of infra folder: dou-compta-main-server/french-ai-accounting-saas-backend-tmp
$backendPath = (Resolve-Path (Join-Path $projectRoot "..\french-ai-accounting-saas-backend-tmp")).Path

Write-Host "Running migrations via Docker (container network)..." -ForegroundColor Cyan
docker run --rm --network french-accounting-ai-saas-infra-tmp_dou-network `
  -e DATABASE_URL=postgresql://dou_user:dou_password123@postgres:5432/dou_expense_audit `
  -v "${backendPath}:/app" `
  -w /app python:3.12-slim `
  bash -c "pip install -q asyncpg python-dotenv && python scripts/run_all_migrations.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nMigrations completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nMigrations failed." -ForegroundColor Red
    exit 1
}
