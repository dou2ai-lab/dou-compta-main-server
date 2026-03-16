# Apply trust-based pg_hba.conf to running Postgres (no password required for local dev)
# Run from infrastructure/ directory: .\fix-pg-trust.ps1

docker cp pg_hba.conf dou-postgres:/tmp/pg_hba_new.conf
docker exec dou-postgres sh -c "cp /tmp/pg_hba_new.conf /var/lib/postgresql/data/pg_hba.conf"
docker restart dou-postgres
Write-Host "Restarting Postgres... waiting for healthy (up to 30s)..."
Start-Sleep -Seconds 5
$attempts = 0
while ($attempts -lt 6) {
    $status = docker inspect --format='{{.State.Health.Status}}' dou-postgres 2>$null
    if ($status -eq "healthy") { break }
    Start-Sleep -Seconds 5
    $attempts++
}
Write-Host "Done. Host connections (localhost:5433) now use trust auth - no password needed."
