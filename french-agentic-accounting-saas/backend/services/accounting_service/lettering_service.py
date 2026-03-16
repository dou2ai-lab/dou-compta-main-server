"""
Lettering service: matches journal entry lines for reconciliation.
Lettering assigns a code (AA, AB, AC...) to matching debit/credit lines
for the same third party and amount.
"""
import structlog
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import datetime

from .models import JournalEntryLine

logger = structlog.get_logger()


def generate_lettering_code(index: int) -> str:
    """Generate lettering codes: AA, AB, AC, ..., AZ, BA, BB, ..."""
    first = chr(ord('A') + (index // 26))
    second = chr(ord('A') + (index % 26))
    return f"{first}{second}"


async def get_next_lettering_index(db: AsyncSession, tenant_id: UUID) -> int:
    """Get the next available lettering index for a tenant."""
    from .models import JournalEntry

    result = await db.execute(
        select(func.count(func.distinct(JournalEntryLine.lettering_code))).select_from(
            JournalEntryLine.__table__.join(
                JournalEntry.__table__,
                JournalEntryLine.entry_id == JournalEntry.id,
            )
        ).where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntryLine.lettering_code.isnot(None),
        )
    )
    return result.scalar() or 0


async def auto_letter_lines(
    db: AsyncSession, tenant_id: UUID, account_code: str
) -> int:
    """
    Auto-letter matching debit/credit lines for a given account.
    Matches lines with the same third_party_id where debit == credit.
    Returns number of lines lettered.
    """
    from .models import JournalEntry

    # Get unlettered lines for this account
    result = await db.execute(
        select(JournalEntryLine).select_from(
            JournalEntryLine.__table__.join(
                JournalEntry.__table__,
                JournalEntryLine.entry_id == JournalEntry.id,
            )
        ).where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntryLine.account_code == account_code,
            JournalEntryLine.lettering_code.is_(None),
        ).order_by(JournalEntryLine.created_at)
    )
    lines = list(result.scalars().all())

    if len(lines) < 2:
        return 0

    lettering_index = await get_next_lettering_index(db, tenant_id)
    lettered_count = 0
    used = set()

    # Match debit lines with credit lines of same amount
    debit_lines = [l for l in lines if (l.debit or Decimal("0")) > 0]
    credit_lines = [l for l in lines if (l.credit or Decimal("0")) > 0]

    for dl in debit_lines:
        if dl.id in used:
            continue
        for cl in credit_lines:
            if cl.id in used:
                continue
            if dl.debit == cl.credit and dl.third_party_id == cl.third_party_id:
                code = generate_lettering_code(lettering_index)
                dl.lettering_code = code
                dl.lettered_at = datetime.utcnow()
                cl.lettering_code = code
                cl.lettered_at = datetime.utcnow()
                used.add(dl.id)
                used.add(cl.id)
                lettering_index += 1
                lettered_count += 2
                break

    if lettered_count > 0:
        await db.flush()
        logger.info("auto_lettering_complete", account=account_code, count=lettered_count)

    return lettered_count
