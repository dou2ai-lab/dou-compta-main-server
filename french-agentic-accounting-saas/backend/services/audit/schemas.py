# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Pydantic schemas for audit service
# -----------------------------------------------------------------------------

"""
Pydantic schemas for Audit Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID

class AuditReportCreate(BaseModel):
    """Create audit report request"""
    title: str = Field(..., min_length=1, max_length=255)
    period_start: date
    period_end: date
    period_type: str = Field(default="custom", pattern="^(monthly|quarterly|annual|custom)$")
    report_type: str = Field(default="combined", pattern="^(technical|narrative|combined)$")
    description: Optional[str] = None

class AuditReportResponse(BaseModel):
    """Audit report response"""
    id: str
    report_number: str
    title: str
    description: Optional[str]
    audit_period_start: date
    audit_period_end: date
    period_type: str
    report_type: str
    status: str
    template_version: str
    sample_size: int
    total_expenses_in_scope: int
    total_amount_in_scope: float
    technical_data: Dict[str, Any]
    narrative_sections: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PendingExpenseReportItem(BaseModel):
    """Expense report submitted for approval, shown in Audit Reports for auditor review"""
    id: str
    report_number: str
    title: Optional[str]
    period_start_date: Optional[date]
    period_end_date: Optional[date]
    total_amount: float
    currency: str
    expense_count: int
    status: str
    approval_status: Optional[str]
    submitted_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditReportUpdate(BaseModel):
    """Update audit report request"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|in_progress|completed|published)$")
    technical_data: Optional[Dict[str, Any]] = None
    narrative_sections: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AuditMetadataCreate(BaseModel):
    """Create audit metadata request"""
    key: str = Field(..., min_length=1, max_length=100)
    value: Any

class AuditMetadataResponse(BaseModel):
    """Audit metadata response"""
    id: str
    key: str
    value: Dict[str, Any]
    data_type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EvidenceCollectionRequest(BaseModel):
    """Evidence collection request"""
    expense_ids: List[str] = Field(..., min_items=1)

class EvidenceCollectionResponse(BaseModel):
    """Evidence collection response"""
    success: bool
    audit_report_id: str
    expenses_processed: int
    evidence_items_collected: int
    evidence_items: List[Dict[str, Any]]
    error: Optional[str] = None

class EvidenceItem(BaseModel):
    """Evidence item response"""
    id: str
    evidence_type: str
    evidence_category: str
    description: str
    expense_id: Optional[str]
    receipt_id: Optional[str]
    file_name: Optional[str]
    file_size: Optional[int]
    mime_type: Optional[str]
    metadata: Dict[str, Any]
    collected_at: datetime
    
    class Config:
        from_attributes = True

class SignedUrlResponse(BaseModel):
    """Signed URL response"""
    evidence_id: str
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    signed_url: str
    expires_at: str
    evidence_type: str

class AuditScopeCreate(BaseModel):
    """Create audit scope request"""
    scope_type: str = Field(..., pattern="^(period|department|employee|merchant|category)$")
    scope_value: Optional[str] = None
    scope_criteria: Optional[Dict[str, Any]] = None
    is_included: bool = True
    priority: int = Field(default=0, ge=0)

class PopulateReportRequest(BaseModel):
    """Populate report from sample request"""
    sample_expense_ids: List[str] = Field(..., min_items=1)

# Phase 19 & 20 Schemas

class AuditTrailResponse(BaseModel):
    """Audit trail response"""
    id: str
    entity_type: str
    entity_id: str
    action: str
    performed_by: str
    performed_at: datetime
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True

class SnapshotVerificationResponse(BaseModel):
    """Snapshot verification response"""
    valid: bool
    snapshot_id: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    action: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None
    expected_hash: Optional[str] = None
    calculated_hash: Optional[str] = None

class BasicReportRequest(BaseModel):
    """Basic report generation request"""
    period_start: date
    period_end: date
    expense_ids: Optional[List[str]] = None

class BasicReportResponse(BaseModel):
    """Basic report response (5.2.3)"""
    report_period: Dict[str, str]
    generated_at: str
    total_expenses: int
    spend_summary: Dict[str, Any]
    policy_violations: Dict[str, Any]
    vat_summary: Dict[str, Any]
    executive_summary: Optional[str] = None
    top_risk_employees: Optional[List[Dict[str, Any]]] = None
    top_risk_merchants: Optional[List[Dict[str, Any]]] = None

# Phase 23 & 24 Schemas

class CoPilotRequest(BaseModel):
    """Co-pilot query request"""
    query: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None

class CoPilotResponse(BaseModel):
    """Co-pilot response"""
    success: bool
    answer: str
    citations: List[Dict[str, Any]]
    reasoning_steps: List[Dict[str, Any]]
    confidence_score: str
    query_type: str
    retrieved_documents: List[Dict[str, Any]]
    session_id: str
    error: Optional[str] = None

class NarrativeGenerationRequest(BaseModel):
    """Narrative generation request"""
    report_id: Optional[str] = None
    period_start: date
    period_end: date
    report_data: Optional[Dict[str, Any]] = None

class NarrativeGenerationResponse(BaseModel):
    """Narrative generation response"""
    success: bool
    narratives: Dict[str, Any]
    generated_at: str

