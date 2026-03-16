"""
Simple OCR worker helper for local/manual runs.

Public API is kept minimal and stable:
- extract_text(file_path: str) -> dict with at least "text" and "confidence".

This implementation uses PaddleOCR directly so that PDF inputs can take advantage
of the pdf2image+Poppler path and the PyMuPDF fallback implemented in
PaddleOCRProvider.
"""
from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path
from typing import Any, Dict

import structlog

from .provider_paddle import PaddleOCRProvider


logger = structlog.get_logger()


def _detect_mime_type(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    # Default to image/jpeg if unknown; PaddleOCR handles common image types and PDFs explicitly.
    return mime or "image/jpeg"


def extract_text(file_path: str) -> Dict[str, Any]:
    """
    Run OCR on a local file path using PaddleOCR.

    Returns a dict with:
    - text: combined OCR text
    - confidence: overall confidence score if available
    - raw_response: underlying provider payload
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"OCR input file not found: {file_path}")

    file_content = path.read_bytes()
    mime_type = _detect_mime_type(path)

    provider = PaddleOCRProvider()

    async def _run() -> Dict[str, Any]:
        return await provider.extract(file_content, mime_type)

    logger.info("ocr_worker_started", file=str(path), mime_type=mime_type)
    result = asyncio.run(_run())

    text = result.get("text") or result.get("ocr_text") or ""
    confidence = None
    scores = result.get("confidence_scores") or {}
    if isinstance(scores, dict):
        confidence = scores.get("overall", scores.get("confidence"))

    logger.info(
        "ocr_worker_completed",
        file=str(path),
        text_length=len(text),
        confidence=confidence,
    )

    return {
        "text": text,
        "confidence": confidence,
        "raw_response": result,
    }

