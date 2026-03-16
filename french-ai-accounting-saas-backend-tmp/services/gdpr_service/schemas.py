# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Pydantic schemas for GDPR service
# -----------------------------------------------------------------------------

"""
Pydantic schemas for GDPR Service
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any

class DataSubjectRequestCreate(BaseModel):
    """Create data subject request"""
    request_type: str = Field(..., pattern="^(access|rectification|erasure|portability)$")
    subject_email: EmailStr
    subject_name: Optional[str] = None
    subject_id: Optional[str] = None

class DataSubjectRequestVerify(BaseModel):
    """Verify data subject request"""
    verification_token: str

class DataSubjectRequestResponse(BaseModel):
    """Data subject request response"""
    success: bool
    request_id: str
    verification_token: Optional[str] = None
    status: str




