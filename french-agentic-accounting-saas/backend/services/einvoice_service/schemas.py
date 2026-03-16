"""Pydantic schemas for the E-Invoice Service."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

class InvoiceLineCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    vat_rate: Decimal = Decimal("20")
    account_code: Optional[str] = None

class InvoiceCreate(BaseModel):
    type: str = "sent"
    invoice_number: Optional[str] = None
    recipient_name: str
    recipient_siren: Optional[str] = None
    recipient_vat_number: Optional[str] = None
    issue_date: date
    due_date: Optional[date] = None
    lines: List[InvoiceLineCreate] = []
    notes: Optional[str] = None

class InvoiceLineResponse(BaseModel):
    id: UUID
    line_number: int
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate: Decimal
    line_total_ht: Decimal
    line_total_vat: Decimal
    account_code: Optional[str] = None
    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str
    type: str
    format: Optional[str] = None
    status: str
    issuer_name: Optional[str] = None
    recipient_name: Optional[str] = None
    issue_date: date
    due_date: Optional[date] = None
    total_ht: Decimal
    total_vat: Decimal
    total_ttc: Decimal
    currency: str
    ppf_status: Optional[str] = None
    lines: List[InvoiceLineResponse] = []
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class InvoiceListResponse(BaseModel):
    data: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
