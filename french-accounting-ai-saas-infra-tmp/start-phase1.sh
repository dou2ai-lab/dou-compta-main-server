#!/bin/bash
echo "Starting DouCompta Phase 1 Infrastructure..."

docker compose -f docker-compose.db-only.yml up -d
docker compose -f docker-compose.full.yml up -d redis minio

echo "Done! Services running:"
echo "   Adminer:   http://localhost:8080"
echo "   MinIO:     http://localhost:9001"
echo "   Postgres:  localhost:5433"
echo "   Redis:     localhost:6379"
echo "   MinIO API: localhost:9000"

