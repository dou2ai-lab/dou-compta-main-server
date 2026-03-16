# Database access

## Connection details (PostgreSQL)

Use these when connecting from a desktop client (DBeaver, pgAdmin, etc.) or from the browser (Adminer).

| Setting   | Value                |
|----------|----------------------|
| **Host** | `localhost`          |
| **Port** | `5433`               |
| **User** | `dou_user`           |
| **Password** | `dou_password123` |
| **Database** | `dou_expense_audit` |

**Connection URL (for apps that accept a URL):**
```
postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit
```

---

## Access from the browser (Adminer)

When the database is started with the project’s db-only compose, an **Adminer** container is available so you can use the DB from your browser.

### 1. Start the database (and Adminer)

From the project root:

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
.\scripts\start-database.ps1
```

This starts Postgres and Adminer (if using `docker-compose.db-only.yml`).

### 2. Open Adminer in the browser

- **URL:** **http://localhost:8080**
- **System:** `PostgreSQL`
- **Server:** `postgres` (leave as is when using Docker)
- **Username:** `dou_user`
- **Password:** `dou_password123`
- **Database:** `dou_expense_audit`

Click **Login**. You can then run SQL, browse tables, and export data.

### 3. If Adminer does not start or "This site can't be reached"

- **Start Adminer** (if only Postgres was running):
  ```powershell
  cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\infrastructure"
  docker compose -f docker-compose.db-only.yml up -d
  ```
- **If you see "container name already in use"**, remove the old Adminer container and start again:
  ```powershell
  docker rm -f dou-adminer
  cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\infrastructure"
  docker compose -f docker-compose.db-only.yml up -d adminer
  ```
- Then open **http://localhost:8080** (not 8080/ with a trailing slash) and use the credentials above.

---

## Summary

| Access method | URL / target | Login |
|---------------|--------------|--------|
| **Browser (Adminer)** | http://localhost:8080 | Server: `postgres`, User: `dou_user`, Password: `dou_password123`, Database: `dou_expense_audit` |
| **Direct (e.g. DBeaver)** | Host: `localhost`, Port: `5433` | User: `dou_user`, Password: `dou_password123`, Database: `dou_expense_audit` |
