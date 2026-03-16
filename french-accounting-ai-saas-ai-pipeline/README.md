# French Accounting AI SaaS – AI Pipeline

Standalone AI pipeline for **OCR**, **document classification**, and **invoice/receipt field extraction**. Used by the French Accounting SaaS backend to process uploaded receipts and invoices. Can run as a **CLI**, **HTTP API**, or **Python library**.

---

## Table of contents

- [Features](#features)
- [Supported inputs: images and PDF](#supported-inputs-images-and-pdf)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project structure](#project-structure)
- [OCR providers](#ocr-providers)
- [LLM and extraction](#llm-and-extraction)
- [Integration with the backend](#integration-with-the-backend)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Features

- **OCR** on invoices and receipts (Tesseract or PaddleOCR).
- **PDF support** when using PaddleOCR (PDF → images via `pdf2image` with Poppler, with automatic PyMuPDF fallback when configured); Tesseract is image-only.
- **Document classification**: invoice, receipt, bank_statement, payslip, or other (keyword-based, no LLM required).
- **Structured extraction**: supplier, invoice number, date, VAT, total, currency (LLM or rule-based fallback).
- **Lightweight default**: Tesseract + rule-based extraction so you can run without GPU or LLM APIs.
- **Optional LLM**: Gemini, OpenAI, or Anthropic for higher-quality extraction when configured.
- **HTTP API**: `POST /extract` for backend integration; **CLI** and **Python API** for scripts and local runs.

---

## Supported inputs: images and PDF

| OCR provider   | Images (PNG, JPEG, etc.) | PDF |
|----------------|---------------------------|-----|
| **Tesseract**  | Yes                       | No  |
| **PaddleOCR**  | Yes                       | Yes (converts to images internally) |

- **Tesseract**: Accepts only image files. Uploading a PDF will fail at OCR unless you convert it to images elsewhere.
- **PaddleOCR**: Accepts both images and PDFs; PDFs are converted to images (first few pages) using `pdf2image` (requires Poppler on the system) and will fall back to PyMuPDF when `pymupdf` is installed but Poppler/`pdf2image` is unavailable.

---

## Prerequisites

### Windows

- **Python 3.12** (or 3.11+).
- **Tesseract OCR**
  - Install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) (e.g. to `C:\Program Files\Tesseract-OCR`).
  - Add the Tesseract folder to your **user PATH** so `tesseract --version` works in a new terminal.
- **(Optional) PaddleOCR + PDF**: Either install [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) and set `POPPLER_PATH` to its `bin` folder, or install PyMuPDF for PDF support without external tools: `pip install pymupdf`.

### Linux / macOS

- **Tesseract**: `sudo apt install tesseract-ocr tesseract-ocr-fra` (or equivalent).
- **Poppler** (for PDF with PaddleOCR): `sudo apt install poppler-utils` / `brew install poppler`.

### Repo path

All commands below assume you are in the pipeline repo:

```text
C:\Users\ASUS\OneDrive\Desktop\DOU\french-accounting-ai-saas-ai-pipeline
```

---

## Installation

### 1. Clone and enter the repo

```powershell
cd "C:\Users\ASUS\OneDrive\Desktop\DOU\french-accounting-ai-saas-ai-pipeline"
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` in your prompt.

### 3. Install dependencies

**Minimal (Tesseract + rule-based extraction, no LLM):**

```powershell
pip install pytesseract pdf2image opencv-python pillow structlog pydantic pydantic-settings
```

**With HTTP API (for backend integration):**

```powershell
pip install fastapi uvicorn python-multipart
```

**Optional – PaddleOCR (images + PDF):**

```powershell
pip install "paddlepaddle>=3.2.2" "paddleocr>=2.7.0.3" pdf2image opencv-python pillow pymupdf
```

(PaddleOCR 3.4 requires PaddlePaddle 3.x; 2.6.x will raise `set_optimization_level` errors.)

Ensure Poppler is installed and on PATH so `pdf2image` can convert PDFs.

**Optional – LLM (Gemini for better extraction):**

```powershell
pip install google-generativeai
```

Set `GEMINI_API_KEY` and `LLM_PROVIDER=gemini` (see [Configuration](#configuration)). If the LLM is not configured, the pipeline uses a rule-based fallback and logs a warning.

---

## Configuration

Configuration is via **environment variables** (and optional `.env` in the repo root).

### OCR

| Variable        | Description                                      | Default     |
|----------------|--------------------------------------------------|-------------|
| `OCR_PROVIDER` | `tesseract`, `paddle` / `paddleocr`, `google_document_ai`, `azure_form_recognizer` | `tesseract` |

- **Tesseract**: Requires Tesseract installed and on PATH.
- **Paddle**: Supports images and PDF; needs `paddlepaddle`, `paddleocr`, `pdf2image`, and Poppler for the primary path. If Poppler / `pdf2image` is not available (for example on Windows without Poppler), the provider can fall back to PyMuPDF (`pymupdf`) when installed.

### LLM (optional)

| Variable           | Description                    | Default |
|-------------------|--------------------------------|--------|
| `LLM_PROVIDER`    | `gemini`, `openai`, `anthropic`| `gemini`|
| `GEMINI_API_KEY`  | From [Google AI Studio](https://aistudio.google.com/app/apikey) | — |
| `GEMINI_MODEL`    | Model name                     | `models/gemini-2.0-flash` |
| `OPENAI_API_KEY`  | For `openai` provider          | — |
| `ANTHROPIC_API_KEY` | For `anthropic` provider     | — |

If no LLM is configured, the pipeline uses rule-based extraction from OCR text.

### Other

| Variable       | Description |
|----------------|-------------|
| `DATABASE_URL` | Required by the settings model; for CLI/API a dummy value is fine, e.g. `postgresql://dummy:dummy@localhost:5432/dummy`. |
| `PATH`         | On Windows, include Tesseract (and if using Paddle+PDF, Poppler) so the pipeline can find the binaries. |

**Example (PowerShell, Tesseract only):**

```powershell
$env:PATH = "C:\Program Files\Tesseract-OCR;" + $env:PATH
$env:OCR_PROVIDER = "tesseract"
$env:DATABASE_URL = "postgresql://dummy:dummy@localhost:5432/dummy"
```

**Example (with Gemini):**

```powershell
$env:LLM_PROVIDER = "gemini"
$env:GEMINI_API_KEY = "your-api-key"
$env:GEMINI_MODEL = "models/gemini-2.0-flash"
```

---

## Usage

### CLI – full invoice pipeline (OCR + classification + extraction)

Runs OCR, classifies the document, and extracts structured fields. Output is JSON (e.g. `document_type`, `ocr_text`, `supplier`, `total_amount`, `vat_amount`, `invoice_number`, `invoice_date`, `currency`, `raw_extraction`).

```powershell
cd "C:\Users\ASUS\OneDrive\Desktop\DOU\french-accounting-ai-saas-ai-pipeline"
.\.venv\Scripts\Activate.ps1

$env:PATH = "C:\Program Files\Tesseract-OCR;" + $env:PATH
$env:OCR_PROVIDER = "tesseract"
$env:DATABASE_URL = "postgresql://dummy:dummy@localhost:5432/dummy"

python -m ai_pipeline.llm_service.invoice_pipeline "C:\path\to\invoice.png" --tenant dev-tenant-1 --language fr
```

- **First argument**: Path to a **PDF or image** (PDF works only with `OCR_PROVIDER=paddle`).
- **`--tenant`**: Tenant identifier (default `tenant-dev-1`).
- **`--language`**: Language hint for OCR/extraction (default `fr`).

Example with a PDF (use PaddleOCR):

```powershell
$env:OCR_PROVIDER = "paddle"
python -m ai_pipeline.llm_service.invoice_pipeline "C:\path\to\invoice.pdf" --tenant dev-tenant-1
```

### CLI – OCR only (no classification/extraction)

For raw OCR text and confidence only, use the helper script or the worker directly.

**Using `run_ocr_manual.py`:** edit `FILE_PATH` in the file, then:

```powershell
python run_ocr_manual.py
```

**Using the worker from Python:**

```python
from ai_pipeline.ocr_service.worker import extract_text

result = extract_text(r"C:\path\to\receipt.png")
print(result["text"])       # OCR text
print(result["confidence"]) # 0–100 or None
```

### HTTP API (for backend integration)

Start the FastAPI app:

```powershell
pip install fastapi uvicorn python-multipart
$env:PATH = "C:\Program Files\Tesseract-OCR;" + $env:PATH
$env:OCR_PROVIDER = "tesseract"
$env:DATABASE_URL = "postgresql://dummy:dummy@localhost:5432/dummy"

uvicorn ai_pipeline.api.main:app --host 0.0.0.0 --port 8006
```

- **POST /extract**  
  - **Body**: multipart form with `file` (required), and optional `tenant_id`, `receipt_id`, `language`.  
  - **Response**: JSON with `supplier`, `invoice_number`, `invoice_date`, `vat_amount`, `total_amount`, `currency`, `ocr_text`, `document_type`, `raw_extraction`, etc.

- **GET /health**  
  - Returns `{"status": "ok", "service": "ai-pipeline"}`.

Test with the provided script (adjust port if needed, e.g. 8007 in `test_extract_api.py`):

```powershell
python test_extract_api.py "C:\path\to\receipt.png"
```

### Python API (in-process, no HTTP)

From another Python process (e.g. backend worker):

```python
from ai_pipeline.llm_service.invoice_pipeline import run_invoice_pipeline_as_dict

out = run_invoice_pipeline_as_dict(
    "/path/to/file.pdf",
    tenant_id="tenant-dev-1",
    receipt_id="optional-uuid",
    language="fr",
)
# out: dict with document_type, ocr_text, supplier, total_amount, vat_amount, currency, raw_extraction, ...
```

See [INTEGRATION.md](INTEGRATION.md) for how to plug this into the backend (HTTP vs in-process).

---

## Project structure

```text
french-accounting-ai-saas-ai-pipeline/
├── ai_pipeline/
│   ├── api/
│   │   └── main.py              # FastAPI app: POST /extract, GET /health
│   ├── ocr_service/
│   │   ├── config.py            # OCR settings (OCR_PROVIDER, Google/Azure, etc.)
│   │   ├── provider.py          # Provider interface + factory (get_ocr_provider)
│   │   ├── provider_tesseract.py # Tesseract (image-only)
│   │   ├── provider_paddle.py   # PaddleOCR (image + PDF)
│   │   ├── worker.py            # extract_text(file_path) → {text, confidence, ...}
│   │   ├── service.py           # OCR service layer
│   │   ├── routes.py
│   │   └── ...
│   ├── llm_service/
│   │   ├── config.py            # LLM_PROVIDER, Gemini/OpenAI/Anthropic keys
│   │   ├── invoice_pipeline.py  # Full pipeline: OCR → classify → extract (CLI entrypoint)
│   │   ├── classifier.py        # Document type from OCR text (invoice/receipt/...)
│   │   ├── extractor.py         # LLM extractor + rule-based fallback
│   │   ├── extractor_gemini.py  # Gemini implementation
│   │   ├── schemas.py           # ReceiptExtractionRequest / Response
│   │   └── ...
│   ├── workers/                 # Optional queue-based workers
│   ├── rag_service/             # Optional RAG/embeddings
│   └── anomaly_service/        # Optional anomaly detection
├── tests/
│   └── unit/
│       └── test_ocr_worker.py   # OCR worker tests (sample image)
├── run_ocr_manual.py           # Quick OCR-only script (edit FILE_PATH)
├── test_extract_api.py         # Quick POST /extract test
├── README.md                   # This file
└── INTEGRATION.md              # Backend integration (HTTP vs library)
```

---

## OCR providers

- **Tesseract** (`OCR_PROVIDER=tesseract`): Free, local, image-only. Good default for receipts/photos.
- **PaddleOCR** (`OCR_PROVIDER=paddle` or `paddleocr`): Supports images and PDF (via `pdf2image` + Poppler by default). When Poppler/`pdf2image` is missing, it will automatically fall back to PyMuPDF if `pymupdf` is installed (pure-Python, no external binaries; especially useful on Windows).
- **Google Document AI** / **Azure Form Recognizer**: Stubs exist in `provider.py`; set `OCR_PROVIDER=google_document_ai` or `azure_form_recognizer`. Full implementation is left for you (credentials and client calls).

Provider is selected in `ai_pipeline/ocr_service/provider.py` via `get_ocr_provider()` using `settings.OCR_PROVIDER`.

---

## LLM and extraction

- **Gemini** (default if `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` set): Structured extraction from OCR text.
- **OpenAI / Anthropic**: Configure via `OPENAI_*` / `ANTHROPIC_*` env vars; used by `extractor.py`.
- **Rule-based fallback**: If no LLM is configured or the LLM fails, the pipeline extracts amounts, dates, and merchant from OCR text using regex and heuristics. No API key needed.

Document classification (invoice vs receipt vs bank_statement vs payslip vs other) is keyword-based in `classifier.py` and does not use an LLM.

---

## Integration with the backend

The **frontend** does not call the AI pipeline. Flow: **Frontend → Backend (upload) → Backend uses OCR + extraction → Frontend gets receipt/expense data.**

Two ways for the backend to use this pipeline:

1. **HTTP (recommended)**  
   Run this repo as a service (e.g. `uvicorn` on port 8006). Backend sets `AI_PIPELINE_URL=http://localhost:8006` and sends `POST /extract` with the file. See [INTEGRATION.md](INTEGRATION.md).

2. **In-process**  
   Install this repo as a dependency in the backend and call `run_invoice_pipeline_as_dict(path, ...)` from the receipt pipeline. See [INTEGRATION.md](INTEGRATION.md).

Details, code snippets, and env vars are in **[INTEGRATION.md](INTEGRATION.md)**.

---

## Testing

Run the OCR worker unit tests (they create a small invoice-like image; no committed file needed):

```powershell
pip install pytest
pytest tests/unit/test_ocr_worker.py -v
```

Tests check that `extract_text()` returns the expected structure (`text`, `confidence`, etc.) and, when Tesseract or PaddleOCR is available, non-empty text and sensible content.

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| `tesseract` not found | Add Tesseract’s install directory to `PATH` (e.g. `C:\Program Files\Tesseract-OCR` on Windows). |
| PDF upload fails with Tesseract | Tesseract cannot read PDFs. Use `OCR_PROVIDER=paddle` and install `pdf2image` + Poppler, or convert PDF to images before calling the pipeline. |
| `pdf2image` / Poppler error with PaddleOCR | Either install Poppler and add its `bin` folder to PATH (and set `POPPLER_PATH` on Windows) so `pdf2image` can find `pdfinfo.exe`, or install PyMuPDF (`pip install pymupdf`) so the pipeline can fall back to a pure-Python PDF renderer. |
| Empty or poor extraction | Ensure OCR runs (check logs for `tesseract_ocr_extraction_completed` or PaddleOCR). For better fields, set `GEMINI_API_KEY` and `LLM_PROVIDER=gemini`. |
| `DATABASE_URL` required | The config model expects it; for CLI/API a dummy value is fine, e.g. `postgresql://dummy:dummy@localhost:5432/dummy`. |
| API returns 500 | Check logs for OCR or LLM errors. Confirm file is image (or PDF only when using PaddleOCR) and that env vars (e.g. `OCR_PROVIDER`, PATH) are set in the process that runs uvicorn. |

---

## License and attribution

Part of the French Accounting AI SaaS (Dou Expense & Audit – France Edition). See repository and company documentation for license and attribution.
