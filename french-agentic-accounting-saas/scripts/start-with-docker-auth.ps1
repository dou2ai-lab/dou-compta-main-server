# Start Postgres + Auth in Docker (fixes Windows host->Postgres auth issues)
# Frontend runs locally. Expense/Admin/Audit can run locally or add more services to compose.
# Usage: .\scripts\start-with-docker-auth.ps1

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$infraPath = Join-Path $projectRoot "infrastructure"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting Postgres + Auth in Docker" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $infraPath

# Stop local backend if running (ports 8001-8004)
Write-Host "Starting Postgres + Auth (slim build ~2 min first time)..." -ForegroundColor Yellow
docker compose up -d --build

Write-Host "`nWaiting for services..." -ForegroundColor Yellow
$maxAttempts = 60
$attempt = 0
do {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { break }
    } catch {}
    $attempt++
    Write-Host "  Attempt $attempt/$maxAttempts..."
} while ($attempt -lt $maxAttempts)

if ($attempt -ge $maxAttempts) {
    Write-Host "Auth service did not become ready. Check: docker logs dou-auth" -ForegroundColor Red
    Set-Location $projectRoot
    exit 1
}

Write-Host "`nPostgres + Auth are running!" -ForegroundColor Green
Write-Host "  Auth: http://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "Run migrations if needed:" -ForegroundColor Cyan
Write-Host "  .\scripts\run-migrations-docker.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Start Expense, Admin, Audit locally (optional):" -ForegroundColor Cyan
Write-Host "  .\scripts\start-backend-local.ps1" -ForegroundColor White
Write-Host "  (Auth runs in Docker; other 3 services run locally - they may still have DB auth issues)" -ForegroundColor Gray
Write-Host ""
Write-Host "Start frontend:" -ForegroundColor Cyan
Write-Host "  cd frontend-web; npm run dev" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot
