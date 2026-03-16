# Setup for New Clones (Teammates)

After cloning the repo from GitHub, follow these steps to run the app locally.

## Prerequisites

- **Docker & Docker Compose** (for Postgres and backend services)
- **Node.js 18+** (for the frontend)
- **PowerShell** (on Windows; for bootstrap script). On macOS/Linux you can run the equivalent commands manually.

---

## 1. Backend environment (required)

The repo does **not** commit `.env` (it’s in `.gitignore`). Create it from the example:

```powershell
cd backend
copy .env.example .env
```

Then edit `backend/.env`:

- **DATABASE_URL** – Only needed if you run backend scripts from the host. For Docker, the compose file sets it. Default: `postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit`
- **JWT_SECRET** – Must be the same across services. Use any long random string (e.g. `9f3b6c7e8a1d2f4c6b8e0a3d5f7c9e1b2d4a6c8e0f3b5d7a9c1e2f4a6b8c0d2`) or match what’s in `infrastructure/docker-compose.yml`.
- **GEMINI_API_KEY** – Required if you use receipt extraction/LLM. Get one from Google AI Studio; or leave as placeholder if you don’t need that feature.

Other vars (e.g. `STORAGE_PROVIDER=local`, `ENCRYPTION_ENABLED=false`) are fine as in the example for local dev.

---

## 2. Start Postgres and backend services

From the **project root** (not inside `backend` or `infrastructure`):

```powershell
docker compose -f infrastructure/docker-compose.yml up -d
```

Wait until Postgres is healthy (about 30–60 seconds). Optionally check:

```powershell
docker compose -f infrastructure/docker-compose.yml ps
```

---

## 3. Bootstrap the database (required once per fresh DB)

After the first `up`, or after `docker compose down -v`, the database is empty. Run the bootstrap script **from the project root**:

```powershell
.\infrastructure\bootstrap-db.ps1
```

This will:

1. Create all tables
2. Seed tenant, permissions, roles, and default users
3. Seed PRD roles (admin, employee, approver, finance)

If this fails (e.g. “relation tenants does not exist”), ensure step 2 finished and Postgres is healthy, then run the script again.

---

## 4. Frontend

```powershell
cd frontend-web
npm install
npm run dev
```

Frontend will be at **http://localhost:3000**.

Optional: copy `frontend-web/.env.example` to `frontend-web/.env.local` if you need to override API URLs (defaults point to localhost:8001, 8002, etc.).

---

## 5. Log in (seed users)

Bootstrap creates these users; password for all is **`password`**:

| Email                 | Role     |
|-----------------------|----------|
| admin@example.com     | Admin    |
| approver@example.com  | Approver |
| finance@example.com   | Finance  |
| user@example.com      | Employee |

These are defined in `backend/scripts/seed_data.py`, not in `.env`. No extra setup is required to use them.

---

## 6. Optional: SSO (Google / Microsoft / Okta)

You can enable SSO via Google Workspace, Microsoft Entra ID (Azure AD), and Okta. This is **optional** for local dev; if you skip it, email/password login continues to work.

### 6.1 Auth service env (Python auth service in Docker)

The SSO flow is handled by the **Python auth service** that runs in Docker from `infrastructure/docker-compose.yml` (service `auth` on port 8001).

Secrets like Google client secrets should **never** live in source-controlled files. Instead:

1. From the project root:

   ```powershell
   cd infrastructure
   copy .env.auth-local.example .env.auth-local
   ```

2. Edit `infrastructure/.env.auth-local` and fill in your own values:

   ```bash
   FRONTEND_APP_URL=http://localhost:3000

   # Google
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:8001/api/v1/auth/oauth/google/callback
   ```

   This file is **gitignored** and only used on your machine.

3. The `auth` service in `infrastructure/docker-compose.yml` already imports this file via `env_file: .env.auth-local` and exposes the variables to the Python auth service.

After changing `.env.auth-local`, run:

```powershell
.\scripts\start-with-docker-auth.ps1
```

to rebuild/restart the auth container so it picks up the new env.

### 6.2 Frontend env (`frontend-web/.env.local`)

The frontend already uses `NEXT_PUBLIC_API_URL` to talk to the auth service. For local dev:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

With this set, the **“Continue with Microsoft / Google / Okta”** buttons on `/login` will redirect through the auth service, complete the OAuth flow, and then the backend will:

- Create or reuse a local user for the email from the IdP
- Issue the same JWT / refresh token as password login
- Set `token` and `refresh_token` cookies for `localhost`
- Redirect back to the frontend (default `FRONTEND_APP_URL`), where the app picks up the session automatically.

---

## Summary checklist

- [ ] Clone repo, open in terminal at **project root**
- [ ] `backend`: copy `.env.example` → `.env`, set `JWT_SECRET` (and optionally `GEMINI_API_KEY`)
- [ ] `docker compose -f infrastructure/docker-compose.yml up -d`
- [ ] `.\infrastructure\bootstrap-db.ps1` (once per fresh DB)
- [ ] `cd frontend-web && npm install && npm run dev`
- [ ] Open http://localhost:3000 and log in with e.g. **admin@example.com** / **password**

---

## Troubleshooting

- **“Password authentication failed for user dou_user”** – You’re connecting to Postgres from the host with wrong credentials. Use the same URL as in `infrastructure/docker-compose.yml` (e.g. `dou_password123`) or run bootstrap/scripts via Docker (as in `bootstrap-db.ps1`).
- **“Relation tenants does not exist”** – DB not bootstrapped. Run `.\infrastructure\bootstrap-db.ps1`.
- **Activity log always empty** or **"Could not load activity"** – Run from project root:  
  `.\infrastructure\ensure-activity-table.ps1`  
  This creates the activity table if missing, **rebuilds the admin image** (so the container has the `/activity` API), and starts admin. Then refresh the Activity Log tab.
- **403 when approving expenses** – Log in again after the frontend fix so the app uses the real JWT; use **admin@example.com** or **approver@example.com** with password **password**.
- **Settings page fails to load or save** – The Settings page uses `tenant_settings` and `settings_changelog` tables. If they are missing, run bootstrap again or `create_tables.py` (which now ensures these tables exist).
- **Port already in use** – Change ports in `infrastructure/docker-compose.yml` or stop the process using the port.

For RBAC testing see [RBAC_TESTING.md](./RBAC_TESTING.md).
