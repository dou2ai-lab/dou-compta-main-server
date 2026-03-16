# Restart backend services (Postgres, Auth, File, Expense, Report).
# Run from repo root or infrastructure folder.
# Usage: .\restart-backend.ps1   or   pwsh -File .\restart-backend.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker compose down 2>$null

Write-Host "Building report-service (and other services if needed)..." -ForegroundColor Yellow
docker compose build report-service

Write-Host "Starting all backend services..." -ForegroundColor Yellow
docker compose up -d

Write-Host "Waiting for report-service to be reachable..." -ForegroundColor Yellow
$base = "http://localhost:8009"
$maxAttempts = 30
$attempt = 0
do {
    Start-Sleep -Seconds 2
    $attempt++
    try {
        $r = Invoke-WebRequest -Uri "$base/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) {
            Write-Host "Report service is up at $base" -ForegroundColor Green
            break
        }
    } catch {
        # ignore
    }
    if ($attempt -ge $maxAttempts) {
        Write-Host "Report service did not respond at $base after ${maxAttempts} attempts. Check: docker compose logs report-service" -ForegroundColor Red
        exit 1
    }
} while ($true)

Write-Host "Backend restarted. Services: postgres:5433, auth:8001, expense:8002, file:8005, report:8009" -ForegroundColor Green
