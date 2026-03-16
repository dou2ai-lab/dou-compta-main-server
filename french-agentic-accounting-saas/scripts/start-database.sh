#!/bin/bash
# Bash script to start only the database container
# Usage: ./scripts/start-database.sh

set -e

echo "=========================================="
echo "Starting PostgreSQL Database Container"
echo "=========================================="
echo ""

# Navigate to infrastructure directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
INFRA_DIR="$PROJECT_ROOT/infrastructure"

cd "$INFRA_DIR"

# Start only the postgres service
echo "Starting PostgreSQL container..."
docker-compose up -d postgres

# Wait for database to be ready
echo "Waiting for database to be ready..."
max_retries=30
retry_count=0
is_ready=false

while [ $retry_count -lt $max_retries ] && [ "$is_ready" = false ]; do
    sleep 2
    if docker-compose exec -T postgres pg_isready -U dou_user -d dou_expense_audit > /dev/null 2>&1; then
        is_ready=true
        echo "✅ PostgreSQL is ready!"
    else
        retry_count=$((retry_count + 1))
        echo "Waiting... ($retry_count/$max_retries)"
    fi
done

if [ "$is_ready" = false ]; then
    echo "❌ PostgreSQL failed to start within timeout period"
    exit 1
fi

echo ""
echo "Database connection details:"
echo "  Host: localhost"
echo "  Port: 5432"
echo "  User: dou_user"
echo "  Password: dou_password"
echo "  Database: dou_expense_audit"
echo ""
echo "To stop the database, run: docker-compose down"
echo ""

cd "$PROJECT_ROOT"
