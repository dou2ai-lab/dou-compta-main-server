# Seed expense categories via Docker (uses same Postgres connection as app).
# Use this when running the script on the host fails (e.g. password auth from host to Docker Postgres).
# Mounts current backend code so no image rebuild is needed.
# Usage: .\scripts\seed-categories-docker.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$backendPath = Join-Path $projectRoot "backend"

Write-Host "Seeding categories via Docker (admin image + current backend mount)..." -ForegroundColor Cyan
docker run --rm --network infrastructure_dou-network `
  -e DATABASE_URL=postgresql://dou_user:dou_password123@postgres:5432/dou_expense_audit `
  -v "${backendPath}:/app" `
  -w /app `
  dou-admin:local `
  python scripts/seed_categories.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nCategories seeded successfully!" -ForegroundColor Green
} else {
    Write-Host "`nSeeding failed. Ensure dou-postgres is running and dou-admin image exists (e.g. docker compose -f infrastructure/docker-compose.yml up -d --build)." -ForegroundColor Red
    exit 1
}
