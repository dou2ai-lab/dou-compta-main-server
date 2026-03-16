#!/bin/bash
# Bash script to start frontend locally
# Usage: ./scripts/start-frontend-local.sh

set -e

echo "=========================================="
echo "Starting Frontend Web Locally"
echo "=========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
FRONTEND_DIR="$PROJECT_ROOT/frontend-web"

cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo "⚠️  Warning: .env.local file not found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        echo "Please update .env.local with your API URLs"
    else
        echo "⚠️  .env.example not found. Creating default .env.local..."
        cat > .env.local << EOF
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
EOF
    fi
fi

echo ""
echo "Starting frontend development server..."
echo ""

# Start the development server
npm run dev

cd "$PROJECT_ROOT"
