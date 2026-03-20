# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Pydantic schemas for request/response validation in file service
# -----------------------------------------------------------------------------

"""
Pydantic schemas for File Service
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ReceiptUploadResponse(BaseModel):
    receipt_id: str
    file_id: str
    status: str
    ocr_status: str
    file_name: str
    file_size: int
    mime_type: str
    uploaded_at: str
    expense_id: Optional[str] = None
    meta_data: Optional[dict] = None

class ReceiptStatusResponse(BaseModel):
    receipt_id: str
    upload_status: str
    ocr_status: str
    ocr_progress: Optional[int] = None
    ocr_job_id: Optional[str] = None
    estimated_completion: Optional[str] = None
    error: Optional[str] = None
    last_updated: str

class ReceiptDownloadResponse(BaseModel):
    receipt_id: str
    download_url: str
    expires_at: str
    expires_in: int

class ErrorResponse(BaseModel):
    success: bool = False
    errors: list[dict]


class ReceiptCorrectionsRequest(BaseModel):
    """
    Human-in-the-loop corrections payload.
    corrected_values is the user's final values (what they edited in UI).
    predicted_extraction is the model's latest extraction snapshot (optional but recommended).
    """
    corrected_values: Dict[str, Any]
    predicted_extraction: Optional[Dict[str, Any]] = None









