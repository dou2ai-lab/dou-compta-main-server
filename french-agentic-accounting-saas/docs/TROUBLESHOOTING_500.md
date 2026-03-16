# Troubleshooting 500 Internal Server Error

When you see **"Failed to load resource: the server responded with a status of 500"**:

## 1. See the actual error

- **Browser**: Open DevTools (F12) → **Network** tab → click the failed request (red, status 500) → **Response** (or **Preview**). The body is JSON with:
  - `detail`: error message
  - `error_type`: exception type
  - `path`: API path that failed
  - `hint`: suggested fix

- **Backend terminal**: The file service prints the full traceback when a 500 occurs:
  ```
  ================================================================================
  GLOBAL EXCEPTION HANDLER TRIGGERED
  Path: ...
  Error Type: ...
  Error Message: ...
  Full Traceback:
  ...
  ================================================================================
  ```

## 2. Common causes and fixes

| Symptom / message | Fix |
|-------------------|-----|
| Connection refused / could not connect | Start PostgreSQL: `cd infrastructure && docker-compose up -d postgres`. Ensure `DATABASE_URL` in `backend/.env` uses `localhost:5433`. |
| Password authentication failed | In `backend/.env`, set `DATABASE_URL=postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit` (password `dou_password123`, port `5433`). |
| Tesseract / pytesseract | Install Tesseract on the machine or ignore OCR errors (extract endpoint may still return 500 if OCR is required). For dev, you can use a mock. |
| Gemini / API key / 429 | Set valid `GEMINI_API_KEY` in `backend/.env`. If you hit quota, wait or use another key. |
| Storage / path / permission | Set `LOCAL_STORAGE_PATH` to a writable folder, e.g. `./uploads/receipts`. On Windows avoid `/tmp/...`. |
| User not authenticated / 401 | Upload uses `Authorization: Bearer dev_mock_token_local`. File service must accept this (auth dependency). If you get 401, the 500 might be from a different request (e.g. getReceipt). |

## 3. Which request is 500?

In Network tab, check the **Request URL**:

- `/api/receipts/upload` → Next.js proxy to file service **POST /api/v1/receipts/upload**. Backend may fail on auth, storage, or DB.
- `http://localhost:8005/api/v1/receipts/...` → Direct file service (getReceipt, getReceiptStatus). Often auth (DB) or missing receipt.

## 4. Quick checks

```powershell
# PostgreSQL running?
docker ps
# Should show dou-postgres on 5433

# File service health
Invoke-WebRequest -Uri http://localhost:8005/health -UseBasicParsing | Select-Object Content

# Env (no secrets)
# In backend folder, ensure .env has DATABASE_URL, JWT_SECRET, GEMINI_API_KEY, OCR_PROVIDER
```

After fixing, restart the backend (file service) and retry.
