# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: API routes for OCR service including job status and result endpoints
# -----------------------------------------------------------------------------

"""
OCR Service Routes
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
import asyncio
import structlog

from .schemas import OCRCallbackResponse, OCRJobResponse, OCRResultResponse
from .consumer import process_receipt_uploaded

router = APIRouter()
logger = structlog.get_logger()


@router.post("/ocr/process-event")
async def process_ocr_event(payload: Dict):
    """
    Development helper endpoint: trigger OCR processing directly without RabbitMQ.

    This accepts the same event shape as the `receipt.uploaded` message:
    {
      "receipt_id": "...",
      "tenant_id": "...",
      "user_id": "...",
      "payload": { "storage_path": "...", "mime_type": "...", ... }
    }
    """
    try:
        receipt_id = payload.get("receipt_id")
        if not receipt_id:
            raise HTTPException(status_code=400, detail="receipt_id is required")

        # Fire-and-forget; OCR will update receipt_documents.ocr_status/meta_data.
        asyncio.create_task(process_receipt_uploaded(payload))
        logger.info("ocr_process_event_queued", receipt_id=receipt_id)
        return {"queued": True, "receipt_id": receipt_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ocr_process_event_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ocr/callback", response_model=OCRCallbackResponse)
async def ocr_callback(payload: Dict):
    """
    Webhook endpoint for OCR provider callbacks (if supported)
    """
    # TODO: Verify webhook signature
    # TODO: Process callback
    # TODO: Update OCR job status
    return {"success": True, "data": {"status": "processed"}}

@router.get("/ocr/jobs/{job_id}", response_model=OCRJobResponse)
async def get_ocr_job(job_id: str):
    """Get OCR job status"""
    # TODO: Query database for OCR job
    raise NotImplementedError

@router.get("/ocr/jobs/{job_id}/result", response_model=OCRResultResponse)
async def get_ocr_result(job_id: str):
    """Get OCR extraction result"""
    # TODO: Query database for OCR result
    raise NotImplementedError









