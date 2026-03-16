"""
Pydantic schemas for the Tax Service API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class DeclarationType(str, Enum):
    CA3 = "CA3"
    CA12 = "CA12"
    IS = "IS"
    CVAE = "CVAE"
    CFE = "CFE"
    DAS2 = "DAS2"


class DeclarationStatus(str, Enum):
    DRAFT = "draft"
    COMPUTED = "computed"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CalendarStatus(str, Enum):
    UPCOMING = "upcoming"
    DUE = "due"
    OVERDUE = "overdue"
    COMPLETED = "completed"
    SKIPPED = "skipped"


# --- Request schemas ---

class ComputeDeclarationRequest(BaseModel):
    type: DeclarationType
    period_start: date
    period_end: date
    dossier_id: Optional[UUID] = None


# --- Response schemas ---

class CA3LineResponse(BaseModel):
    line_code: str
    label: str
    base: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")


class CA3ComputedResponse(BaseModel):
    period_start: date
    period_end: date
    collected_vat_20: Decimal = Decimal("0")
    collected_vat_10: Decimal = Decimal("0")
    collected_vat_55: Decimal = Decimal("0")
    collected_vat_21: Decimal = Decimal("0")
    total_collected: Decimal = Decimal("0")
    deductible_vat_goods: Decimal = Decimal("0")
    deductible_vat_services: Decimal = Decimal("0")
    deductible_vat_immobilisations: Decimal = Decimal("0")
    total_deductible: Decimal = Decimal("0")
    vat_due: Decimal = Decimal("0")
    credit_vat: Decimal = Decimal("0")
    net_amount: Decimal = Decimal("0")


class TaxDeclarationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    dossier_id: Optional[UUID] = None
    type: str
    period_start: date
    period_end: date
    due_date: Optional[date] = None
    status: str
    computed_data: Optional[dict] = None
    total_amount: Decimal
    edi_file_path: Optional[str] = None
    submitted_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaxDeclarationListResponse(BaseModel):
    data: List[TaxDeclarationResponse]
    total: int
    page: int
    page_size: int


class TaxCalendarResponse(BaseModel):
    id: UUID
    declaration_type: str
    due_date: date
    status: str
    declaration_id: Optional[UUID] = None
    reminder_sent: bool
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PenaltyWarning(BaseModel):
    declaration_type: str
    due_date: date
    days_overdue: int
    estimated_penalty: Decimal
    message: str
