#!/bin/bash
# Bash script to start everything locally (database, backend, frontend)
# Usage: ./scripts/start-all-local.sh

set -e

echo "=========================================="
echo "Starting All Services Locally"
echo "=========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Step 1: Start database
echo "Step 1: Starting database..."
"$SCRIPT_DIR/start-database.sh"

if [ $? -ne 0 ]; then
    echo "❌ Failed to start database. Exiting."
    exit 1
fi

echo ""
echo "Step 2: Starting backend services..."
echo "Press Enter to continue after database is ready..."
read

"$SCRIPT_DIR/start-backend-local.sh"

echo ""
echo "Step 3: Starting frontend..."
echo "Press Enter to continue after backend services are ready..."
read

"$SCRIPT_DIR/start-frontend-local.sh"

echo ""
echo "✅ All services started!"
echo ""
echo "Access the application at: http://localhost:3000"
echo ""
