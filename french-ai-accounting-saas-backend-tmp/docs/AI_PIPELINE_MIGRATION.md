# AI Pipeline → Backend Migration

This document tracks migrating features from the **french-accounting-ai-saas-ai-pipeline** repo into **french-ai-accounting-saas-backend-tmp** so all AI/OCR capabilities live in the backend.

## Pipeline repo location

- **Path**: `dou-compta-main-server/french-accounting-ai-saas-ai-pipeline/`
- **Contents**: OCR (Tesseract + Paddle), LLM extraction, document classification, RAG, anomaly service, workers, HTTP API (`POST /extract`)

## Backend already has

- `services/ocr_service`: Tesseract provider, config, routes, consumer, events, normalizer
- `services/llm_service`: extractor, extractor_gemini, worker, routes, config
- `services/rag_service`: embeddings, qa_service, agentic_copilot
- `services/anomaly_service`: risk scoring, explainers
- `services/file_service/receipt_pipeline.py`: in-process OCR → LLM extract → expense
- `common/receipt_extraction.py`: rule-based extraction from OCR text
- `workers/`: receipt_worker, export_worker (under backend root)

## Migration checklist

| Feature | Pipeline source | Backend target | Status |
|--------|------------------|----------------|--------|
| **Paddle OCR** (image + PDF) | `ai_pipeline/ocr_service/provider_paddle.py` | `services/ocr_service/provider_paddle.py` | ✅ Done |
| **OCR provider factory** (paddle/paddleocr) | pipeline `provider.py` `get_ocr_provider` | `services/ocr_service/provider.py` | ✅ Done |
| **Document classifier** (invoice/receipt/bank_statement/payslip) | `ai_pipeline/llm_service/classifier.py` | `services/llm_service/classifier.py` | ✅ Done |
| **Full invoice pipeline** (OCR → classify → extract) | `ai_pipeline/llm_service` invoice_pipeline | `services/llm_service/invoice_pipeline.py` | ✅ Done |
| **POST /extract API** (file upload → pipeline JSON) | `ai_pipeline/api/main.py` | `POST /api/v1/receipts/extract` (file_service) | ✅ Done |
| **OCR worker** (extract_text for scripts) | `ai_pipeline/ocr_service/worker.py` | `services/ocr_service/worker.py` | ✅ Done |
| **RAG / Anomaly** | Pipeline has versions | Backend has own; sync if pipeline is newer | Optional |

## Usage after migration

- **OCR_PROVIDER**: Set to `tesseract` (default), `paddle` / `paddleocr`, `google_document_ai`, or `azure_form_recognizer`. Paddle supports PDFs (requires `pdf2image` + Poppler or `pymupdf`).
- **Optional deps for Paddle**: `pip install paddlepaddle paddleocr pdf2image opencv-python pillow pymupdf` (see `requirements.txt` or optional deps file).
- **Full pipeline (upload → extract)**:
  - **POST /api/v1/receipts/extract** (file_service): send a multipart file; returns `document_type`, `ocr_text`, `ocr_confidence`, `supplier`, `invoice_number`, `invoice_date`, `vat_amount`, `total_amount`, `currency`, `raw_extraction`.
  - **From code**: `from services.llm_service.invoice_pipeline import run_invoice_pipeline` then `await run_invoice_pipeline(file_path="...")` or `await run_invoice_pipeline(file_content=bytes, mime_type="image/png", tenant_id="dev", language="fr")`.
- **OCR only (script/local file)**: `from services.ocr_service.worker import extract_text` then `extract_text("/path/to/image_or_pdf")` → `{ "text", "confidence", "raw_response" }`.

## References

- Pipeline README: `french-accounting-ai-saas-ai-pipeline/README.md`
- Backend receipt flow: `services/file_service/receipt_pipeline.py`, `services/ocr_service/service.py`
