"""
Pydantic schemas for the Banking Service API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from enum import Enum


class ConnectionType(str, Enum):
    API = "api"
    MANUAL = "manual"
    IMPORT = "import"


class ReconciliationStatus(str, Enum):
    UNMATCHED = "unmatched"
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    IGNORED = "ignored"


# --- Request schemas ---

class BankAccountCreate(BaseModel):
    account_name: str = Field(..., max_length=255)
    iban: Optional[str] = Field(None, max_length=34)
    bic: Optional[str] = Field(None, max_length=11)
    bank_name: Optional[str] = None
    currency: str = "EUR"
    pcg_account_code: str = "512000"
    connection_type: str = "manual"


class BankAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None
    balance: Optional[Decimal] = None
    balance_date: Optional[date] = None
    pcg_account_code: Optional[str] = None
    is_active: Optional[bool] = None


class ManualTransactionCreate(BaseModel):
    transaction_date: date
    value_date: Optional[date] = None
    amount: Decimal
    label: str
    reference: Optional[str] = None
    counterparty_name: Optional[str] = None
    transaction_type: Optional[str] = None
    category: Optional[str] = None


class MatchTransactionRequest(BaseModel):
    entry_id: UUID


class ReconciliationRuleCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    match_criteria: dict = {}
    target_account_code: Optional[str] = None
    target_journal_code: str = "BNQ"
    auto_apply: bool = False
    priority: int = 100


# --- Response schemas ---

class BankAccountResponse(BaseModel):
    id: UUID
    account_name: str
    iban: Optional[str] = None
    bic: Optional[str] = None
    bank_name: Optional[str] = None
    currency: str
    balance: Decimal
    balance_date: Optional[date] = None
    pcg_account_code: str
    connection_type: str
    is_active: bool
    last_sync_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankAccountListResponse(BaseModel):
    data: List[BankAccountResponse]
    total: int


class BankStatementResponse(BaseModel):
    id: UUID
    bank_account_id: UUID
    statement_date: date
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    opening_balance: Optional[Decimal] = None
    closing_balance: Optional[Decimal] = None
    transaction_count: int
    file_format: Optional[str] = None
    import_status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankTransactionResponse(BaseModel):
    id: UUID
    bank_account_id: UUID
    transaction_date: date
    value_date: Optional[date] = None
    amount: Decimal
    currency: str
    label: str
    reference: Optional[str] = None
    counterparty_name: Optional[str] = None
    transaction_type: Optional[str] = None
    category: Optional[str] = None
    reconciliation_status: str
    matched_entry_id: Optional[UUID] = None
    match_confidence: Optional[Decimal] = None
    matched_at: Optional[datetime] = None
    matched_by: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankTransactionListResponse(BaseModel):
    data: List[BankTransactionResponse]
    total: int
    page: int
    page_size: int


class ReconciliationRuleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    match_criteria: dict
    target_account_code: Optional[str] = None
    target_journal_code: str
    auto_apply: bool
    priority: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReconciliationSummary(BaseModel):
    total_transactions: int
    matched: int
    unmatched: int
    ignored: int
    match_rate: float
