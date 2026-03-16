# Reset PostgreSQL (remove volume) and start fresh with trust auth for local dev
# Fixes: InvalidPasswordError when backend on Windows connects to Postgres in Docker
# Usage: .\scripts\reset-db-and-start.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$infraPath = Join-Path $projectRoot "infrastructure"

Write-Host "Resetting database and starting Postgres with trust auth..." -ForegroundColor Cyan
Set-Location $infraPath

docker compose down -v
docker compose up -d --build

Write-Host "`nWaiting for Postgres to be ready..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
do {
    Start-Sleep -Seconds 2
    $healthy = docker inspect dou-postgres --format '{{.State.Health.Status}}' 2>$null
    if ($healthy -eq "healthy") { break }
    $attempt++
    Write-Host "  Attempt $attempt/$maxAttempts..."
} while ($attempt -lt $maxAttempts)

if ($attempt -ge $maxAttempts) {
    Write-Host "Postgres did not become healthy. Check: docker logs dou-postgres" -ForegroundColor Red
    exit 1
}

Write-Host "`nPostgres is ready. Run migrations:" -ForegroundColor Green
Write-Host "  cd $projectRoot" -ForegroundColor White
Write-Host "  .\scripts\run-migrations-docker.ps1" -ForegroundColor White
Set-Location $projectRoot
