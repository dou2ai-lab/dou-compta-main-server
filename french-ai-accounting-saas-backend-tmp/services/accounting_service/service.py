"""
Accounting Service - Business logic layer.
"""
import structlog
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from uuid import UUID
from datetime import date

from .models import JournalEntry, JournalEntryLine, PCGAccount, ThirdParty, FiscalPeriod

logger = structlog.get_logger()


class AccountingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_entries(
        self,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        journal_code: Optional[str] = None,
        status: Optional[str] = None,
        fiscal_year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> tuple[list[JournalEntry], int]:
        """List journal entries with filters and pagination."""
        query = select(JournalEntry).where(JournalEntry.tenant_id == tenant_id)
        count_query = select(func.count(JournalEntry.id)).where(JournalEntry.tenant_id == tenant_id)

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

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_number)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        entries = list(result.scalars().all())

        # Load lines for each entry using set_committed_value to avoid lazy load trigger
        from sqlalchemy.orm.attributes import set_committed_value
        for entry in entries:
            lines_result = await self.db.execute(
                select(JournalEntryLine).where(
                    JournalEntryLine.entry_id == entry.id
                ).order_by(JournalEntryLine.line_number)
            )
            set_committed_value(entry, 'lines', list(lines_result.scalars().all()))

        return entries, total

    async def get_entry(self, tenant_id: UUID, entry_id: UUID) -> Optional[JournalEntry]:
        """Get a single journal entry with lines."""
        result = await self.db.execute(
            select(JournalEntry).where(
                JournalEntry.id == entry_id,
                JournalEntry.tenant_id == tenant_id,
            )
        )
        entry = result.scalar_one_or_none()
        if entry:
            from sqlalchemy.orm.attributes import set_committed_value
            lines_result = await self.db.execute(
                select(JournalEntryLine).where(
                    JournalEntryLine.entry_id == entry.id
                ).order_by(JournalEntryLine.line_number)
            )
            set_committed_value(entry, 'lines', list(lines_result.scalars().all()))
        return entry

    async def compute_trial_balance(
        self,
        tenant_id: UUID,
        fiscal_year: int,
        period_start: Optional[int] = None,
        period_end: Optional[int] = None,
    ) -> list[dict]:
        """Compute trial balance (balance des comptes) for a fiscal year."""
        query = (
            select(
                JournalEntryLine.account_code,
                JournalEntryLine.account_name,
                func.sum(JournalEntryLine.debit).label("total_debit"),
                func.sum(JournalEntryLine.credit).label("total_credit"),
            )
            .select_from(
                JournalEntryLine.__table__.join(
                    JournalEntry.__table__,
                    JournalEntryLine.entry_id == JournalEntry.id,
                )
            )
            .where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.fiscal_year == fiscal_year,
                JournalEntry.status.in_(["validated", "posted"]),
            )
            .group_by(JournalEntryLine.account_code, JournalEntryLine.account_name)
            .order_by(JournalEntryLine.account_code)
        )

        if period_start is not None:
            query = query.where(JournalEntry.fiscal_period >= period_start)
        if period_end is not None:
            query = query.where(JournalEntry.fiscal_period <= period_end)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "account_code": row.account_code,
                "account_name": row.account_name or "",
                "total_debit": row.total_debit or Decimal("0"),
                "total_credit": row.total_credit or Decimal("0"),
                "balance": (row.total_debit or Decimal("0")) - (row.total_credit or Decimal("0")),
            }
            for row in rows
        ]

    async def list_pcg_accounts(self, tenant_id: UUID) -> list[PCGAccount]:
        result = await self.db.execute(
            select(PCGAccount).where(
                PCGAccount.tenant_id == tenant_id,
                PCGAccount.is_active == True,
            ).order_by(PCGAccount.account_code)
        )
        return list(result.scalars().all())

    async def list_third_parties(self, tenant_id: UUID) -> list[ThirdParty]:
        result = await self.db.execute(
            select(ThirdParty).where(
                ThirdParty.tenant_id == tenant_id,
                ThirdParty.is_active == True,
            ).order_by(ThirdParty.name)
        )
        return list(result.scalars().all())

    async def create_third_party(self, tenant_id: UUID, **kwargs) -> ThirdParty:
        tp = ThirdParty(tenant_id=tenant_id, **kwargs)
        self.db.add(tp)
        await self.db.flush()
        return tp

    async def list_fiscal_periods(self, tenant_id: UUID, fiscal_year: Optional[int] = None) -> list[FiscalPeriod]:
        query = select(FiscalPeriod).where(FiscalPeriod.tenant_id == tenant_id)
        if fiscal_year:
            query = query.where(FiscalPeriod.fiscal_year == fiscal_year)
        query = query.order_by(FiscalPeriod.fiscal_year, FiscalPeriod.period_number)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def close_period(self, tenant_id: UUID, period_id: UUID, user_id: UUID) -> Optional[FiscalPeriod]:
        from datetime import datetime
        result = await self.db.execute(
            select(FiscalPeriod).where(
                FiscalPeriod.id == period_id,
                FiscalPeriod.tenant_id == tenant_id,
            )
        )
        period = result.scalar_one_or_none()
        if not period:
            return None
        period.status = "closed"
        period.closed_at = datetime.utcnow()
        period.closed_by = user_id
        await self.db.flush()
        return period
