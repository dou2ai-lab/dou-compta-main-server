"""Payroll Service API routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog
from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .schemas import PayslipData, ChargeAllocation
from .charge_allocator import allocate_charges

logger = structlog.get_logger()
router = APIRouter()

@router.post("/allocate-charges", response_model=list[ChargeAllocation])
async def compute_charge_allocation(
    payload: PayslipData,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute PCG account allocation from payslip data."""
    lines = allocate_charges(payload.model_dump())
    return [ChargeAllocation(**l) for l in lines]

@router.get("/accounts")
async def get_payroll_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get standard payroll PCG accounts."""
    from .charge_allocator import PAYROLL_ACCOUNTS
    return [{"code": k, "name": v} for k, v in PAYROLL_ACCOUNTS.items()]
