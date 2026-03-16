# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Expense report service models and schemas
# -----------------------------------------------------------------------------

"""
Expense report service models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal

class ReportType(str):
    """Report type enum"""
    PERIOD = "period"
    TRIP = "trip"

class ExpenseReportCreate(BaseModel):
    """Create expense report request"""
    report_type: str = Field(..., description="Type of report: period or trip")
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Period-based fields
    period_start_date: Optional[date] = None
    period_end_date: Optional[date] = None
    period_type: Optional[str] = None  # monthly, weekly, custom
    
    # Trip-based fields
    trip_name: Optional[str] = None
    trip_start_date: Optional[date] = None
    trip_end_date: Optional[date] = None
    trip_destination: Optional[str] = None
    
    expense_ids: List[UUID] = Field(default_factory=list, description="List of expense IDs to include")

class ExpenseReportUpdate(BaseModel):
    """Update expense report request"""
    title: Optional[str] = None
    description: Optional[str] = None
    expense_ids: Optional[List[UUID]] = None

class ExpenseReportResponse(BaseModel):
    """Expense report response"""
    id: UUID
    tenant_id: UUID
    submitted_by: UUID
    report_number: str
    report_type: str
    title: Optional[str]
    description: Optional[str]
    period_start_date: Optional[date]
    period_end_date: Optional[date]
    period_type: Optional[str]
    trip_name: Optional[str]
    trip_start_date: Optional[date]
    trip_end_date: Optional[date]
    trip_destination: Optional[str]
    total_amount: Decimal
    currency: str
    expense_count: int
    status: str
    approval_status: Optional[str]
    submitted_at: Optional[datetime]
    approver_id: Optional[UUID]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    approval_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    expense_ids: List[UUID] = []
    
    class Config:
        from_attributes = True

class ExpenseReportListResponse(BaseModel):
    """Expense report list response"""
    success: bool = True
    data: List[ExpenseReportResponse]
    total: int
    page: int
    page_size: int

class ExpenseReportDetailResponse(BaseModel):
    """Expense report detail response"""
    success: bool = True
    data: ExpenseReportResponse

class ExpenseReportSubmitRequest(BaseModel):
    """Submit expense report request"""
    notes: Optional[str] = None

class ExpenseReportApproveRequest(BaseModel):
    """Approve expense report request"""
    notes: Optional[str] = None

class ExpenseReportRejectRequest(BaseModel):
    """Reject expense report request"""
    reason: str = Field(..., min_length=1)


class ReportExpenseItemResponse(BaseModel):
    """Expense item as returned in report expenses list"""
    id: UUID
    amount: Decimal
    currency: str
    expense_date: Optional[date]
    merchant_name: Optional[str]
    category: Optional[str]
    description: Optional[str]
    vat_amount: Optional[Decimal]
    vat_rate: Optional[Decimal]
    status: Optional[str]
    approval_status: Optional[str]

    class Config:
        from_attributes = True


class ReportExpensesListResponse(BaseModel):
    """List of expenses in a report"""
    success: bool = True
    data: List[ReportExpenseItemResponse]



























