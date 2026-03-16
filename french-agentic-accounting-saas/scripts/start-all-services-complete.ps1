# PowerShell script to start ALL services (database, migrations, backend, frontend)
# Usage: .\scripts\start-all-services-complete.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting All Services" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend-web"
$infraPath = Join-Path $projectRoot "infrastructure"

# Step 1: Start Database
Write-Host "Step 1: Starting PostgreSQL database..." -ForegroundColor Yellow
Set-Location $infraPath
docker-compose up -d postgres

Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 2: Run Migrations
Write-Host ""
Write-Host "Step 2: Running database migrations..." -ForegroundColor Yellow
Set-Location $backendPath

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

& ".\venv\Scripts\Activate.ps1"
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python scripts/run_all_migrations.py

Write-Host ""
Write-Host "Step 3: Starting backend services..." -ForegroundColor Yellow
Write-Host "Each service will open in a separate window." -ForegroundColor Gray
Write-Host ""

# Define all services including file and OCR
$services = @(
    @{Name="Auth Service"; Port=8001; Service="services.auth.main:app"},
    @{Name="Expense Service"; Port=8002; Service="services.expense.main:app"},
    @{Name="Admin Service"; Port=8003; Service="services.admin.main:app"},
    @{Name="Audit Service"; Port=8004; Service="services.audit.main:app"},
    @{Name="File Service"; Port=8005; Service="services.file_service.main:app"},
    @{Name="OCR Service"; Port=8006; Service="services.ocr_service.main:app"}
)

foreach ($svc in $services) {
    Write-Host "Starting $($svc.Name) on port $($svc.Port)..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit'; python -m uvicorn $($svc.Service) --reload --port $($svc.Port)"
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "Step 4: Starting frontend..." -ForegroundColor Yellow
Set-Location $frontendPath
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendPath'; npm run dev"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "All services started!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend Services:" -ForegroundColor Cyan
foreach ($svc in $services) {
    Write-Host "  $($svc.Name): http://localhost:$($svc.Port)" -ForegroundColor White
}
Write-Host ""
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Wait 10-15 seconds for all services to start, then:" -ForegroundColor Yellow
Write-Host "  1. Go to http://localhost:3000/expenses/new" -ForegroundColor White
Write-Host "  2. Upload a receipt (JPG, PNG, or PDF)" -ForegroundColor White
Write-Host "  3. OCR will extract details automatically" -ForegroundColor White
Write-Host "  4. Fill the form and submit" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot
