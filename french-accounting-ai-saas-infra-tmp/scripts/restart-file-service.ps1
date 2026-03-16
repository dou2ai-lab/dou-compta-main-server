# Restart the File Service (port 8005)
# Usage: .\scripts\restart-file-service.ps1

$FileServicePort = 8005

# Find process using port 8005
$conn = Get-NetTCPConnection -LocalPort $FileServicePort -ErrorAction SilentlyContinue
if ($conn) {
    $pid = ($conn | Select-Object -First 1).OwningProcess
    if ($pid) {
        Write-Host "Stopping process on port $FileServicePort (PID $pid)..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
} else {
    Write-Host "No process found on port $FileServicePort." -ForegroundColor Gray
}

# Start File Service (same as start-file-service.ps1)
& "$PSScriptRoot\start-file-service.ps1"
