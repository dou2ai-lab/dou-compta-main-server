"""
Accounting Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from datetime import date
import structlog

from common.database import get_db
from common.models import User, Expense
from services.auth.dependencies import get_current_user
from .service import AccountingService
from .entry_generator import generate_expense_entry
from .validation_service import validate_and_post_entry
from .lettering_service import auto_letter_lines
from .fec_exporter import export_fec, get_fec_filename
from .pcg_seed import seed_pcg_accounts
from .schemas import (
    JournalEntryResponse, JournalEntryListResponse, JournalEntryLineResponse,
    ThirdPartyCreate, ThirdPartyResponse, PCGAccountResponse,
    FiscalPeriodCreate, FiscalPeriodResponse,
    TrialBalanceResponse, TrialBalanceLineResponse,
    GenerateFromExpenseRequest,
)
from .models import FiscalPeriod

logger = structlog.get_logger()
router = APIRouter()


def entry_to_response(entry) -> JournalEntryResponse:
    """Convert ORM entry to response schema."""
    return JournalEntryResponse(
        id=entry.id,
        entry_number=entry.entry_number,
        journal_code=entry.journal_code,
        entry_date=entry.entry_date,
        description=entry.description,
        status=entry.status,
        source_type=entry.source_type,
        source_id=entry.source_id,
        fiscal_year=entry.fiscal_year,
        fiscal_period=entry.fiscal_period,
        total_debit=entry.total_debit,
        total_credit=entry.total_credit,
        is_balanced=entry.is_balanced,
        lines=[
            JournalEntryLineResponse(
                id=line.id,
                line_number=line.line_number,
                account_code=line.account_code,
                account_name=line.account_name,
                debit=line.debit,
                credit=line.credit,
                label=line.label,
                vat_rate=line.vat_rate,
                vat_amount=line.vat_amount,
                third_party_id=line.third_party_id,
                lettering_code=line.lettering_code,
            )
            for line in (entry.lines or [])
        ],
        created_at=entry.created_at,
        validated_at=entry.validated_at,
    )


# --- Static routes MUST come before dynamic /{entry_id} ---

@router.get("", response_model=JournalEntryListResponse)
async def list_entries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    journal_code: Optional[str] = None,
    status: Optional[str] = None,
    fiscal_year: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select, func
    from .models import JournalEntry, JournalEntryLine
    from sqlalchemy.orm.attributes import set_committed_value

    # Build query
    query = select(JournalEntry).where(JournalEntry.tenant_id == current_user.tenant_id)
    count_query = select(func.count(JournalEntry.id)).where(JournalEntry.tenant_id == current_user.tenant_id)

    if journal_code:
        query = query.where(JournalEntry.journal_code == journal_code)
        count_query = count_query.where(JournalEntry.journal_code == journal_code)
    if status:
        query = query.where(JournalEntry.status == status)
        count_query = count_query.where(JournalEntry.status == status)
    if fiscal_year:
        query = query.where(JournalEntry.fiscal_year == fiscal_year)
        count_query = count_query.where(JournalEntry.fiscal_year == fiscal_year)
    if start_date:
        query = query.where(JournalEntry.entry_date >= start_date)
        count_query = count_query.where(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.where(JournalEntry.entry_date <= end_date)
        count_query = count_query.where(JournalEntry.entry_date <= end_date)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_number)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    entries = list(result.scalars().all())

    # Load lines using set_committed_value to avoid lazy load trigger
    for entry in entries:
        lines_result = await db.execute(
            select(JournalEntryLine).where(
                JournalEntryLine.entry_id == entry.id
            ).order_by(JournalEntryLine.line_number)
        )
        set_committed_value(entry, 'lines', list(lines_result.scalars().all()))

    return JournalEntryListResponse(
        data=[entry_to_response(e) for e in entries],
        total=total, page=page, page_size=page_size,
    )


@router.post("/generate", response_model=JournalEntryResponse)
async def generate_entry_from_expense(
    request: GenerateFromExpenseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a journal entry from an approved expense."""
    from sqlalchemy import select as sa_select
    result = await db.execute(
        sa_select(Expense).where(
            Expense.id == request.expense_id,
            Expense.tenant_id == current_user.tenant_id,
        )
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Depense non trouvee")

    entry = await generate_expense_entry(
        db=db,
        tenant_id=current_user.tenant_id,
        expense_id=expense.id,
        amount=expense.amount,
        category=expense.category or "",
        description=expense.description or "",
        expense_date=expense.expense_date,
        vat_rate=expense.vat_rate,
        vat_amount=expense.vat_amount,
        merchant_name=expense.merchant_name,
        created_by=current_user.id,
    )
    await db.commit()
    return entry_to_response(entry)


@router.get("/journal/{journal_code}")
async def get_journal(
    journal_code: str,
    fiscal_year: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get entries for a specific journal."""
    svc = AccountingService(db)
    entries, total = await svc.list_entries(
        tenant_id=current_user.tenant_id,
        page=page, page_size=page_size,
        journal_code=journal_code,
        fiscal_year=fiscal_year,
    )
    return {
        "data": [entry_to_response(e) for e in entries],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def get_trial_balance(
    fiscal_year: int = Query(...),
    period_start: Optional[int] = None,
    period_end: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get trial balance (balance des comptes)."""
    svc = AccountingService(db)
    rows = await svc.compute_trial_balance(
        current_user.tenant_id, fiscal_year, period_start, period_end
    )
    lines = [TrialBalanceLineResponse(**r) for r in rows]
    total_debit = sum(l.total_debit for l in lines)
    total_credit = sum(l.total_credit for l in lines)
    return TrialBalanceResponse(
        fiscal_year=fiscal_year,
        period_start=period_start,
        period_end=period_end,
        lines=lines,
        total_debit=total_debit,
        total_credit=total_credit,
    )


@router.get("/fec/export")
async def export_fec_file(
    fiscal_year: int = Query(...),
    siren: str = Query(..., max_length=9),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export FEC file for tax authorities."""
    content = await export_fec(db, current_user.tenant_id, fiscal_year, siren)
    filename = get_fec_filename(siren, fiscal_year)
    return Response(
        content=content,
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/letter/{account_code}")
async def auto_letter(
    account_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Auto-letter matching lines for an account."""
    count = await auto_letter_lines(db, current_user.tenant_id, account_code)
    await db.commit()
    return {"lettered_count": count}


# --- PCG Accounts ---

@router.get("/pcg-accounts", response_model=list[PCGAccountResponse])
async def list_pcg_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AccountingService(db)
    accounts = await svc.list_pcg_accounts(current_user.tenant_id)
    return [PCGAccountResponse(
        id=a.id, account_code=a.account_code, account_name=a.account_name,
        account_class=a.account_class, account_type=a.account_type,
        parent_code=a.parent_code, is_active=a.is_active,
    ) for a in accounts]


@router.post("/pcg-accounts/seed")
async def seed_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Seed PCG 2025 standard accounts for the tenant."""
    count = await seed_pcg_accounts(db, current_user.tenant_id)
    await db.commit()
    return {"seeded": count}


# --- Third Parties ---

@router.get("/third-parties", response_model=list[ThirdPartyResponse])
async def list_third_parties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AccountingService(db)
    parties = await svc.list_third_parties(current_user.tenant_id)
    return [ThirdPartyResponse(
        id=p.id, type=p.type, name=p.name, siren=p.siren,
        siret=p.siret, vat_number=p.vat_number,
        default_account_code=p.default_account_code,
        is_active=p.is_active, created_at=p.created_at,
    ) for p in parties]


@router.post("/third-parties", response_model=ThirdPartyResponse)
async def create_third_party(
    payload: ThirdPartyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AccountingService(db)
    tp = await svc.create_third_party(
        tenant_id=current_user.tenant_id,
        **payload.model_dump(),
    )
    await db.commit()
    return ThirdPartyResponse(
        id=tp.id, type=tp.type, name=tp.name, siren=tp.siren,
        siret=tp.siret, vat_number=tp.vat_number,
        default_account_code=tp.default_account_code,
        is_active=tp.is_active, created_at=tp.created_at,
    )


# --- Fiscal Periods ---

@router.get("/periods", response_model=list[FiscalPeriodResponse])
async def list_periods(
    fiscal_year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AccountingService(db)
    periods = await svc.list_fiscal_periods(current_user.tenant_id, fiscal_year)
    return [FiscalPeriodResponse(
        id=p.id, fiscal_year=p.fiscal_year, period_number=p.period_number,
        start_date=p.start_date, end_date=p.end_date, status=p.status,
        closed_at=p.closed_at,
    ) for p in periods]


@router.post("/periods", response_model=FiscalPeriodResponse)
async def create_period(
    payload: FiscalPeriodCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    period = FiscalPeriod(
        tenant_id=current_user.tenant_id,
        fiscal_year=payload.fiscal_year,
        period_number=payload.period_number,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(period)
    await db.commit()
    return FiscalPeriodResponse(
        id=period.id, fiscal_year=period.fiscal_year,
        period_number=period.period_number,
        start_date=period.start_date, end_date=period.end_date,
        status=period.status, closed_at=period.closed_at,
    )


@router.post("/periods/{period_id}/close")
async def close_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Close a fiscal period."""
    svc = AccountingService(db)
    period = await svc.close_period(current_user.tenant_id, period_id, current_user.id)
    if not period:
        raise HTTPException(status_code=404, detail="Periode non trouvee")
    await db.commit()
    return FiscalPeriodResponse(
        id=period.id,
        fiscal_year=period.fiscal_year,
        period_number=period.period_number,
        start_date=period.start_date,
        end_date=period.end_date,
        status=period.status,
        closed_at=period.closed_at,
    )


# --- Dynamic entry routes MUST come LAST ---

@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AccountingService(db)
    entry = await svc.get_entry(current_user.tenant_id, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Ecriture non trouvee")
    return entry_to_response(entry)


@router.post("/{entry_id}/validate")
async def validate_entry(
    entry_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate a journal entry (checks balance, PCG accounts, period)."""
    success, messages = await validate_and_post_entry(db, entry_id, current_user.id)
    if success:
        await db.commit()
    return {"success": success, "messages": messages}
