# RAG and document_embeddings

## Why is document_embeddings empty when receipt_documents has rows?

- **Receipts** are embedded into `document_embeddings` in **two** ways:
  1. **On new upload:** When a receipt is uploaded, the receipt pipeline runs (OCR → extraction) and then calls the RAG pipeline to embed that **one** receipt. So only receipts processed **after** that code was added get embedded automatically.
  2. **Backfill:** Existing rows in `receipt_documents` (e.g. your 32 rows) were created **before** the embed step existed or were never passed through the pipeline, so they were **never** embedded.

- **Policies** and **VAT rules** are embedded only when you click **Index policies** / **Index VAT rules** on the Audit Q&A page. They are read from `expense_policies` and `vat_rules`; if those tables are empty, 0 documents are embedded.

So: **document_embeddings** stays empty until you either run the backfill (Index receipts) or add and index policies/VAT rules.

---

## What to do: fill document_embeddings

**Option A – One-shot backfill script (recommended if the table stays empty)**  
From the **backend** folder with **venv activated**:

```powershell
.\venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python scripts/backfill_document_embeddings.py
```

This script embeds all policies, VAT rules, and receipts for the first tenant into `document_embeddings`. It needs `sentence-transformers` and `asyncpg` installed (`pip install -r requirements.txt` if needed).

**Option B – Use the Audit Q&A page**  
1. **Receipts (backfill):** Go to **http://localhost:3000/audit/qa** → **RAG Only** or **Hybrid** → click **Index receipts**.  
2. **Policies:** Add rows to **expense_policies** (see below), then click **Index policies**.  
3. **VAT rules:** Add rows to **vat_rules** (see below), then click **Index VAT rules**.

---

## How to add data to expense_policies

**Option A – Seed script (recommended)**  
From the **backend** folder:

```bash
# Windows PowerShell
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python scripts/seed_french_policies.py
```

This inserts French expense policies (meal caps, hotel, mileage, etc.) for the first tenant.

**Option B – Admin API**  
If you have an Admin UI or API client:

- **POST** `/api/v1/admin/policies` with body like:
  - `name`, `description`, `policy_type` (e.g. `meal_cap`, `amount_limit`), `policy_rules` (JSON).

**Option C – SQL**  
Insert directly into `expense_policies` (columns: `id`, `tenant_id`, `name`, `description`, `policy_type`, `policy_rules`, `is_active`, `created_at`, `updated_at`, etc.). Use an existing `tenant_id` from `tenants`.

---

## How to add data to vat_rules

**Option A – Seed script**  
From the **backend** folder:

```bash
$env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
python scripts/seed_vat_rules.py
```

This inserts a few French VAT rules (Restaurant 10%, Default 20%, etc.) for the first tenant.

**Option B – Admin API**  
- **POST** `/api/v1/admin/vat-rules` with body:
  - `category` (e.g. `"Restaurant"`), `vat_rate` (e.g. `10.0`), `vat_code` (e.g. `"FR-TVA-10"`), optional `is_default`, `effective_from`, `effective_to`.

**Option C – SQL**  
Insert into `vat_rules` (columns: `id`, `tenant_id`, `category`, `merchant_pattern`, `vat_rate`, `vat_code`, `is_default`, `effective_from`, `effective_to`, `created_at`, `updated_at`).

---

## Summary

| Table                 | How to add rows                          | How to get into RAG (document_embeddings)     |
|-----------------------|------------------------------------------|-----------------------------------------------|
| **expense_policies**  | Seed: `python scripts/seed_french_policies.py` or Admin API / SQL | Audit Q&A → **Index policies**                |
| **vat_rules**         | Seed: `python scripts/seed_vat_rules.py` or Admin API / SQL       | Audit Q&A → **Index VAT rules**               |
| **receipt_documents** | Already have 32 rows (uploads)           | Audit Q&A → **Index receipts** (backfill)     |

After indexing, ask questions on the same page with **RAG Only** (e.g. “What is the expense policy?”, “What do my receipts show?”).
