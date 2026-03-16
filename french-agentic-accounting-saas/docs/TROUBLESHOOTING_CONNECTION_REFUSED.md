# Fix: ERR_CONNECTION_REFUSED on Signup/Login

## What the error means

- **`POST http://localhost:8001/api/v1/auth/signup net::ERR_CONNECTION_REFUSED`**
- The frontend is calling the **Auth API** at `http://localhost:8001`, but nothing is listening on that port.
- So the **Auth backend service is not running**.

## Fix: Start the backend

You need the **database** and the **Auth service** (and optionally other services) running.

### Option A: Using Docker (recommended)

From the project root:

```powershell
cd infrastructure
docker-compose up -d postgres
docker-compose -f docker-compose.yml -f docker-compose.backend.yml up -d auth
```

- First time: building the `auth` image can take several minutes.
- If the `auth` image is not built yet, use:

  ```powershell
  docker-compose -f docker-compose.yml -f docker-compose.backend.yml up -d --build auth
  ```

Check that the auth container is running:

```powershell
docker ps
```

You should see `dou-postgres` and `dou-auth`. Auth is exposed on **port 8001**.

### Option B: Running Auth locally (Python)

1. **Start the database** (if not already running):

   ```powershell
   cd infrastructure
   docker-compose up -d postgres
   ```

2. **Use Python 3.11 or 3.12** (3.13 can cause install issues). Create/use a venv and install deps:

   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Run the Auth service**:

   ```powershell
   $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
   python -m uvicorn services.auth.main:app --reload --port 8001
   ```

4. Keep this terminal open. When you see something like “Application startup complete”, try signup again in the browser.

## Verify

- Open: **http://localhost:8001/docs**  
  You should see the Auth API Swagger UI.
- Then retry **signup** (or login) in the frontend; the connection refused error should go away.

## Frontend API URL

The frontend uses:

- `NEXT_PUBLIC_API_URL` if set (e.g. in `.env.local`), or  
- `http://localhost:8001` by default for auth.

So the Auth service must be reachable at **localhost:8001** (or whatever host/port you set in `NEXT_PUBLIC_API_URL`).
