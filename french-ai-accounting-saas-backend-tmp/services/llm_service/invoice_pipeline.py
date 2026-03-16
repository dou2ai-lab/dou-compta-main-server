# -----------------------------------------------------------------------------
# Full invoice/receipt pipeline: OCR → classify → LLM/regex extraction.
# Single entry point for upload or script use. Returns document_type + extracted fields.
# -----------------------------------------------------------------------------
"""
Invoice/Receipt pipeline: OCR → document classification → field extraction (LLM + regex fallback).
Use run_invoice_pipeline(file_path=...) or run_invoice_pipeline(file_content=..., mime_type=...).
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

from common.receipt_extraction import extract_from_ocr_text
from .classifier import classify_document
from .extractor import LLMExtractor
from .schemas import ReceiptExtractionRequest, ReceiptExtractionResponse

logger = structlog.get_logger()


async def _ocr_from_content(file_content: bytes, mime_type: str) -> Dict[str, Any]:
    """Run OCR on in-memory content. Converts PDF to image so any provider (Paddle or Tesseract) gets an image."""
    from services.ocr_service.provider import get_ocr_provider

    # Always convert PDF to first-page image; providers expect image bytes (Tesseract can't read PDF, Paddle fallback uses Tesseract)
    if mime_type == "application/pdf":
        try:
            from services.ocr_service.worker import _pdf_to_first_image_bytes
            file_content = _pdf_to_first_image_bytes(file_content)
            mime_type = "image/png"
        except Exception as e:
            logger.warning("pdf_to_image_failed", error=str(e))
            return {"text": "", "confidence": None, "raw_response": {"error": str(e)}}

    provider = get_ocr_provider()
    result = await provider.extract(file_content, mime_type)
    text = result.get("text") or result.get("ocr_text") or ""
    confidence = None
    scores = result.get("confidence_scores") or {}
    if isinstance(scores, dict):
        confidence = scores.get("overall", scores.get("confidence"))
    if confidence is not None and 0 <= confidence <= 1:
        confidence = round(confidence * 100, 1)
    return {"text": text, "confidence": confidence, "raw_response": result}


def _response_to_extraction_dict(res: ReceiptExtractionResponse) -> Dict[str, Any]:
    """Convert ReceiptExtractionResponse to a flat dict for API output."""
    expense_date_str = None
    if res.expense_date:
        expense_date_str = res.expense_date.isoformat() if hasattr(res.expense_date, "isoformat") else str(res.expense_date)
    out: Dict[str, Any] = {
        "supplier": res.merchant_name,
        "merchant_name": res.merchant_name,
        "invoice_number": res.invoice_number,
        "invoice_date": expense_date_str,
        "expense_date": expense_date_str,
        "vat_amount": float(res.vat_amount) if res.vat_amount is not None else None,
        "total_amount": float(res.total_amount) if res.total_amount is not None else None,
        "currency": res.currency or "EUR",
        "vat_rate": float(res.vat_rate) if res.vat_rate is not None else None,
        "line_items": res.line_items,
        "confidence_scores": res.confidence_scores,
    }
    return out


async def run_invoice_pipeline(
    *,
    file_path: Optional[str] = None,
    file_content: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    tenant_id: str = "dev",
    language: str = "fr",
    receipt_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the full pipeline: OCR → classify → extract.

    Provide either:
      - file_path: path to a local file (image or PDF), or
      - file_content + mime_type: in-memory file (e.g. from upload).

    Returns a dict with:
      - document_type: invoice | receipt | bank_statement | payslip | other
      - ocr_text: raw OCR text
      - ocr_confidence: OCR confidence 0–100 or null
      - supplier / merchant_name, invoice_number, invoice_date, vat_amount, total_amount, currency
      - raw_extraction: full extraction dict (LLM or regex fallback)
    """
    if not file_path and not file_content:
        raise ValueError("Provide either file_path or file_content")

    rid = receipt_id or "pipeline"

    # Step 1: OCR
    if file_path:
        from services.ocr_service.worker import extract_text
        # Sync worker expects file on disk
        ocr_result = extract_text(file_path)
        ocr_text = ocr_result.get("text") or ""
        ocr_confidence = ocr_result.get("confidence")
    else:
        mime = mime_type or "image/jpeg"
        ocr_result = await _ocr_from_content(file_content, mime)
        ocr_text = ocr_result.get("text") or ""
        ocr_confidence = ocr_result.get("confidence")

    # Step 2: Classify
    document_type = classify_document(ocr_text)
    logger.info("pipeline_classified", document_type=document_type, receipt_id=rid)

    # Step 3: Extract fields (LLM with regex fallback)
    extraction_dict: Dict[str, Any] = {}
    try:
        extractor = LLMExtractor()
        req = ReceiptExtractionRequest(
            ocr_text=ocr_text,
            receipt_id=rid,
            tenant_id=tenant_id,
            language=language,
        )
        response = await extractor.extract(req)
        extraction_dict = _response_to_extraction_dict(response)
        extraction_dict["_source"] = "llm"
    except Exception as e:
        logger.warning("llm_extraction_failed_using_regex", error=str(e), receipt_id=rid)
        raw = extract_from_ocr_text(ocr_text)
        expense_date_val = raw.get("expense_date")
        if expense_date_val and hasattr(expense_date_val, "isoformat"):
            expense_date_val = expense_date_val.isoformat()
        else:
            expense_date_val = str(expense_date_val) if expense_date_val else None
        extraction_dict = {
            "supplier": raw.get("merchant_name"),
            "merchant_name": raw.get("merchant_name"),
            "invoice_number": raw.get("invoice_number"),
            "invoice_date": expense_date_val,
            "expense_date": expense_date_val,
            "vat_amount": raw.get("vat_amount"),
            "total_amount": raw.get("total_amount"),
            "currency": raw.get("currency") or "EUR",
            "vat_rate": raw.get("vat_rate"),
            "line_items": [],
            "confidence_scores": {},
            "_source": "regex",
        }

    return {
        "document_type": document_type,
        "ocr_text": ocr_text,
        "ocr_confidence": ocr_confidence,
        "raw_extraction": extraction_dict,
        "supplier": extraction_dict.get("supplier") or extraction_dict.get("merchant_name"),
        "invoice_number": extraction_dict.get("invoice_number"),
        "invoice_date": extraction_dict.get("invoice_date") or extraction_dict.get("expense_date"),
        "vat_amount": extraction_dict.get("vat_amount"),
        "total_amount": extraction_dict.get("total_amount"),
        "currency": extraction_dict.get("currency") or "EUR",
    }
