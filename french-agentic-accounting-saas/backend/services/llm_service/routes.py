# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: API routes for LLM extraction service
# -----------------------------------------------------------------------------

"""
API routes for LLM Service
"""
from fastapi import APIRouter, HTTPException, status
import structlog

from .schemas import ReceiptExtractionRequest, ReceiptExtractionResponse
from .extractor import LLMExtractor

logger = structlog.get_logger()
router = APIRouter()

extractor = LLMExtractor()

@router.post("/extract", response_model=ReceiptExtractionResponse)
async def extract_receipt_data(request: ReceiptExtractionRequest):
    """
    Extract structured data from OCR text using LLM
    
    - **ocr_text**: Raw OCR extracted text
    - **receipt_id**: Receipt document ID
    - **tenant_id**: Tenant ID
    - **language**: Receipt language (default: fr)
    """
    try:
        logger.info("extraction_requested", receipt_id=request.receipt_id)
        
        result = await extractor.extract(request)
        
        logger.info("extraction_completed", receipt_id=request.receipt_id)
        return result
        
    except Exception as e:
        logger.error("extraction_failed", error=str(e), receipt_id=request.receipt_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract receipt data: {str(e)}"
        )




























