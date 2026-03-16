#!/bin/bash
# health-check.sh - Verify all services are healthy

set -e

SERVICES=(
  "http://localhost:8001/health:Auth"
  "http://localhost:8002/health:Expense"
  "http://localhost:8003/health:Admin"
  "http://localhost:8004/health:Audit"
  "http://localhost:8005/health:File"
  "http://localhost:8006/health:OCR"
  "http://localhost:8007/health:LLM"
  "http://localhost:8008/health:Policy"
  "http://localhost:8009/health:Report"
  "http://localhost:8010/health:Anomaly"
  "http://localhost:8011/health:ERP"
  "http://localhost:8012/health:GDPR"
  "http://localhost:8013/health:Performance"
  "http://localhost:8014/health:Security"
  "http://localhost:8015/health:Monitoring"
)

echo "Running health checks..."

FAILED=0

for service in "${SERVICES[@]}"; do
  IFS=':' read -r url name <<< "$service"
  if curl -f -s "$url" > /dev/null 2>&1; then
    echo "✅ $name service is healthy"
  else
    echo "❌ $name service is unhealthy"
    FAILED=$((FAILED + 1))
  fi
done

if [ $FAILED -eq 0 ]; then
  echo ""
  echo "All services are healthy!"
  exit 0
else
  echo ""
  echo "$FAILED service(s) failed health checks"
  exit 1
fi



