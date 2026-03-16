# Receipt Extraction Pipeline

## Overview

Upload → **Tesseract OCR** (raw text) → **Gemini** (structured JSON) → Backend returns full extraction → Frontend auto-fills entire Expense Details form.

- **No regex parsing** – LLM-only structured extraction.
- **Strict schema** – All fields (merchant, address, date, time, invoice number, line items, subtotal, VAT, total, currency, payment method, description, category).

## Required environment variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL URL (e.g. `postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit`) |
| `JWT_SECRET` | Yes | Same as auth; used for file service auth |
| `OCR_PROVIDER` | Yes | `tesseract` (or `google_document_ai` / `azure_form_recognizer`) |
| `GEMINI_API_KEY` | Yes | Google AI Studio API key for Gemini |
| `GEMINI_MODEL` | No | Default `models/gemini-2.0-flash` |
| `STORAGE_PROVIDER` | No | `local` for dev |
| `LOCAL_STORAGE_PATH` | No | Local folder for receipt files |

### Frontend

- `NEXT_PUBLIC_FILE_API_URL` (default `http://localhost:8005`) for file service.

## Commands to run

### 1. Database

```powershell
cd "e:\French Accounting SAAS\french-agentic-accounting-saas\infrastructure"
docker-compose up -d postgres
```

### 2. Backend (from project root)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"

# Run each in a separate terminal (or use start-backend-local.ps1)
uvicorn services.auth.main:app --reload --port 8001
uvicorn services.expense.main:app --reload --port 8002
uvicorn services.admin.main:app --reload --port 8003
uvicorn services.audit.main:app --reload --port 8004
uvicorn services.file_service.main:app --reload --port 8005
```

### 3. Frontend

```powershell
cd frontend-web
npm run dev
```

- App: **http://localhost:3000**
- New expense (upload): **http://localhost:3000/expenses/new**

## API

- **POST /api/v1/receipts/upload** – Upload receipt; runs OCR + Gemini pipeline in background. Returns `receipt_id`. Frontend polls **GET /api/v1/receipts/{id}/status** then **GET /api/v1/receipts/{id}** to get `meta_data.extraction` and auto-fill form.
- **POST /api/v1/receipts/extract** – Run OCR + Gemini only (no save). Returns `{ success: true, data: ReceiptData }` or `{ success: false, error: "..." }`. Use for instant extraction without storing.

## Flow verification

1. Open http://localhost:3000/expenses/new
2. Upload a receipt image (e.g. sample: BISTROT DU COIN, 14/01/2026, menu/café/dessert, Subtotal 26.00, VAT 2.60, Total 28.60, card)
3. Wait for “Data Extracted Successfully”
4. Form should show: Merchant, Date, Total, VAT, Subtotal, Payment, Description, Category, Line items (no manual entry needed)

## What was implemented

- **Strict schema**: `ReceiptDataStrict` (backend) and `ReceiptData` / `ReceiptExtractionFromAPI` (frontend types).
- **Gemini prompt**: “You are a receipt data extraction engine” + schema + `response_mime_type = application/json`.
- **Pipeline**: OCR (Tesseract) → raw text → Gemini → parse JSON → save to `meta_data.extraction`; regex enrichment removed.
- **POST /api/v1/receipts/extract**: OCR + Gemini only, returns `{ success, data }`.
- **Frontend**: `receiptDataToFormState()` maps all extraction fields to form; `setFormData(receiptDataToFormState(data))` after getReceipt.
