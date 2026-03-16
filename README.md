# Dou Compta — Server

Backend and infrastructure for **Dou Expense & Audit AI**: auth, expense API, file service (upload, storage, receipt OCR + extraction pipeline), and optional services (email ingestion, AI pipeline).

**Related:** The web frontend is in the **dou-compta-main-client** repository (Next.js; runs at `http://localhost:3000`).

## Repo layout

| Path | Description |
|------|-------------|
| `french-ai-accounting-saas-backend-tmp` | Python backend (FastAPI): auth, expense, **file-service**, OCR, LLM pipeline |
| `french-accounting-ai-saas-infra-tmp` | Docker Compose for local dev: Postgres, auth, **file-service**, expense, etc. |

The **file-service** (receipt upload + extract) is built from `french-ai-accounting-saas-backend-tmp` and runs in Docker via the infra compose.

## Quick start (Docker)

From the infra directory:

```bash
cd french-accounting-ai-saas-infra-tmp
cp .env.example .env
# Edit .env: set GEMINI_API_KEY (and optionally OCR_PROVIDER, GEMINI_MODEL)
docker compose up -d postgres file-service
```

- **Postgres**: `localhost:5433` (user `dou_user`, DB `dou_expense_audit`).
- **File service**: `http://localhost:8005` (upload + receipt extract). Health: `http://localhost:8005/health`.

To rebuild file-service after code changes:

```bash
docker compose build file-service
docker compose up -d file-service
```

## File service & receipt extraction

- **Upload**: Store receipt file; optional background pipeline runs OCR → normalize → LLM extract and updates receipt metadata.
- **Extract** (instant): `POST /api/v1/receipts/extract` with the file; runs OCR (Paddle with Tesseract fallback), document classification, and LLM extraction. Returns supplier, invoice number, date, VAT, total, currency. PDFs are converted to an image before OCR so Tesseract fallback works.

### Environment (file-service)

In `french-accounting-ai-saas-infra-tmp/.env` (or compose env):

| Variable | Description | Default |
|----------|-------------|---------|
| `OCR_PROVIDER` | `paddle` or `tesseract` | `paddle` |
| `GEMINI_API_KEY` | Gemini API key for LLM extraction | — |
| `GEMINI_MODEL` | Model name | `models/gemini-2.0-flash` |
| `DATABASE_URL` | Postgres URL (set by compose) | — |

### Logs

```bash
docker compose logs -f file-service
```

Useful to confirm OCR provider, PDF→image, and extraction errors.

## Backend (run locally)

If you run services outside Docker:

```bash
cd french-ai-accounting-saas-backend-tmp
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements-slim.txt   # or requirements.txt
# Set DATABASE_URL, JWT_SECRET, etc. (see .env.example in infra)
uvicorn services.file_service.main:app --reload --port 8005
```

## Other services (compose)

Infra compose can start auth (8001), expense (8002), and other microservices; see `french-accounting-ai-saas-infra-tmp/docker-compose.yml`. The frontend expects **expense** at `8002` and **file-service** at `8005`.

## Tech stack (backend)

- **Python 3.11**, FastAPI, Uvicorn
- **PostgreSQL** (SQLAlchemy, asyncpg/psycopg2)
- **OCR**: Paddle OCR (primary), Tesseract (fallback); PDFs converted to image before OCR
- **LLM**: Gemini for document classification and field extraction

## Troubleshooting

- **Upload or extract fails** — Ensure file-service is up: `curl http://localhost:8005/health`. Check `NEXT_PUBLIC_FILE_API_URL` in the client `.env.local` and restart the Next.js dev server.
- **No data / empty extraction** — Run `docker compose logs -f file-service` during an upload; confirm OCR returns text and that `GEMINI_API_KEY` is set in infra `.env`.
- **Rebuild after code changes** — From infra: `docker compose build file-service && docker compose up -d file-service`.
