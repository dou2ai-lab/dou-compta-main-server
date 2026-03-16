#!/bin/bash
# start-services.sh - Production service startup script

set -e

echo "=========================================="
echo "Starting Dou Expense & Audit AI Services"
echo "=========================================="
echo ""

# Phase 1: Infrastructure
echo "Phase 1: Starting infrastructure services..."
docker-compose up -d postgres rabbitmq redis

echo "Waiting for infrastructure to be ready (30 seconds)..."
sleep 30

# Check infrastructure health
echo "Checking infrastructure health..."
if ! docker-compose exec -T postgres pg_isready -U dou_user > /dev/null 2>&1; then
  echo "❌ PostgreSQL is not ready"
  exit 1
fi
echo "✅ PostgreSQL is ready"

if ! docker-compose exec -T rabbitmq rabbitmq-diagnostics ping > /dev/null 2>&1; then
  echo "❌ RabbitMQ is not ready"
  exit 1
fi
echo "✅ RabbitMQ is ready"

if ! docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
  echo "❌ Redis is not ready"
  exit 1
fi
echo "✅ Redis is ready"

# Phase 2: Core Backend Services
echo ""
echo "Phase 2: Starting core backend services..."
docker-compose up -d backend-auth backend-file backend-expense backend-admin backend-audit

echo "Waiting for core services to start (20 seconds)..."
sleep 20

# Phase 3: Processing Services
echo ""
echo "Phase 3: Starting processing services..."
docker-compose up -d backend-ocr backend-llm backend-llm-worker

echo "Waiting for processing services (15 seconds)..."
sleep 15

# Phase 4: Supporting Services
echo ""
echo "Phase 4: Starting supporting services..."
docker-compose up -d backend-policy backend-report backend-anomaly backend-rag \
  backend-erp backend-gdpr backend-performance backend-security backend-monitoring

echo "Waiting for supporting services (15 seconds)..."
sleep 15

# Phase 5: Frontend
echo ""
echo "Phase 5: Starting frontend..."
docker-compose up -d frontend-web

echo "Waiting for frontend to start (30 seconds)..."
sleep 30

echo ""
echo "=========================================="
echo "All services started!"
echo "=========================================="
echo ""
echo "Running health checks..."
./scripts/health-check.sh

echo ""
echo "Deployment complete!"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8001/docs"



