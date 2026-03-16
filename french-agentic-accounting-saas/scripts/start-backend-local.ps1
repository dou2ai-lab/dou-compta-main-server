# PowerShell script to start backend services locally
# Usage: .\scripts\start-backend-local.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting Backend Services Locally" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$backendPath = Join-Path $projectRoot "backend"

Set-Location $backendPath

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Install/update dependencies (optional; skip if venv already has packages to avoid long/failing install)
if (-not (Test-Path "venv\Lib\site-packages\fastapi")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -q -r requirements.txt 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "Note: Some packages may have failed (e.g. psycopg2 on Windows). Continuing..." -ForegroundColor Yellow }
} else {
    Write-Host "Using existing venv packages." -ForegroundColor Gray
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found. Creating from example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Please update .env with your database URL: postgresql://dou_user:dou_password@localhost:5432/dou_expense_audit" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  .env.example not found. Please create .env manually." -ForegroundColor Red
    }
}

# Set default DATABASE_URL if not in .env
# Note: matches infrastructure/docker-compose.yml (host port 5433, password dou_password123)
if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
}

Write-Host ""
Write-Host "Starting backend services..." -ForegroundColor Green
Write-Host "Note: Each service will run in a separate window." -ForegroundColor Yellow
Write-Host ""

# Start services in separate PowerShell windows
$services = @(
    @{Name="Auth Service"; Port=8001; Service="services.auth.main:app"},
    @{Name="Expense Service"; Port=8002; Service="services.expense.main:app"},
    @{Name="Admin Service"; Port=8003; Service="services.admin.main:app"},
    @{Name="Audit Service"; Port=8004; Service="services.audit.main:app"},
    @{Name="File Service"; Port=8005; Service="services.file_service.main:app"},
    # Optional but important for Audit Co-Pilot / RAG-based features
    @{Name="RAG Service"; Port=8018; Service="services.rag_service.main:app"}
)

foreach ($svc in $services) {
    Write-Host "Starting $($svc.Name) on port $($svc.Port)..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='$env:DATABASE_URL'; uvicorn $($svc.Service) --reload --port $($svc.Port)"
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "✅ Backend services started!" -ForegroundColor Green
Write-Host "Services are running in separate windows." -ForegroundColor White
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
foreach ($svc in $services) {
    Write-Host "  $($svc.Name): http://localhost:$($svc.Port)" -ForegroundColor White
}
Write-Host ""

Set-Location $projectRoot
