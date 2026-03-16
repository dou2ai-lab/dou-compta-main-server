# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Pydantic schemas for request/response validation in OCR service
# -----------------------------------------------------------------------------

"""
Pydantic schemas for OCR Service
"""
from pydantic import BaseModel
from typing import Optional, Dict

class OCRCallbackResponse(BaseModel):
    success: bool
    data: Dict

class OCRJobResponse(BaseModel):
    job_id: str
    receipt_id: str
    status: str
    provider: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    retry_count: int

class OCRResultResponse(BaseModel):
    job_id: str
    receipt_id: str
    status: str
    extracted_data: Dict
    confidence_scores: Dict
    raw_response: Optional[Dict]
    normalized_at: Optional[str]









