# Test Steps – In Sequence

Run these in order. Use PowerShell from the project root:
`d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas`

## Dependencies (install once)

- **Backend venv:** `pip install -r backend/requirements.txt` (includes `pandas`, `scikit-learn` for anomaly + monitoring script).
- **RAG (optional):** RAG service requires `sentence-transformers` (already in requirements; first run may download a model). If you see `ModuleNotFoundError: No module named 'sentence_transformers'`, run: `pip install sentence-transformers`.

---

## Step 1: Start the database (if not already running)

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
.\scripts\start-database.ps1
```

The script uses `docker compose -f infrastructure/docker-compose.db-only.yml` (port **5433**, password **dou_password123**). Wait until you see: `PostgreSQL is ready!`

---

## Step 2: Run DB/schema test (no backend needed)

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python backend/scripts/test_agentic_audit_db.py
```

Expected: `Schema + ingest OK` and lines showing expense columns, new tables, knowledge_documents count.

---

## Step 3: Restart backend (auth + audit) so dev user has audit permissions

Close any existing PowerShell windows that are running backend services (auth, expense, admin, audit, file). Then start the backend again:

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
.\scripts\start-backend-local.ps1
```

Wait until it says backend services started and 5 new windows have opened (Auth, Expense, Admin, Audit, File). Leave those windows open.

---

## Step 4: Run API tests (auth + audit)

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
.\scripts\test-agentic-audit-apis.ps1
```

Expected:  
- 1. Auth health (8001)... OK  
- 2. Audit health (8004)... OK  
- 3. Audit generate-basic (8004)... OK  
- 4. Anomaly run-monitoring (8010)... SKIP (until Step 6)  
- 5. RAG Co-Pilot (8018)... SKIP (until Step 7)

---

## Step 5 (Optional): Start anomaly service

Open a **new** PowerShell window:

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\backend"
.\venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
uvicorn services.anomaly_service.main:app --host 0.0.0.0 --port 8010
```

Leave this window open. If you get `ModuleNotFoundError: No module named 'pandas'`, run `pip install pandas scikit-learn` (or `pip install -r requirements.txt`), then run the `uvicorn` command again.

---

## Step 6 (Optional): Run API tests again (with anomaly)

In the **original** PowerShell (project root):

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
.\scripts\test-agentic-audit-apis.ps1
```

Expected: Step 4 (Anomaly run-monitoring) should now show OK (or a result with `processed=...`).

---

## Step 7 (Optional): Start RAG service

Install dependency once if needed: `pip install sentence-transformers` (first run may download a model; can take a few minutes).

Open another **new** PowerShell window:

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\backend"
.\venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
uvicorn services.rag_service.main:app --host 0.0.0.0 --port 8018
```

Leave this window open. Then run Step 8 to confirm RAG Co-Pilot shows OK.

---

## Step 8 (Optional): Run API tests again (with RAG)

In the project root PowerShell:

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
.\scripts\test-agentic-audit-apis.ps1
```

Expected: Step 5 (RAG Co-Pilot) should show OK (or an answer).

---

## Step 9 (Optional): Monitoring job with data – run script

In a **new** PowerShell (backend venv). Dependencies `pandas` and `scikit-learn` are in `requirements.txt`; if missing, run `pip install pandas scikit-learn` first.

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\backend"
.\venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python scripts/run_monitoring_job.py --limit 100 --days 90
```

Expected: `Done: processed=..., employees_updated=..., merchants_updated=...`  
(If there are no expenses, processed will be 0.)

---

## Step 10 (Optional): Create expenses via UI, then run monitoring again

1. Start the frontend (if not already running):

   ```powershell
   cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\frontend-web"
   npm run dev
   ```

2. In the browser: open `http://localhost:3000`, log in (or use dev flow), create a few expenses.
3. Run the monitoring job again (Step 9). You should see `processed > 0` and risk_scores populated.

---

## Step 11 (Optional): Audit Co-Pilot in the UI

1. Ensure **RAG** is running (Step 7) and **frontend** is running (Step 10).
2. In the browser go to: `http://localhost:3000/audit-copilot`
3. Type a question (e.g. “What expenses are high risk?”) and send.
4. You should get a real answer from the API (or an error if RAG/backend is down).

---

## Summary

| Scope | Steps | Expectation |
|-------|--------|-------------|
| **Required** | 1 → 2 → 3 → 4 | Database up (5433), schema + ingest OK, backend 5 services running, API tests: auth + audit OK; anomaly/RAG SKIP until started. |
| **Optional** | 5–6 | Anomaly on 8010; API test 4 shows OK (processed=…). |
| **Optional** | 7–8 | RAG on 8018 (requires sentence-transformers); API test 5 shows OK. |
| **Optional** | 9 | Monitoring script: `Done: processed=…` (0 if no expenses). |
| **Optional** | 10–11 | Frontend on 3000, create expenses, re-run Step 9; Audit Co-Pilot UI at `/audit-copilot`. |

---

## One-page quick reference

All commands from project root unless noted. Set `$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"` where needed.

| Step | Command / action | Expected result |
|------|-------------------|-----------------|
| 1 | `.\scripts\start-database.ps1` | `PostgreSQL is ready!` |
| 2 | `$env:DATABASE_URL="postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"; python backend/scripts/test_agentic_audit_db.py` | `Schema + ingest OK` |
| 3 | `$env:DATABASE_URL="..."; .\scripts\start-backend-local.ps1` | 5 backend windows open |
| 4 | `.\scripts\test-agentic-audit-apis.ps1` | 1–3 OK; 4–5 SKIP |
| 5 | New window: `cd backend; .\venv\Scripts\Activate.ps1; $env:DATABASE_URL="..."; uvicorn services.anomaly_service.main:app --host 0.0.0.0 --port 8010` | Leave open |
| 6 | `.\scripts\test-agentic-audit-apis.ps1` | Step 4 (Anomaly) OK |
| 7 | New window: `cd backend; .\venv\Scripts\Activate.ps1; $env:DATABASE_URL="..."; uvicorn services.rag_service.main:app --host 0.0.0.0 --port 8018` | Leave open (install `sentence-transformers` first if needed) |
| 8 | `.\scripts\test-agentic-audit-apis.ps1` | Step 5 (RAG Co-Pilot) OK |
| **RAG only** | `.\scripts\test-rag-pipeline.ps1` (after DB + backend + RAG 8018) | 1. Health OK 2. /qa (rag) OK 3. /copilot OK 4. /search OK |
| 9 | `cd backend; .\venv\Scripts\Activate.ps1; $env:DATABASE_URL="..."; python scripts/run_monitoring_job.py --limit 100 --days 90` | `Done: processed=..., employees_updated=..., merchants_updated=...` |
| 10 | `cd frontend-web; npm run dev` → browser `http://localhost:3000` → log in, create expenses → run Step 9 again | `processed > 0` after creating expenses |
| 11 | Browser: `http://localhost:3000/audit-copilot` (RAG + frontend running), send a question | Real API answer in UI |

---

## Restart after code changes (permission / audit fix)

After updating auth or RAG code (e.g. `get_user_permissions`, audit access), restart services so they load the new code:

1. **Restart RAG (8018) and Anomaly (8010):**
   ```powershell
   cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
   .\scripts\restart-optional-services.ps1
   ```
   This stops processes on 8018 and 8010, then starts RAG and Anomaly in new windows. Wait ~30s for RAG to be ready (embedding model loads on first request). After RAG code changes (e.g. policy/VAT document-type filter, similarity threshold), always restart RAG so the new logic is used.

2. **Restart Auth (8001), Audit (8004), and other backend services:**  
   Close the 5 backend PowerShell windows (Auth, Expense, Admin, Audit, File), then run:
   ```powershell
   $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
   .\scripts\start-backend-local.ps1
   ```

3. **Optional:** Have users **log out and log in again** so a new token/session is used.

4. **Verify:** Run API tests and test the Audit Q&A page:
   ```powershell
   .\scripts\test-agentic-audit-apis.ps1
   ```
   Then open **http://localhost:3000/audit/qa**, log in (Admin or user with `audit:read`), ask a question. You should **not** see "Audit access required".

---

## Test RAG pipeline (RAG queries only)

To run the project and test **only** the RAG pipeline (health, `/qa` with `query_type=rag`, `/copilot`, `/search`):

1. **Start database and backend** (Steps 1–3):  
   `.\scripts\start-database.ps1` → then `$env:DATABASE_URL="..."; .\scripts\start-backend-local.ps1`

2. **Start RAG service** (one window):  
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
   uvicorn services.rag_service.main:app --host 0.0.0.0 --port 8018
   ```  
   Wait until the server logs show it is ready (first run may take 1–2 minutes to load the model).

3. **Run RAG pipeline tests:**  
   ```powershell
   cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"
   .\scripts\test-rag-pipeline.ps1
   ```  
   **Expected:**  
   - 1. RAG health (8018)... OK  
   - 2. RAG /qa (query_type=rag)... OK  
   - 3. RAG /copilot (agentic)... OK  
   - 4. RAG /search (semantic)... OK (or OK with no results if index is empty)

   This script uses the dev token and calls: `GET /health`, `POST /api/v1/rag/qa` (RAG path), `POST /api/v1/rag/copilot`, `POST /api/v1/rag/search`.
