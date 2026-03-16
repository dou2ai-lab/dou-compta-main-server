"""Pydantic schemas for Payroll Service."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

class PayslipData(BaseModel):
    employee_name: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    gross_salary: Decimal = Decimal("0")
    net_salary: Decimal = Decimal("0")
    employer_charges: Decimal = Decimal("0")
    employee_charges: Decimal = Decimal("0")
    urssaf: Decimal = Decimal("0")
    retirement: Decimal = Decimal("0")
    csg_crds: Decimal = Decimal("0")

class PayslipResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    employee_name: Optional[str] = None
    period: Optional[str] = None
    gross_salary: Decimal
    net_salary: Decimal
    total_charges: Decimal
    status: str
    entry_id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ChargeAllocation(BaseModel):
    account_code: str
    account_name: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
