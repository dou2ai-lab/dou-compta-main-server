-- DouCompta Phase 1 — Required PostgreSQL Extensions
-- This file runs automatically on first container startup
-- Do NOT remove existing extensions, only add if not exists

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create doucompta database if it doesn't exist
SELECT 'CREATE DATABASE doucompta'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = 'doucompta'
)\gexec

-- Ensure required extensions exist inside doucompta database as well
\connect doucompta
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

