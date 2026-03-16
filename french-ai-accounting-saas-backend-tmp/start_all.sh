#!/bin/bash
# Start ALL DouCompta backend services
# Usage: cd backend && bash start_all.sh

echo "============================================"
echo "  DouCompta V4.0 - Starting ALL services"
echo "============================================"

# Kill any existing uvicorn processes
pkill -f "uvicorn services" 2>/dev/null
sleep 1

# Core services (Phase 0 - pre-existing)
python -m uvicorn services.auth.main:app --host 0.0.0.0 --port 8001 &
python -m uvicorn services.expense.main:app --host 0.0.0.0 --port 8002 &
python -m uvicorn services.admin.main:app --host 0.0.0.0 --port 8003 &
python -m uvicorn services.audit.main:app --host 0.0.0.0 --port 8004 &
python -m uvicorn services.policy_service.main:app --host 0.0.0.0 --port 8008 &
python -m uvicorn services.report_service.main:app --host 0.0.0.0 --port 8009 &
python -m uvicorn services.anomaly_service.main:app --host 0.0.0.0 --port 8010 &

# V4 services (Phases 1-10)
python -m uvicorn services.accounting_service.main:app --host 0.0.0.0 --port 8019 &
python -m uvicorn services.dossier_service.main:app --host 0.0.0.0 --port 8023 &
python -m uvicorn services.notification_service.main:app --host 0.0.0.0 --port 8024 &
python -m uvicorn services.banking_service.main:app --host 0.0.0.0 --port 8025 &
python -m uvicorn services.tax_service.main:app --host 0.0.0.0 --port 8026 &
python -m uvicorn services.analysis_service.main:app --host 0.0.0.0 --port 8027 &
python -m uvicorn services.einvoice_service.main:app --host 0.0.0.0 --port 8028 &
python -m uvicorn services.payroll_service.main:app --host 0.0.0.0 --port 8029 &
python -m uvicorn services.collection_service.main:app --host 0.0.0.0 --port 8030 &
python -m uvicorn services.agents_service.main:app --host 0.0.0.0 --port 8031 &

echo ""
echo "17 services starting on ports:"
echo "  Auth:8001 Expense:8002 Admin:8003 Audit:8004"
echo "  Policy:8008 Report:8009 Anomaly:8010"
echo "  Accounting:8019 Dossier:8023 Notification:8024"
echo "  Banking:8025 Tax:8026 Analysis:8027"
echo "  E-Invoice:8028 Payroll:8029 Collection:8030 Agents:8031"
echo ""
echo "Waiting for services to start..."
sleep 5

# Health check
echo ""
echo "=== Health Check ==="
for port in 8001 8002 8003 8004 8008 8009 8010 8019 8023 8024 8025 8026 8027 8028 8029 8030 8031; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" 2>/dev/null)
    if [ "$status" = "200" ]; then
        echo "  OK  :$port"
    else
        echo "  FAIL:$port (HTTP $status)"
    fi
done

echo ""
echo "============================================"
echo "  All services started. Press Ctrl+C to stop"
echo "============================================"
wait
