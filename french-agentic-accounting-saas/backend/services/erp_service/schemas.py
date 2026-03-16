# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Pydantic schemas for ERP service
# -----------------------------------------------------------------------------

"""
Pydantic schemas for ERP Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

class ERPConnectionCreate(BaseModel):
    """Create ERP connection"""
    provider: str = Field(..., pattern="^(sap|netsuite|odoo)$")
    connection_type: str = Field(..., pattern="^(api|sftp)$")
    configuration: Dict[str, Any]

class ERPConnectionResponse(BaseModel):
    """ERP connection response"""
    id: str
    provider: str
    connection_type: str
    is_active: bool
    last_sync_at: Optional[str] = None
    last_sync_status: Optional[str] = None
    created_at: str

class PostExpenseRequest(BaseModel):
    """Post expense to ERP"""
    expense_id: str
    erp_connection_id: Optional[str] = None
    posting_date: Optional[datetime] = None

class PostExpenseResponse(BaseModel):
    """Post expense response"""
    success: bool
    expense_id: str
    postings: List[Dict[str, Any]]

class SEPACreateRequest(BaseModel):
    """Create SEPA file request"""
    expense_ids: List[str]
    creditor_iban: str
    creditor_bic: Optional[str] = None
    creditor_name: Optional[str] = None
    execution_date: Optional[date] = None

class SEPACreateResponse(BaseModel):
    """SEPA file creation response"""
    success: bool
    file_id: str
    file_name: str
    file_path: str
    transaction_count: int
    total_amount: float
    xml_content: Optional[str] = None

class CardPaymentImportRequest(BaseModel):
    """Import card payment"""
    card_transaction_id: str
    card_last_four: str
    merchant_name: str
    transaction_date: datetime
    amount: Decimal
    currency: str = "EUR"
    metadata: Optional[Dict[str, Any]] = None

class CardPaymentImportResponse(BaseModel):
    """Card payment import response"""
    success: bool
    reconciliation_id: str
    matched: bool
    expense_id: Optional[str] = None
    confidence: Optional[float] = None

class ManualReconcileRequest(BaseModel):
    """Manual reconciliation request"""
    reconciliation_id: str
    expense_id: str




