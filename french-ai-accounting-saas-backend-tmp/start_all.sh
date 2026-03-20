#!/bin/bash
# Start ALL DouCompta backend services
# Usage: cd backend && bash start_all.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REQ_FILE="${SCRIPT_DIR}/requirements-slim.txt"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "============================================"
echo "  DouCompta V4.0 - Starting ALL services"
echo "============================================"

# Ensure we can run uvicorn.
# 1) macOS may not have a `python` shim => we use `python3`
# 2) If deps aren't installed, create/use `.venv` and install `requirements-slim.txt`
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not available on PATH."
  echo "Install Python 3 and re-run: bash start_all.sh"
  exit 1
fi

if [ -x "${VENV_DIR}/bin/python" ]; then
  PYBIN="${VENV_DIR}/bin/python"
else
  PYBIN="$(command -v python3)"
fi
LAUNCH_PYBIN="${PYBIN}"

if ! "${PYBIN}" -c "import uvicorn" >/dev/null 2>&1; then
  # Create venv if missing, then install deps.
  if [ ! -x "${VENV_DIR}/bin/python" ]; then
    echo "Creating virtualenv at ${VENV_DIR} ..."
    python3 -m venv "${VENV_DIR}" || { echo "ERROR: could not create venv"; exit 1; }
  fi
  echo "Installing backend dependencies (uvicorn, fastapi, etc.) ..."
  "${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
  "${VENV_DIR}/bin/python" -m pip install -r "${REQ_FILE}" || {
    echo "ERROR: failed to install dependencies from ${REQ_FILE}"
    echo "Try running: ${VENV_DIR}/bin/python -m pip install -r \"${REQ_FILE}\""
    exit 1
  }
  LAUNCH_PYBIN="${VENV_DIR}/bin/python"
fi

# SQLAlchemy async requires `greenlet`.
# Install it if missing (covers cases where .venv already existed before requirements changed).
if ! "${PYBIN}" -c "import greenlet" >/dev/null 2>&1; then
  echo "Installing missing dependency: greenlet ..."
  "${PYBIN}" -m pip install "greenlet>=1.1.0" || {
    echo "ERROR: failed to install greenlet"
    exit 1
  }
fi

# Anomaly service imports sklearn (IsolationForest).
if ! "${PYBIN}" -c "import sklearn" >/dev/null 2>&1; then
  echo "Installing missing dependency: scikit-learn ..."
  "${PYBIN}" -m pip install "scikit-learn>=1.3.0" || {
    echo "ERROR: failed to install scikit-learn"
    exit 1
  }
fi

# Ensure core DB tables exist (some environments/images add new models later).
# This is safe for local/dev and avoids runtime 500s when tables are missing.
echo "Ensuring DB tables exist (create_tables.py) ..."
"${LAUNCH_PYBIN}" "${SCRIPT_DIR}/create_tables.py" || {
  echo "WARNING: create_tables.py failed; continuing to start services."
}

# Kill any existing uvicorn processes
pkill -f "uvicorn services" 2>/dev/null
sleep 1

# Core services (Phase 0 - pre-existing)
# macOS often does not ship with a `python` shim; prefer `python3`.
"${LAUNCH_PYBIN}" -m uvicorn services.auth.main:app --host 0.0.0.0 --port 8001 &
"${LAUNCH_PYBIN}" -m uvicorn services.expense.main:app --host 0.0.0.0 --port 8002 &
"${LAUNCH_PYBIN}" -m uvicorn services.admin.main:app --host 0.0.0.0 --port 8003 &
"${LAUNCH_PYBIN}" -m uvicorn services.audit.main:app --host 0.0.0.0 --port 8004 &
"${LAUNCH_PYBIN}" -m uvicorn services.policy_service.main:app --host 0.0.0.0 --port 8008 &
"${LAUNCH_PYBIN}" -m uvicorn services.report_service.main:app --host 0.0.0.0 --port 8009 &
"${LAUNCH_PYBIN}" -m uvicorn services.anomaly_service.main:app --host 0.0.0.0 --port 8010 &

# V4 services (Phases 1-10)
"${LAUNCH_PYBIN}" -m uvicorn services.accounting_service.main:app --host 0.0.0.0 --port 8019 &
"${LAUNCH_PYBIN}" -m uvicorn services.dossier_service.main:app --host 0.0.0.0 --port 8023 &
"${LAUNCH_PYBIN}" -m uvicorn services.notification_service.main:app --host 0.0.0.0 --port 8024 &
"${LAUNCH_PYBIN}" -m uvicorn services.banking_service.main:app --host 0.0.0.0 --port 8025 &
"${LAUNCH_PYBIN}" -m uvicorn services.tax_service.main:app --host 0.0.0.0 --port 8026 &
"${LAUNCH_PYBIN}" -m uvicorn services.analysis_service.main:app --host 0.0.0.0 --port 8027 &
"${LAUNCH_PYBIN}" -m uvicorn services.einvoice_service.main:app --host 0.0.0.0 --port 8028 &
"${LAUNCH_PYBIN}" -m uvicorn services.payroll_service.main:app --host 0.0.0.0 --port 8029 &
"${LAUNCH_PYBIN}" -m uvicorn services.collection_service.main:app --host 0.0.0.0 --port 8030 &
"${LAUNCH_PYBIN}" -m uvicorn services.agents_service.main:app --host 0.0.0.0 --port 8031 &

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
