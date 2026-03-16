#!/bin/bash
# Bash script to start backend services locally
# Usage: ./scripts/start-backend-local.sh

set -e

echo "=========================================="
echo "Starting Backend Services Locally"
echo "=========================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"

cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please update .env with your database URL: postgresql://dou_user:dou_password@localhost:5432/dou_expense_audit"
    else
        echo "⚠️  .env.example not found. Please create .env manually."
    fi
fi

# Set default DATABASE_URL if not in .env
export DATABASE_URL="${DATABASE_URL:-postgresql://dou_user:dou_password@localhost:5432/dou_expense_audit}"

echo ""
echo "Starting backend services..."
echo "Note: Each service will run in a separate terminal."
echo ""

# Start services in background
services=(
    "Auth Service:8001:services.auth.main:app"
    "Expense Service:8002:services.expense.main:app"
    "Admin Service:8003:services.admin.main:app"
    "Audit Service:8004:services.audit.main:app"
)

for service_info in "${services[@]}"; do
    IFS=':' read -r name port service <<< "$service_info"
    echo "Starting $name on port $port..."
    gnome-terminal -- bash -c "cd '$BACKEND_DIR' && source venv/bin/activate && export DATABASE_URL='$DATABASE_URL' && uvicorn $service --reload --port $port; exec bash" 2>/dev/null || \
    xterm -e "cd '$BACKEND_DIR' && source venv/bin/activate && export DATABASE_URL='$DATABASE_URL' && uvicorn $service --reload --port $port" 2>/dev/null || \
    osascript -e "tell app \"Terminal\" to do script \"cd '$BACKEND_DIR' && source venv/bin/activate && export DATABASE_URL='$DATABASE_URL' && uvicorn $service --reload --port $port\"" 2>/dev/null || \
    echo "⚠️  Could not open new terminal. Run manually: uvicorn $service --reload --port $port"
    sleep 2
done

echo ""
echo "✅ Backend services started!"
echo "Services are running in separate terminals."
echo ""
echo "Service URLs:"
for service_info in "${services[@]}"; do
    IFS=':' read -r name port service <<< "$service_info"
    echo "  $name: http://localhost:$port"
done
echo ""

cd "$PROJECT_ROOT"
