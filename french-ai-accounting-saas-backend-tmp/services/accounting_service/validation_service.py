"""
Validation service for journal entries.
Ensures PCG compliance and accounting integrity.
"""
import structlog
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime

from .models import JournalEntry, JournalEntryLine, PCGAccount, FiscalPeriod

logger = structlog.get_logger()


class ValidationError:
    def __init__(self, field: str, message: str, severity: str = "error"):
        self.field = field
        self.message = message
        self.severity = severity

    def to_dict(self):
        return {"field": self.field, "message": self.message, "severity": self.severity}


async def validate_entry(db: AsyncSession, entry: JournalEntry) -> list[ValidationError]:
    """Validate a journal entry for PCG compliance."""
    errors = []

    # 1. Check debit == credit
    total_debit = sum(line.debit or Decimal("0") for line in entry.lines)
    total_credit = sum(line.credit or Decimal("0") for line in entry.lines)

    if total_debit != total_credit:
        errors.append(ValidationError(
            "balance",
            f"L'ecriture n'est pas equilibree: debit={total_debit}, credit={total_credit}",
        ))

    # 2. Check minimum 2 lines
    if len(entry.lines) < 2:
        errors.append(ValidationError(
            "lines",
            "Une ecriture comptable doit avoir au moins 2 lignes",
        ))

    # 3. Check each line has either debit or credit (not both)
    for line in entry.lines:
        debit = line.debit or Decimal("0")
        credit = line.credit or Decimal("0")
        if debit > 0 and credit > 0:
            errors.append(ValidationError(
                f"line_{line.line_number}",
                f"Ligne {line.line_number}: une ligne ne peut avoir a la fois un debit et un credit",
            ))
        if debit == 0 and credit == 0:
            errors.append(ValidationError(
                f"line_{line.line_number}",
                f"Ligne {line.line_number}: une ligne doit avoir un debit ou un credit",
            ))

    # 4. Check PCG account codes exist
    for line in entry.lines:
        result = await db.execute(
            select(PCGAccount).where(
                PCGAccount.tenant_id == entry.tenant_id,
                PCGAccount.account_code == line.account_code,
                PCGAccount.is_active == True,
            )
        )
        if not result.scalar_one_or_none():
            errors.append(ValidationError(
                f"line_{line.line_number}.account_code",
                f"Compte PCG {line.account_code} non trouve ou inactif",
                severity="warning",
            ))

    # 5. Check fiscal period is open
    result = await db.execute(
        select(FiscalPeriod).where(
            FiscalPeriod.tenant_id == entry.tenant_id,
            FiscalPeriod.fiscal_year == entry.fiscal_year,
            FiscalPeriod.period_number == entry.fiscal_period,
        )
    )
    period = result.scalar_one_or_none()
    if period and period.status != "open":
        errors.append(ValidationError(
            "fiscal_period",
            f"La periode comptable {entry.fiscal_year}/{entry.fiscal_period} est {period.status}",
        ))

    return errors


async def validate_and_post_entry(
    db: AsyncSession, entry_id: UUID, user_id: UUID
) -> tuple[bool, list[dict]]:
    """Validate and change status to 'validated'."""
    result = await db.execute(
        select(JournalEntry).where(JournalEntry.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return False, [{"field": "entry", "message": "Ecriture non trouvee", "severity": "error"}]

    # Eagerly load lines
    lines_result = await db.execute(
        select(JournalEntryLine).where(JournalEntryLine.entry_id == entry_id)
    )
    from sqlalchemy.orm.attributes import set_committed_value
    set_committed_value(entry, 'lines', list(lines_result.scalars().all()))

    errors = await validate_entry(db, entry)
    blocking_errors = [e for e in errors if e.severity == "error"]

    if blocking_errors:
        return False, [e.to_dict() for e in errors]

    entry.status = "validated"
    entry.validated_by = user_id
    entry.validated_at = datetime.utcnow()
    await db.flush()

    return True, [e.to_dict() for e in errors]
