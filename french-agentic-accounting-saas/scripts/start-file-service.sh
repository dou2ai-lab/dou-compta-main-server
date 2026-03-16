#!/bin/bash
# Start only the File Service (port 8005) for receipt upload
# Usage: ./scripts/start-file-service.sh

set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"
cd "$BACKEND_DIR"

[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

[ ! -f ".env" ] && [ -f ".env.example" ] && cp .env.example .env && echo "Created .env from .env.example. Set JWT_SECRET to match auth-service-node."
export DATABASE_URL="${DATABASE_URL:-postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit}"

echo "Starting File Service on http://localhost:8005 ..."
exec uvicorn services.file_service.main:app --reload --port 8005
