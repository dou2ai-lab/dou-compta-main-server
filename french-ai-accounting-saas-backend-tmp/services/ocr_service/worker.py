# -----------------------------------------------------------------------------
# OCR Worker – extract_text(file_path) for receipt/invoice pipeline.
# Runs OCR (Tesseract or Paddle), returns raw text and confidence.
# PDF: Paddle handles natively; Tesseract uses PDF→image conversion.
# -----------------------------------------------------------------------------
"""
OCR Worker
- extract_text(file_path) -> { text, confidence, raw_response }
- Supports images and PDF (PDF via PaddleOCR or PDF→image for Tesseract).
"""
from __future__ import annotations

import asyncio
import io
import mimetypes
from pathlib import Path
from typing import Any, Dict

import structlog

from .config import settings
from .provider import get_ocr_provider

logger = structlog.get_logger()


def _detect_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    return mime or "image/jpeg"


def _pdf_to_first_image_bytes(file_content: bytes) -> bytes:
    """Convert first page of PDF to image bytes (PNG) for Tesseract. Uses pdf2image or pymupdf."""
    # Try pdf2image (Poppler)
    try:
        from pdf2image import convert_from_bytes
        import os
        poppler_path = os.environ.get("POPPLER_PATH") or None
        if poppler_path and not os.path.isdir(poppler_path):
            poppler_path = None
        images = convert_from_bytes(file_content, first_page=1, last_page=1, poppler_path=poppler_path)
        if not images:
            raise ValueError("PDF produced no images")
        buf = io.BytesIO()
        images[0].save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.warning("pdf2image_failed_trying_pymupdf", error=str(e))
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_content, filetype="pdf")
            try:
                page = doc[0]
                pix = page.get_pixmap(dpi=200)
                from PIL import Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue()
            finally:
                doc.close()
        except ImportError:
            raise RuntimeError(
                "PDF input requires PaddleOCR (OCR_PROVIDER=paddle) or install pdf2image+Poppler or pymupdf for Tesseract."
            ) from e


def extract_text(file_path: str) -> Dict[str, Any]:
    """
    Run OCR on a local file (image or PDF).

    Returns:
        - text: combined OCR text
        - confidence: overall confidence 0–100 or None
        - raw_response: full provider result
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"OCR input file not found: {file_path}")

    file_content = path.read_bytes()
    mime_type = _detect_mime(path)

    async def _run() -> Dict[str, Any]:
        provider = get_ocr_provider()
        # If PDF and Tesseract, convert PDF to first page image
        if mime_type == "application/pdf" and (settings.OCR_PROVIDER or "").strip().lower() == "tesseract":
            file_content_to_use = _pdf_to_first_image_bytes(file_content)
            mime_to_use = "image/png"
        else:
            file_content_to_use = file_content
            mime_to_use = mime_type
        return await provider.extract(file_content_to_use, mime_to_use)

    logger.info("ocr_worker_started", file=str(path), mime_type=mime_type)
    result = asyncio.run(_run())

    text = result.get("text") or result.get("ocr_text") or ""
    confidence = None
    scores = result.get("confidence_scores") or {}
    if isinstance(scores, dict):
        confidence = scores.get("overall", scores.get("confidence"))
    if confidence is not None and 0 <= confidence <= 1:
        confidence = round(confidence * 100, 1)

    logger.info("ocr_worker_completed", file=str(path), text_length=len(text), confidence=confidence)

    return {
        "text": text,
        "confidence": confidence,
        "raw_response": result,
    }
