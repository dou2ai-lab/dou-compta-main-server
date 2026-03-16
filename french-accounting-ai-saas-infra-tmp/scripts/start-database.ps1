# PowerShell script to start only the database container
# Usage: .\scripts\start-database.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting PostgreSQL Database Container" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to infrastructure directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$infraPath = Join-Path $projectRoot "infrastructure"

Set-Location $infraPath

# Start postgres + Adminer (db-only: no build, port 5433, Adminer on 8080)
Write-Host "Starting PostgreSQL and Adminer containers..." -ForegroundColor Yellow
docker compose -f docker-compose.db-only.yml up -d

# Wait for database to be ready
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
$maxRetries = 30
$retryCount = 0
$isReady = $false

while ($retryCount -lt $maxRetries -and -not $isReady) {
    Start-Sleep -Seconds 2
    $result = docker compose -f docker-compose.db-only.yml exec -T postgres pg_isready -U dou_user -d dou_expense_audit 2>&1
    if ($LASTEXITCODE -eq 0) {
        $isReady = $true
        Write-Host "✅ PostgreSQL is ready!" -ForegroundColor Green
    } else {
        $retryCount++
        Write-Host "Waiting... ($retryCount/$maxRetries)" -ForegroundColor Gray
    }
}

if (-not $isReady) {
    Write-Host "❌ PostgreSQL failed to start within timeout period" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Database connection details:" -ForegroundColor Cyan
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5433" -ForegroundColor White
Write-Host "  User: dou_user" -ForegroundColor White
Write-Host "  Password: dou_password123" -ForegroundColor White
Write-Host "  Database: dou_expense_audit" -ForegroundColor White
Write-Host ""
Write-Host "Web access (Adminer): http://localhost:8080" -ForegroundColor Cyan
Write-Host "  Login with: Server=postgres, User=dou_user, Password=dou_password123, Database=dou_expense_audit" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop the database, run: docker compose -f docker-compose.db-only.yml down" -ForegroundColor Yellow
Write-Host ""

Set-Location $projectRoot
