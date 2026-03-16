# PowerShell script to start everything locally (database, backend, frontend)
# Usage: .\scripts\start-all-local.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting All Services Locally" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath

# Step 1: Start database
Write-Host "Step 1: Starting database..." -ForegroundColor Yellow
& "$scriptPath\start-database.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start database. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Starting backend services..." -ForegroundColor Yellow
Write-Host "Press any key to continue after database is ready..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

& "$scriptPath\start-backend-local.ps1"

Write-Host ""
Write-Host "Step 3: Starting frontend..." -ForegroundColor Yellow
Write-Host "Press any key to continue after backend services are ready..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

& "$scriptPath\start-frontend-local.ps1"

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
