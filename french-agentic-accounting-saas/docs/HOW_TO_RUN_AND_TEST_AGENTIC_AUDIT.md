# How to Run & Test the Agentic Audit & Compliance Module

## Prerequisites

- **PostgreSQL** running (e.g. via Docker: `.\scripts\start-database.ps1` or `docker compose -f infrastructure/docker-compose.db-only.yml up -d`).
- **Backend** (auth, expense, audit, anomaly, RAG, etc.) and **frontend** running as needed for each test.

---

## Step 1: Apply database migrations

Run once (or after pulling new migrations):

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas"

$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python backend/scripts/run_all_migrations.py
```

**Expected:** `[APPLY] Applying 016_agentic_audit_compliance.sql` (or `skipped` if already applied), then `Migrations complete. applied=... skipped=... errors=0`.

---

## Step 2: Run the monitoring job (risk scores + anomaly persistence)

Two options.

### Option A: Via HTTP (anomaly service must be running)

1. Start backend services (e.g. `.\scripts\start-backend-local.ps1`).
2. Get a JWT (e.g. log in via frontend or `POST /api/v1/auth/login`).
3. Call the endpoint:

```powershell
# Replace YOUR_JWT with the token from login
$token = "YOUR_JWT"
Invoke-RestMethod -Uri "http://localhost:8010/api/v1/anomaly/jobs/run-monitoring?limit=500&lookback_days=90" `
  -Method POST -Headers @{ Authorization = "Bearer $token" }
```

(If your anomaly service runs on a different port, change `8010`.)

### Option B: Via script (requires backend venv with pandas + scikit-learn)

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\backend"
.\venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python scripts/run_monitoring_job.py --limit 500 --days 90
```

If `pandas` or `scikit-learn` are missing, install them: `pip install pandas scikit-learn`, then run again.

**Expected:** `Done: processed=..., employees_updated=..., merchants_updated=...`.

---

## Step 3: Ingest knowledge for RAG

Run once (or periodically to refresh content):

```powershell
cd "d:\Data Scientist\WorkLearn\Euron Project\9thFeb2026DUO\french-agentic-accounting-saas\backend"
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python scripts/ingest_knowledge.py
```

**Expected:** Lines like `Fetching https://...`, `Stored knowledge_documents id=...`, then `Done. Next: run RAG embed...`.

---

## Step 4: Use the Audit Co-Pilot

1. Start **RAG service** (e.g. on port 8018) and **frontend** (e.g. `cd frontend-web; npm run dev`).
2. Ensure `NEXT_PUBLIC_RAG_API_URL` points to the RAG service (e.g. `http://localhost:8018`).
3. Log in to the app, open **Audit Co-Pilot** (or `/audit-copilot`).
4. Type a question and send; the UI calls the real Co-Pilot API and shows the answer (and citations if returned).

---

## How to test the new changes

### 1. Migrations & schema

- **Check new columns on expenses:**
  ```sql
  SELECT column_name FROM information_schema.columns
  WHERE table_name = 'expenses' AND column_name IN ('risk_score_line','is_anomaly','anomaly_reasons');
  ```
  You should see `risk_score_line`, `is_anomaly`, `anomaly_reasons`.

- **Check new tables:**
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_name IN ('risk_scores','knowledge_documents','audit_report_narratives');
  ```
  All three should exist.

### 2. Continuous monitoring & anomaly persistence

- **After running the monitoring job (Step 2):**
  - Query expenses with risk data:
    ```sql
    SELECT id, amount, risk_score_line, is_anomaly, anomaly_reasons
    FROM expenses WHERE deleted_at IS NULL AND risk_score_line IS NOT NULL LIMIT 5;
    ```
  - Query risk_scores:
    ```sql
    SELECT entity_type, entity_id, risk_score, updated_at FROM risk_scores LIMIT 10;
    ```
- **Via API:** Call `POST /api/v1/anomaly/jobs/run-monitoring` with a valid JWT; response should include `processed`, `employees_updated`, `merchants_updated`.

### 3. Anomaly rules & reasons

- **Single expense analysis:** `POST /api/v1/anomaly/analyze/{expense_id}` with JWT.
  - Response should include `anomaly_reasons` (e.g. `["MISSING_VAT","WEEKEND"]`) and `risk_score`.
- In DB, that expense’s `risk_score_line`, `is_anomaly`, and `anomaly_reasons` should be updated.

### 4. Audit report generation (executive summary & top risks)

- **Generate a basic report:** `POST /api/v1/audit/reports/generate-basic` with body:
  `{ "period_start": "2025-01-01", "period_end": "2025-12-31" }`.
- Response should include `executive_summary`, `top_risk_employees`, `top_risk_merchants` (may be empty if no risk data yet).

### 5. Evidence pack & SYSTEM_AUTO_RULE_ENGINE

- Create an audit report and collect evidence for expenses that are **approved but have no approval workflow** (auto-approved).
- List or download evidence for that report; you should see an approval_chain evidence item with description/approver **"SYSTEM_AUTO_RULE_ENGINE"** instead of a user name.
- **Evidence pack download:** `GET /api/v1/audit/reports/{report_id}/evidence/download`; response headers should include `X-Evidence-Pack-Hash` (SHA-256).

### 6. Knowledge documents & RAG

- **After Step 3 (ingest):**
  ```sql
  SELECT id, title, type, language, LEFT(content, 80) FROM knowledge_documents WHERE deleted_at IS NULL;
  ```
  You should see rows for URSSAF, GDPR, VAT, Appvizer.
- Use RAG embed endpoints (or your existing pipeline) to chunk and embed from `knowledge_documents` into `document_embeddings` so Co-Pilot can retrieve them.

### 7. Audit Co-Pilot (frontend + API)

- **API:** `POST /api/v1/rag/copilot` with body `{ "query": "Show me all expenses over 500 in Q1 with missing VAT" }` and auth header.
  - Expect `answer` and optionally `citations`, `reasoning_steps`.
- **Frontend:** Open Audit Co-Pilot, send the same (or any) question; the reply should come from the API (no mock). If the RAG service is down, you should see an error message in the chat.

### 8. Risk dashboards

- **Anomaly dashboard:** `GET /api/v1/anomaly/dashboard` (with JWT). Response should include `high_risk_employees`, `high_risk_merchants`, `suspicious_transactions` (after the monitoring job has run and there is expense data).

---

## Quick checklist

| Step | Command / action | Verify |
|------|-------------------|--------|
| 1. Migrations | `python backend/scripts/run_all_migrations.py` | 016 applied or skipped, no errors |
| 2. Monitoring job | HTTP: `POST .../anomaly/jobs/run-monitoring` or script `run_monitoring_job.py` | `expenses.risk_score_line` / `risk_scores` populated |
| 3. Knowledge ingest | `python backend/scripts/ingest_knowledge.py` | Rows in `knowledge_documents` |
| 4. Co-Pilot | Open `/audit-copilot`, send a message | Real API answer (or clear error if service down) |
| 5. Report | `POST .../audit/reports/generate-basic` | `executive_summary`, `top_risk_*` in response |
| 6. Evidence | Create report, collect evidence, download ZIP | `SYSTEM_AUTO_RULE_ENGINE` for auto-approved; `X-Evidence-Pack-Hash` header |

---

## Automated test scripts

- **DB/schema + knowledge:**  
  `python backend/scripts/test_agentic_audit_db.py`  
  Checks: expense risk columns, new tables, knowledge_documents count.

- **APIs (backend must be running):**  
  `.\scripts\test-agentic-audit-apis.ps1`  
  Uses token `dev_mock_token_local`. Checks: auth health, audit health, audit generate-basic, anomaly run-monitoring (optional), RAG copilot (optional).

**Note:** For `dev_mock_token_local` to have audit access, the dev user (dev@dou.fr) is given audit permissions in code. Restart audit (and auth if you changed auth) after pulling that change, then re-run the API script.

## Troubleshooting

- **DB connection:** Ensure PostgreSQL is listening on the port in `DATABASE_URL` (e.g. 5433 for Docker).
- **Monitoring job fails (script):** Install backend deps: `pip install pandas scikit-learn` in the venv; then re-run the script.
- **Co-Pilot returns “DB unreachable” or connection error:** Run RAG (and backend) in the same network as the DB (e.g. Docker), or fix `DATABASE_URL` for the RAG service.
- **No risk data:** Run Step 2 (monitoring job) and ensure there are expenses in the date range; then re-check `expenses` and `risk_scores`.
