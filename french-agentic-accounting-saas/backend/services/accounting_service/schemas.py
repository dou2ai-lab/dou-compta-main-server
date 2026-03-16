"""
Pydantic schemas for the Accounting Service API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class JournalCode(str, Enum):
    ACH = "ACH"
    VTE = "VTE"
    BNQ = "BNQ"
    OD = "OD"
    SAL = "SAL"
    AN = "AN"


class EntryStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    POSTED = "posted"


class PeriodStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    LOCKED = "locked"


class ThirdPartyType(str, Enum):
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    EMPLOYEE = "employee"


# --- Request schemas ---

class JournalEntryLineCreate(BaseModel):
    account_code: str = Field(..., max_length=10)
    account_name: Optional[str] = None
    debit: Decimal = Field(default=Decimal("0"), ge=0)
    credit: Decimal = Field(default=Decimal("0"), ge=0)
    label: Optional[str] = None
    vat_rate: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    third_party_id: Optional[UUID] = None


class JournalEntryCreate(BaseModel):
    journal_code: JournalCode
    entry_date: date
    description: Optional[str] = None
    lines: List[JournalEntryLineCreate] = Field(..., min_length=2)


class GenerateFromExpenseRequest(BaseModel):
    expense_id: UUID


class ThirdPartyCreate(BaseModel):
    type: ThirdPartyType
    name: str = Field(..., max_length=255)
    siren: Optional[str] = Field(None, max_length=9)
    siret: Optional[str] = Field(None, max_length=14)
    vat_number: Optional[str] = Field(None, max_length=20)
    default_account_code: Optional[str] = Field(None, max_length=10)


class FiscalPeriodCreate(BaseModel):
    fiscal_year: int
    period_number: int = Field(..., ge=0, le=13)
    start_date: date
    end_date: date


class FECExportRequest(BaseModel):
    fiscal_year: int
    siren: str = Field(..., max_length=9)


# --- Response schemas ---

class JournalEntryLineResponse(BaseModel):
    id: UUID
    line_number: int
    account_code: str
    account_name: Optional[str] = None
    debit: Decimal
    credit: Decimal
    label: Optional[str] = None
    vat_rate: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    third_party_id: Optional[UUID] = None
    lettering_code: Optional[str] = None

    class Config:
        from_attributes = True


class JournalEntryResponse(BaseModel):
    id: UUID
    entry_number: str
    journal_code: str
    entry_date: date
    description: Optional[str] = None
    status: str
    source_type: Optional[str] = None
    source_id: Optional[UUID] = None
    fiscal_year: int
    fiscal_period: int
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    lines: List[JournalEntryLineResponse] = []
    created_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JournalEntryListResponse(BaseModel):
    data: List[JournalEntryResponse]
    total: int
    page: int
    page_size: int


class ThirdPartyResponse(BaseModel):
    id: UUID
    type: str
    name: str
    siren: Optional[str] = None
    siret: Optional[str] = None
    vat_number: Optional[str] = None
    default_account_code: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PCGAccountResponse(BaseModel):
    id: UUID
    account_code: str
    account_name: str
    account_class: int
    account_type: str
    parent_code: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class FiscalPeriodResponse(BaseModel):
    id: UUID
    fiscal_year: int
    period_number: int
    start_date: date
    end_date: date
    status: str
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrialBalanceLineResponse(BaseModel):
    account_code: str
    account_name: str
    total_debit: Decimal
    total_credit: Decimal
    balance: Decimal


class TrialBalanceResponse(BaseModel):
    fiscal_year: int
    period_start: Optional[int] = None
    period_end: Optional[int] = None
    lines: List[TrialBalanceLineResponse]
    total_debit: Decimal
    total_credit: Decimal
