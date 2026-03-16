# Start only the Auth service (port 8001) - keeps window open so you can see errors
# Double-click or run: .\scripts\start-auth-only.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$backendPath = Join-Path $projectRoot "backend"

Set-Location $backendPath

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Error: venv not found. Run from project root first." -ForegroundColor Red
    pause
    exit 1
}

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
}

Write-Host "Starting Auth Service on http://localhost:8001 ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

& ".\venv\Scripts\Activate.ps1"
uvicorn services.auth.main:app --host 0.0.0.0 --port 8001

pause
