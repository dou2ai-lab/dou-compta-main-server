# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Expense service models and schemas
# -----------------------------------------------------------------------------

"""
Expense service models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal

class ExpenseCreate(BaseModel):
    """Create expense request"""
    amount: Decimal = Field(..., gt=0, description="Expense amount")
    currency: str = Field(default="EUR", max_length=3)
    expense_date: date
    category: Optional[str] = None
    description: Optional[str] = None
    merchant_name: Optional[str] = None
    vat_amount: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None
    receipt_ids: Optional[List[UUID]] = []

class ExpenseUpdate(BaseModel):
    """Update expense request"""
    amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    expense_date: Optional[date] = None
    category: Optional[str] = None
    description: Optional[str] = None
    merchant_name: Optional[str] = None
    vat_amount: Optional[Decimal] = None
    vat_rate: Optional[Decimal] = None

class ExpenseResponse(BaseModel):
    """Expense response"""
    id: UUID
    tenant_id: UUID
    submitted_by: UUID
    submitted_by_name: Optional[str] = None
    submitted_by_email: Optional[str] = None
    amount: Decimal
    currency: str
    expense_date: date
    category: Optional[str]
    description: Optional[str]
    merchant_name: Optional[str]
    status: str
    approval_status: Optional[str]
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    vat_amount: Optional[Decimal]
    vat_rate: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    receipt_ids: List[UUID] = []
    submitter_display_name: Optional[str] = None

    class Config:
        from_attributes = True

class ExpenseListResponse(BaseModel):
    """Expense list response"""
    success: bool = True
    data: List[ExpenseResponse]
    total: int
    page: int
    page_size: int

class ExpenseDetailResponse(BaseModel):
    """Expense detail response"""
    success: bool = True
    data: ExpenseResponse

class ExpenseApproveRequest(BaseModel):
    """Approve expense request"""
    notes: Optional[str] = None

class ExpenseRejectRequest(BaseModel):
    """Reject expense request"""
    reason: str = Field(..., min_length=1)
































