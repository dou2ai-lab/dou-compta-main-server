# Test RAG pipeline: health, /qa (RAG query type), /copilot, /search.
# Requires: Auth (8001) and RAG (8018) running. Usage: .\scripts\test-rag-pipeline.ps1

$ErrorActionPreference = "Continue"
$baseRag = "http://localhost:8018"
$token = "dev_mock_token_local"
$headers = @{ "Authorization" = "Bearer $token"; "Content-Type" = "application/json" }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "RAG Pipeline Tests" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 1) RAG health
Write-Host "1. RAG health (8018)..." -NoNewline
try {
    $r = Invoke-RestMethod -Uri "$baseRag/health" -Method GET -TimeoutSec 5
    if ($r.status -eq "healthy") { Write-Host " OK" -ForegroundColor Green } else { Write-Host " unexpected: $r" -ForegroundColor Yellow }
} catch {
    Write-Host " FAIL (start RAG: cd backend; uvicorn services.rag_service.main:app --host 0.0.0.0 --port 8018)" -ForegroundColor Red
    exit 1
}

# 2) RAG Q&A (query_type=rag) - RAG retrieval path
Write-Host "2. RAG /qa (query_type=rag)..." -NoNewline
try {
    $body = '{"question":"What are high-risk expenses?","query_type":"rag"}'
    $r = Invoke-RestMethod -Uri "$baseRag/api/v1/rag/qa" -Method POST -Headers $headers -Body $body -TimeoutSec 45
    if ($r.answer -ne $null -or $r.success -eq $true) {
        Write-Host " OK" -ForegroundColor Green
        if ($r.answer) { Write-Host "   Answer length: $($r.answer.Length) chars" -ForegroundColor Gray }
    } else { Write-Host " no answer in response" -ForegroundColor Yellow }
} catch {
    Write-Host " FAIL/SKIP: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 3) RAG Co-Pilot (agentic)
Write-Host "3. RAG /copilot (agentic)..." -NoNewline
try {
    $body = '{"query":"What expenses are high risk?"}'
    $r = Invoke-RestMethod -Uri "$baseRag/api/v1/rag/copilot" -Method POST -Headers $headers -Body $body -TimeoutSec 60
    if ($r.answer) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "   Answer length: $($r.answer.Length) chars" -ForegroundColor Gray
        if ($r.citations -and $r.citations.Count -gt 0) { Write-Host "   Citations: $($r.citations.Count)" -ForegroundColor Gray }
    } else { Write-Host " no answer" -ForegroundColor Yellow }
} catch {
    Write-Host " FAIL/SKIP: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 4) RAG search (semantic search)
Write-Host "4. RAG /search (semantic)..." -NoNewline
try {
    $body = '{"query":"VAT rules and expense policy","document_types":["policy","knowledge"],"top_k":5}'
    $r = Invoke-RestMethod -Uri "$baseRag/api/v1/rag/search" -Method POST -Headers $headers -Body $body -TimeoutSec 30
    if ($r.results -ne $null) {
        Write-Host " OK (results=$($r.results.Count))" -ForegroundColor Green
    } else { Write-Host " OK (no results)" -ForegroundColor Green }
} catch {
    Write-Host " FAIL/SKIP: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "RAG pipeline tests done. Fix any FAIL; SKIP can be due to RAG still loading (wait and re-run)." -ForegroundColor Cyan
