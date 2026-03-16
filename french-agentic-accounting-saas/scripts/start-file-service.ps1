# Start only the File Service (port 8005) for receipt upload
# Usage: .\scripts\start-file-service.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$backendPath = Join-Path $projectRoot "backend"

Set-Location $backendPath

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}
& ".\venv\Scripts\Activate.ps1"
pip install -q -r requirements.txt

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example. Set JWT_SECRET to match auth-service-node for receipt upload." -ForegroundColor Yellow
    }
}
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
}

Write-Host "Starting File Service on http://localhost:8005 ..." -ForegroundColor Cyan
uvicorn services.file_service.main:app --reload --port 8005
