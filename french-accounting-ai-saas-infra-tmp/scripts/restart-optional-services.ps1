# Restart RAG (8018) and Anomaly (8010) so they load updated code (e.g. permission/audit fix).
# Usage: .\scripts\restart-optional-services.ps1
# Note: Auth (8001) and Audit (8004) are started by start-backend-local.ps1; close those 5 windows and run start-backend-local.ps1 again to restart them.

$ErrorActionPreference = "Continue"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$backendPath = Join-Path $projectRoot "backend"
$dbUrl = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"

function Stop-ProcessOnPort {
    param([int]$Port)
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($conns) {
            $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($procId in $pids) {
                if ($procId -gt 0) {
                    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                    Write-Host "Stopped process $procId on port $Port" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "No process on port $Port" -ForegroundColor Gray
        }
    } catch {
        Write-Host "Port $Port : $($_.Exception.Message)" -ForegroundColor Gray
    }
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Restart optional services (RAG 8018, Anomaly 8010)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Stopping existing processes on 8018 (RAG) and 8010 (Anomaly)..." -ForegroundColor Yellow
Stop-ProcessOnPort -Port 8018
Stop-ProcessOnPort -Port 8010
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "Starting Anomaly service (8010) in new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='$dbUrl'; uvicorn services.anomaly_service.main:app --host 0.0.0.0 --port 8010"
Start-Sleep -Seconds 2

Write-Host "Starting RAG service (8018) in new window..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendPath'; .\venv\Scripts\Activate.ps1; `$env:DATABASE_URL='$dbUrl'; uvicorn services.rag_service.main:app --host 0.0.0.0 --port 8018"

Write-Host ""
Write-Host "Done. RAG and Anomaly are starting in new windows." -ForegroundColor Green
Write-Host "Wait ~30s for RAG to load, then run: .\scripts\test-agentic-audit-apis.ps1" -ForegroundColor White
Write-Host "To restart Auth/Audit/File/Expense/Admin: close their 5 windows and run .\scripts\start-backend-local.ps1" -ForegroundColor White
Write-Host ""

Set-Location $projectRoot
