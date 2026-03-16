# Quick check: backend and frontend services + database
# Usage: .\scripts\check-services.ps1

Write-Host ""
Write-Host "=== Service status ===" -ForegroundColor Cyan
Write-Host ""

# Docker / PostgreSQL
Write-Host "Database (Docker):" -ForegroundColor Yellow
$docker = docker ps --filter "name=dou-postgres" --format "{{.Names}} {{.Status}}" 2>$null
if ($docker) {
    Write-Host "  OK   dou-postgres - $docker" -ForegroundColor Green
} else {
    Write-Host "  DOWN dou-postgres not running. Run: cd infrastructure; docker-compose up -d postgres" -ForegroundColor Red
}
Write-Host ""

# Backend ports
$services = @(
    @{ Name = "Auth (8001)";     Port = 8001; Path = "/health" },
    @{ Name = "Expense (8002)";  Port = 8002; Path = "/health" },
    @{ Name = "Admin (8003)";   Port = 8003; Path = "/health" },
    @{ Name = "Audit (8004)";   Port = 8004; Path = "/health" },
    @{ Name = "File (8005)";     Port = 8005; Path = "/health" }
)
Write-Host "Backend:" -ForegroundColor Yellow
foreach ($s in $services) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$($s.Port)$($s.Path)" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  OK   $($s.Name)" -ForegroundColor Green
    } catch {
        Write-Host "  DOWN $($s.Name)" -ForegroundColor Red
    }
}
Write-Host ""

# Frontend
Write-Host "Frontend:" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  OK   Next.js (http://localhost:3000)" -ForegroundColor Green
} catch {
    Write-Host "  DOWN Next.js (port 3000). Run: cd frontend-web; npm run dev" -ForegroundColor Red
}
Write-Host ""
Write-Host "Done." -ForegroundColor Cyan
Write-Host ""
