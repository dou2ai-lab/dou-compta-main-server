"""
Tax Service - Business logic layer.
"""
import structlog
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID
from datetime import date, datetime

from .models import TaxDeclaration, TaxCalendar
from .ca3_calculator import compute_ca3
from .penalty_detector import detect_overdue_declarations, check_upcoming_deadlines

logger = structlog.get_logger()


class TaxService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_declarations(
        self,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        type_filter: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[list[TaxDeclaration], int]:
        query = select(TaxDeclaration).where(TaxDeclaration.tenant_id == tenant_id)
        count_query = select(func.count(TaxDeclaration.id)).where(TaxDeclaration.tenant_id == tenant_id)

        if type_filter:
            query = query.where(TaxDeclaration.type == type_filter)
            count_query = count_query.where(TaxDeclaration.type == type_filter)
        if status:
            query = query.where(TaxDeclaration.status == status)
            count_query = count_query.where(TaxDeclaration.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(TaxDeclaration.period_end.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_declaration(self, tenant_id: UUID, declaration_id: UUID) -> Optional[TaxDeclaration]:
        result = await self.db.execute(
            select(TaxDeclaration).where(
                TaxDeclaration.id == declaration_id,
                TaxDeclaration.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def compute_declaration(
        self,
        tenant_id: UUID,
        declaration_type: str,
        period_start: date,
        period_end: date,
        dossier_id: Optional[UUID] = None,
    ) -> TaxDeclaration:
        """Compute a tax declaration from journal entries."""
        computed_data = {}
        total_amount = Decimal("0")

        if declaration_type == "CA3":
            computed_data = await compute_ca3(self.db, tenant_id, period_start, period_end)
            net = Decimal(computed_data.get("net_amount", "0"))
            total_amount = net

        # Determine due date (typically 15th-24th of month following period end)
        due_date = date(
            period_end.year if period_end.month < 12 else period_end.year + 1,
            period_end.month + 1 if period_end.month < 12 else 1,
            24,
        )

        declaration = TaxDeclaration(
            tenant_id=tenant_id,
            dossier_id=dossier_id,
            type=declaration_type,
            period_start=period_start,
            period_end=period_end,
            due_date=due_date,
            status="computed",
            computed_data=computed_data,
            total_amount=total_amount,
        )
        self.db.add(declaration)
        await self.db.flush()

        logger.info(
            "declaration_computed",
            type=declaration_type,
            period=f"{period_start}/{period_end}",
            amount=str(total_amount),
        )
        return declaration

    async def validate_declaration(
        self, tenant_id: UUID, declaration_id: UUID, user_id: UUID
    ) -> Optional[TaxDeclaration]:
        decl = await self.get_declaration(tenant_id, declaration_id)
        if not decl:
            return None
        decl.status = "validated"
        decl.validated_by = user_id
        decl.validated_at = datetime.utcnow()
        await self.db.flush()
        return decl

    async def get_calendar(
        self, tenant_id: UUID, year: Optional[int] = None
    ) -> list[TaxCalendar]:
        query = select(TaxCalendar).where(TaxCalendar.tenant_id == tenant_id)
        if year:
            start = date(year, 1, 1)
            end = date(year, 12, 31)
            query = query.where(TaxCalendar.due_date.between(start, end))
        query = query.order_by(TaxCalendar.due_date)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_penalties(self, tenant_id: UUID) -> list[dict]:
        return await detect_overdue_declarations(self.db, tenant_id)

    async def get_upcoming(self, tenant_id: UUID, days: int = 30) -> list[dict]:
        return await check_upcoming_deadlines(self.db, tenant_id, days)
