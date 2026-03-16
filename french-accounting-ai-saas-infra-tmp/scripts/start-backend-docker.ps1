# Start full backend stack with Docker Compose and run migrations.
# Frontend runs locally: cd frontend-web && npm run dev
# Usage: .\scripts\start-backend-docker.ps1
#        .\scripts\start-backend-docker.ps1 -Clean   # Reset DB volume and start fresh

param([switch]$Clean)

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$infraPath = Join-Path $projectRoot "infrastructure"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Backend stack (Docker Compose)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure we use the compose file from infrastructure so network name is consistent (infrastructure_dou-network)
Set-Location $infraPath

if ($Clean) {
    Write-Host "Clean start: removing containers and volumes..." -ForegroundColor Yellow
    docker compose down -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "docker compose down failed." -ForegroundColor Red
        Set-Location $projectRoot
        exit 1
    }
    Write-Host ""
}

Write-Host "Building images..." -ForegroundColor Yellow
docker compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed." -ForegroundColor Red
    Set-Location $projectRoot
    exit 1
}

Write-Host ""
Write-Host "Starting containers..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "docker compose up failed." -ForegroundColor Red
    Set-Location $projectRoot
    exit 1
}

Write-Host ""
Write-Host "Waiting for Postgres to be healthy..." -ForegroundColor Yellow
$maxWait = 90
$elapsed = 0
do {
    Start-Sleep -Seconds 5
    $elapsed += 5
    $state = docker inspect --format "{{.State.Health.Status}}" dou-postgres 2>$null
    if ($state -eq "healthy") { break }
    if ($elapsed -ge $maxWait) {
        Write-Host "Postgres did not become healthy in time." -ForegroundColor Red
        docker compose ps
        Set-Location $projectRoot
        exit 1
    }
    Write-Host "  ... waiting ($elapsed s)"
} while ($true)
Write-Host "Postgres is healthy." -ForegroundColor Green

Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Yellow
Set-Location $projectRoot
& (Join-Path $scriptPath "run-migrations-docker.ps1")
if ($LASTEXITCODE -ne 0) {
    Write-Host "Migrations failed." -ForegroundColor Red
    Write-Host "If you see 'Existing database schema detected but no schema_migrations history', run:" -ForegroundColor Yellow
    Write-Host "  .\scripts\start-backend-docker.ps1 -Clean" -ForegroundColor White
    Write-Host "  (This resets the DB volume and reapplies migrations.)" -ForegroundColor Gray
    Set-Location $projectRoot
    exit 1
}

Set-Location $infraPath
Write-Host ""
Write-Host "Waiting for backend services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Quick health check on file-service (most commonly failing)
$fileOk = $false
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8005/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($r.StatusCode -eq 200) { $fileOk = $true }
} catch {}
if (-not $fileOk) {
    Write-Host "Warning: File service (8005) not responding yet. It may still be starting." -ForegroundColor Yellow
    Write-Host "  Check: docker logs dou-file-service" -ForegroundColor Gray
} else {
    Write-Host "File service is up." -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host " Backend is running" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs (from host):" -ForegroundColor Cyan
Write-Host "  Auth:       http://localhost:8001"
Write-Host "  Expense:    http://localhost:8002"
Write-Host "  Admin:      http://localhost:8003"
Write-Host "  Audit:      http://localhost:8004"
Write-Host "  File:       http://localhost:8005"
Write-Host "  Report:     http://localhost:8009"
Write-Host ""
Write-Host "Frontend (run separately):" -ForegroundColor Cyan
Write-Host "  cd frontend-web && npm run dev"
Write-Host "  Then open http://localhost:3000"
Write-Host ""
Write-Host "Use default dev token in browser: dev_mock_token_local" -ForegroundColor Gray
Write-Host ""

Set-Location $projectRoot
