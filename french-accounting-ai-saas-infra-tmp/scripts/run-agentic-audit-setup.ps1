# Run Agentic Audit & Compliance setup steps (migrations + knowledge ingest).
# Usage: .\scripts\run-agentic-audit-setup.ps1
# Prerequisite: PostgreSQL running (e.g. .\scripts\start-database.ps1)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendPath = Join-Path $projectRoot "backend"

if (-not $env:DATABASE_URL) {
    $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host 'Agentic Audit - Setup (migrations + ingest)' -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Migrations
Write-Host "Step 1: Running migrations..." -ForegroundColor Yellow
Set-Location $projectRoot
python backend/scripts/run_all_migrations.py
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host ""

# Step 2: Knowledge ingestion
Write-Host "Step 2: Ingesting knowledge documents (RAG)..." -ForegroundColor Yellow
Set-Location $backendPath
python scripts/ingest_knowledge.py
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host ""

Write-Host 'Setup done.' -ForegroundColor Green
Write-Host ""
Write-Host 'Next (manual):' -ForegroundColor Cyan
Write-Host '  - Run monitoring job: start backend, then POST .../api/v1/anomaly/jobs/run-monitoring with JWT' -ForegroundColor White
Write-Host '    Or: cd backend; .\venv\Scripts\Activate.ps1; python scripts/run_monitoring_job.py' -ForegroundColor White
Write-Host '  - Start RAG + frontend and test Audit Co-Pilot at /audit-copilot' -ForegroundColor White
Write-Host '  - See docs/HOW_TO_RUN_AND_TEST_AGENTIC_AUDIT.md for full testing' -ForegroundColor White
Write-Host ""
Set-Location $projectRoot
