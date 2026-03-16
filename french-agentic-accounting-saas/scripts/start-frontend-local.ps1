# PowerShell script to start frontend locally
# Usage: .\scripts\start-frontend-local.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting Frontend Web Locally" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$frontendPath = Join-Path $projectRoot "frontend-web"

Set-Location $frontendPath

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "⚠️  Warning: .env.local file not found. Creating from example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env.local"
        Write-Host "Please update .env.local with your API URLs" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  .env.example not found. Creating default .env.local..." -ForegroundColor Yellow
        @"
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_EXPENSE_API_URL=http://localhost:8002
NEXT_PUBLIC_ADMIN_API_URL=http://localhost:8003
NEXT_PUBLIC_AUDIT_API_URL=http://localhost:8004
NEXT_PUBLIC_POLICY_API_URL=http://localhost:8008
NEXT_PUBLIC_REPORT_API_URL=http://localhost:8009
NEXT_PUBLIC_FILE_API_URL=http://localhost:8005
NEXT_PUBLIC_ANOMALY_API_URL=http://localhost:8010
NEXT_PUBLIC_RAG_API_URL=http://localhost:8018
NEXT_PUBLIC_ERP_API_URL=http://localhost:8011
NEXT_PUBLIC_GDPR_API_URL=http://localhost:8012
NEXT_PUBLIC_PERFORMANCE_API_URL=http://localhost:8013
NEXT_PUBLIC_SECURITY_API_URL=http://localhost:8014
NEXT_PUBLIC_MONITORING_API_URL=http://localhost:8015
"@ | Out-File -FilePath ".env.local" -Encoding utf8
    }
}

Write-Host ""
Write-Host "Starting frontend development server..." -ForegroundColor Green
Write-Host ""

# Start the development server
npm run dev

Set-Location $projectRoot
