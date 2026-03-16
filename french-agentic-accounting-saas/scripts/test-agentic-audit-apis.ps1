# Test Agentic Audit APIs. Requires: backend running (auth 8001, audit 8004, optional anomaly 8010, RAG 8018).
# Usage: .\scripts\test-agentic-audit-apis.ps1

$ErrorActionPreference = "Continue"
$baseAuth = "http://localhost:8001"
$baseAudit = "http://localhost:8004"
$baseAnomaly = "http://localhost:8010"
$baseRag = "http://localhost:8018"
$token = "dev_mock_token_local"
$headers = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Agentic Audit - API tests" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1) Auth health
Write-Host "1. Auth health (8001)..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri "$baseAuth/health" -Method GET -TimeoutSec 3
    if ($r.status -eq "healthy") { Write-Host " OK" -ForegroundColor Green } else { Write-Host " unexpected: $r" -ForegroundColor Yellow }
} catch {
    Write-Host " FAIL (start auth service)" -ForegroundColor Red
}

# 2) Audit health
Write-Host "2. Audit health (8004)..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri "$baseAudit/health" -Method GET -TimeoutSec 3
    if ($r.status -eq "healthy") { Write-Host " OK" -ForegroundColor Green } else { Write-Host " unexpected: $r" -ForegroundColor Yellow }
} catch {
    Write-Host " FAIL (start audit service)" -ForegroundColor Red
}

# 3) Generate basic report (audit)
Write-Host "3. Audit generate-basic (8004)..." -NoNewline
try {
    $body = '{"period_start":"2025-01-01","period_end":"2025-12-31"}' 
    $r = Invoke-RestMethod -Uri "$baseAudit/api/v1/audit/reports/generate-basic" -Method POST -Headers $headers -Body $body -TimeoutSec 10
    if ($r.executive_summary -ne $null) { Write-Host " OK (executive_summary + top_risk_* present)" -ForegroundColor Green }
    elseif ($r.report_period) { Write-Host " OK (report generated)" -ForegroundColor Green }
    else { Write-Host " unexpected response" -ForegroundColor Yellow }
} catch {
    Write-Host " FAIL: $($_.Exception.Message)" -ForegroundColor Red
}

# 4) Anomaly monitoring job (optional)
Write-Host "4. Anomaly run-monitoring (8010)..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri "$baseAnomaly/api/v1/anomaly/jobs/run-monitoring?limit=50&lookback_days=90" -Method POST -Headers $headers -TimeoutSec 60
    if ($r.success) { Write-Host " OK (processed=$($r.result.processed))" -ForegroundColor Green } else { Write-Host " $r" -ForegroundColor Yellow }
} catch {
    Write-Host " SKIP (anomaly service not running or error)" -ForegroundColor Yellow
}

# 5) RAG Co-Pilot (optional)
Write-Host "5. RAG Co-Pilot (8018)..." -NoNewline
try {
    $body = '{"query":"What expenses are high risk?"}'
    $r = Invoke-RestMethod -Uri "$baseRag/api/v1/rag/copilot" -Method POST -Headers $headers -Body $body -TimeoutSec 15
    if ($r.answer) { Write-Host " OK" -ForegroundColor Green } else { Write-Host " no answer" -ForegroundColor Yellow }
} catch {
    Write-Host " SKIP (RAG service not running or error)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done. Fix any FAIL and run again; SKIP is optional (anomaly/RAG)." -ForegroundColor Cyan
