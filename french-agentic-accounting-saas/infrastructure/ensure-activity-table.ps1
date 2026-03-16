# Fix Activity Log: create table if missing, rebuild admin (so it has GET /activity), restart admin.
# Run from project root: .\infrastructure\ensure-activity-table.ps1
# Requires: docker compose (postgres will be started if needed).

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sqlPath = Join-Path $scriptDir "ensure-activity-table.sql"

Write-Host "Ensuring postgres is up..." -ForegroundColor Cyan
cmd /c "docker compose -f infrastructure/docker-compose.yml up -d postgres 2>nul"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Start-Sleep -Seconds 3

Write-Host "Creating activity table if missing..." -ForegroundColor Cyan
Get-Content -Raw $sqlPath | docker compose -f infrastructure/docker-compose.yml exec -T postgres psql -U dou_user -d dou_expense_audit
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Rebuilding admin image (so it includes the Activity Log API)..." -ForegroundColor Cyan
docker compose -f infrastructure/docker-compose.yml build admin
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Starting admin service..." -ForegroundColor Cyan
cmd /c "docker compose -f infrastructure/docker-compose.yml up -d admin 2>nul"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nDone. Open the Activity Log tab and refresh; new user/role changes will appear." -ForegroundColor Green
