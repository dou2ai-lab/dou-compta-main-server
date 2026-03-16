# Dou Expense & Audit AI – Complete Setup Guide

This guide provides detailed, step-by-step instructions to set up and run the **Dou Expense & Audit AI** project locally. Follow each section in order for a successful setup.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Backend Environment Setup](#3-backend-environment-setup)
4. [Start Database and Backend Services](#4-start-database-and-backend-services)
5. [Bootstrap the Database](#5-bootstrap-the-database)
6. [Frontend Setup](#6-frontend-setup)
7. [Verify and Log In](#7-verify-and-log-in)
8. [Full Stack (Optional – Workers, Redis, RabbitMQ, MinIO)](#8-full-stack-optional--workers-redis-rabbitmq-minio)
9. [Alternative: macOS / Linux Commands](#9-alternative-macos--linux-commands)
10. [Service Ports Reference](#10-service-ports-reference)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

Before starting, ensure the following are installed on your machine:

| Requirement        | Version   | Purpose                                                       |
|--------------------|-----------|---------------------------------------------------------------|
| **Docker**         | Latest    | Runs PostgreSQL and backend microservices in containers       |
| **Docker Compose** | v2.0+     | Orchestrates multi-container setup                            |
| **Node.js**        | 18+       | Required for the Next.js frontend                             |
| **PowerShell**     | 5.1+      | For running bootstrap scripts on Windows                      |
| **Git**            | Latest    | For cloning the repository                                    |

- **Windows users:** Use PowerShell (included with Windows) to run the bootstrap script.
- **macOS/Linux users:** Use bash and run equivalent commands manually (see [Section 9](#9-alternative-macos--linux-commands)).

### Verify installations

```powershell
docker --version
docker compose version
node --version
git --version
```

---

## 2. Clone the Repository

Clone the repository and navigate to the project root:

```powershell
git clone <repository-url>
cd french-agentic-accounting-saas
```

**Important:** All subsequent commands should be run from this project root directory unless stated otherwise.

---

## 3. Backend Environment Setup

The backend uses environment variables from a `.env` file. This file is **not** committed to the repository for security reasons.

### Step 3.1: Create the backend `.env` file

```powershell
cd backend
copy .env.example .env
cd ..
```

(On macOS/Linux: `cp .env.example .env`)

### Step 3.2: Edit `backend/.env`

Open `backend/.env` and configure these variables:

| Variable        | Required | Description                                                                 |
|-----------------|----------|-----------------------------------------------------------------------------|
| `DATABASE_URL`  | Yes*     | PostgreSQL connection string. For Docker, use: `postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit` |
| `JWT_SECRET`    | **Yes**  | Must match across all services. Use: `9f3b6c7e8a1d2f4c6b8e0a3d5f7c9e1b2d4a6c8e0f3b5d7a9c1e2f4a6b8c0d2` (same as in docker-compose) or your own long random string. |
| `GEMINI_API_KEY`| Optional | Required only for receipt extraction/LLM features. Get from [Google AI Studio](https://aistudio.google.com/). Can leave as placeholder if not using OCR/LLM. |

\*`DATABASE_URL` is needed only if you run backend scripts from the host. When using Docker, the compose file sets it inside containers.

### Step 3.3: Other variables (defaults are fine for local dev)

- `STORAGE_PROVIDER=local` – Uses local file storage
- `ENCRYPTION_ENABLED=false` – Disabled for local development
- `OCR_PROVIDER=tesseract` – Default OCR engine (Tesseract is installed in the Docker image)
- `LLM_PROVIDER=gemini` – For post-processing extracted text

---

## 4. Start Database and Backend Services

From the **project root** directory:

```powershell
docker compose -f infrastructure/docker-compose.yml up -d
```

This starts:

- **PostgreSQL** on port `5433`
- **Auth** service on port `8001`
- **Expense** service on port `8002`
- **Admin** service on port `8003`
- **File Service** on port `8005`
- **Report Service** on port `8009`

**First run:** Building Docker images can take several minutes (typically 2–5 minutes).

### Wait for services to be healthy

PostgreSQL has a health check and other services wait for it. Allow **30–60 seconds** for everything to be ready.

### Optional: Check service status

```powershell
docker compose -f infrastructure/docker-compose.yml ps
```

You should see containers running, with `dou-postgres` marked healthy.

---

## 5. Bootstrap the Database

After the first `docker compose up`, or after `docker compose down -v`, the database is empty. Run the bootstrap script **once per fresh database**:

```powershell
.\infrastructure\bootstrap-db.ps1
```

This script:

1. **Creates all tables** – Uses `create_tables.py` to set up the full schema
2. **Seeds base data** – Tenant, permissions, roles, and default users
3. **Seeds PRD roles** – Admin, employee, approver, finance roles

If you see errors like *"relation tenants does not exist"*, ensure:
- Step 4 completed successfully
- Postgres is healthy (`docker ps`)
- Then run the bootstrap script again

---

## 6. Frontend Setup

### Step 6.1: Install dependencies

```powershell
cd frontend-web
npm install
```

### Step 6.2: (Optional) Configure frontend environment

If you need to override API URLs (e.g., different host/ports):

```powershell
copy .env.example .env.local
```

Then edit `frontend-web/.env.local`. Defaults point to `localhost:8001`, `localhost:8002`, etc., which match the Docker setup.

### Step 6.3: Start the development server

```powershell
npm run dev
```

The frontend will be available at **http://localhost:3000**.

---

## 7. Verify and Log In

### Access the application

1. Open a browser and go to **http://localhost:3000**
2. Use one of the seed users below (password for all is **`password`**):

| Email                  | Role     |
|------------------------|----------|
| `admin@example.com`    | Admin    |
| `approver@example.com` | Approver |
| `finance@example.com`  | Finance  |
| `user@example.com`     | Employee |

### Quick health checks

- **Auth API docs:** http://localhost:8001/docs  
- **Expense API docs:** http://localhost:8002/docs  
- **File Service health:** http://localhost:8005/health  

---

## 8. Full Stack (Optional – Workers, Redis, RabbitMQ, MinIO)

For heavy processing (OCR extraction, report export, CSV/Excel generation), run the full stack with workers and supporting services.

### Step 8.1: Stop the basic stack (if running)

```powershell
docker compose -f infrastructure/docker-compose.yml down
```

### Step 8.2: Start the full stack

From the project root:

```powershell
docker compose -f infrastructure/docker-compose.yml -f infrastructure/docker-compose.full.yml up -d
```

This adds:

- **Redis** (port 6379)
- **RabbitMQ** (5672 AMQP, 15672 management UI)
- **MinIO** (9000 API, 9001 console)
- **OCR worker** – Consumes receipt upload events, runs OCR + LLM extraction
- **Export worker** – Generates CSV/Excel reports

### Step 8.3: Ensure `backend/.env` is configured

The file service and workers read from `backend/.env`. Ensure `GEMINI_API_KEY` is set if you use receipt extraction.

### Step 8.4: Frontend

Run the frontend as usual:

```powershell
cd frontend-web
npm run dev
```

Report export (CSV/Excel) and evidence pack downloads work when the export worker is running.

---

## 9. Alternative: macOS / Linux Commands

If you're not on Windows, use these equivalents:

### Create backend `.env`

```bash
cd backend
cp .env.example .env
# Edit .env as described in Section 3
cd ..
```

### Start services

```bash
docker compose -f infrastructure/docker-compose.yml up -d
```

### Bootstrap database (manual equivalent)

```bash
DB_URL="postgresql+asyncpg://dou_user:dou_password123@postgres:5432/dou_expense_audit"

docker compose -f infrastructure/docker-compose.yml run --rm -e "DATABASE_URL=$DB_URL" auth python create_tables.py
docker compose -f infrastructure/docker-compose.yml run --rm -e "DATABASE_URL=$DB_URL" -e "BOOTSTRAP_SKIP_CREATE=1" auth python scripts/seed_data.py
docker compose -f infrastructure/docker-compose.yml run --rm -e "SEED_DATABASE_URL=$DB_URL" auth python scripts/seed_roles.py
```

### Frontend

```bash
cd frontend-web
npm install
npm run dev
```

---

## 10. Service Ports Reference

| Service          | Port   | URL                          |
|------------------|--------|------------------------------|
| Frontend         | 3000   | http://localhost:3000        |
| Auth             | 8001   | http://localhost:8001        |
| Expense          | 8002   | http://localhost:8002        |
| Admin            | 8003   | http://localhost:8003        |
| File Service     | 8005   | http://localhost:8005        |
| Report Service   | 8009   | http://localhost:8009        |
| PostgreSQL       | 5433   | localhost:5433               |
| RabbitMQ Management | 15672 | http://localhost:15672    |
| MinIO Console    | 9001   | http://localhost:9001        |

---

## 11. Troubleshooting

### "Password authentication failed for user dou_user"

- Use the same credentials as in `infrastructure/docker-compose.yml`: `dou_user` / `dou_password123`
- Ensure `DATABASE_URL` uses `localhost:5433` (host port) when connecting from the host
- Inside Docker, services use `postgres:5432` (container network)

### "Relation tenants does not exist"

- The database has not been bootstrapped. Run `.\infrastructure\bootstrap-db.ps1` from the project root.
- Ensure Postgres is healthy: `docker ps` and check `dou-postgres`.

### "Connection refused" on Signup/Login (ERR_CONNECTION_REFUSED)

- Auth service is not running. Start backend services:  
  `docker compose -f infrastructure/docker-compose.yml up -d`
- Wait 30–60 seconds for services to start, then retry.
- Verify Auth API: http://localhost:8001/docs

### 500 Internal Server Error on API calls

- Check the response body (F12 → Network → failed request → Response) for `detail` and `hint`
- Common causes:
  - Wrong `DATABASE_URL` or `JWT_SECRET` in `backend/.env`
  - Missing `GEMINI_API_KEY` when using receipt extraction
  - Storage path permissions (`LOCAL_STORAGE_PATH`)

### Activity Log always empty / "Could not load activity"

- Run: `.\infrastructure\ensure-activity-table.ps1` from the project root
- This creates the activity table if missing and rebuilds the admin image.

### 403 when approving expenses

- Log in again so the app uses a fresh JWT
- Use `admin@example.com` or `approver@example.com` with password `password`

### Settings page fails to load or save

- Tables `tenant_settings` and `settings_changelog` may be missing
- Run bootstrap again or `create_tables.py` inside the auth container.

### Port already in use

- Change ports in `infrastructure/docker-compose.yml`, or
- Stop the process using the port (e.g., another Postgres instance on 5433)

### Docker build fails

- Ensure Docker has enough memory (recommend 4GB+)
- On Windows: WSL2 backend is recommended for better compatibility

---

## Summary Checklist

- [ ] Clone repo and `cd` to project root
- [ ] Create `backend/.env` from `.env.example`, set `JWT_SECRET` (and `GEMINI_API_KEY` if needed)
- [ ] Run `docker compose -f infrastructure/docker-compose.yml up -d`
- [ ] Run `.\infrastructure\bootstrap-db.ps1` (once per fresh DB)
- [ ] Run `cd frontend-web && npm install && npm run dev`
- [ ] Open http://localhost:3000 and log in with `admin@example.com` / `password`

---

For additional documentation, see:

- [Setup for teammates](./docs/SETUP_FOR_TEAMMATES.md)
- [Troubleshooting 500 errors](./docs/TROUBLESHOOTING_500.md)
- [Troubleshooting connection refused](./docs/TROUBLESHOOTING_CONNECTION_REFUSED.md)
