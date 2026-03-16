"""
FEC (Fichier des Ecritures Comptables) Exporter.
Generates FEC files per Article A47 A-1 of the Livre des procedures fiscales.
"""
import csv
import io
import structlog
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from .models import JournalEntry, JournalEntryLine
from .config import FEC_COLUMNS, JOURNAL_CODES

logger = structlog.get_logger()


def format_fec_date(d: date) -> str:
    """Format date as YYYYMMDD per FEC spec."""
    return d.strftime("%Y%m%d")


def format_fec_amount(amount) -> str:
    """Format amount with comma as decimal separator (French format)."""
    if amount is None or amount == 0:
        return "0,00"
    return f"{float(amount):.2f}".replace(".", ",")


async def export_fec(
    db: AsyncSession,
    tenant_id: UUID,
    fiscal_year: int,
    siren: str,
) -> str:
    """
    Export FEC file for a fiscal year.
    Returns CSV content as string (tab-separated, UTF-8).

    Filename convention: {SIREN}FEC{YYYYMMDD}.txt
    where YYYYMMDD is the closing date of the fiscal year.
    """
    # Fetch all validated/posted entries for the fiscal year
    result = await db.execute(
        select(JournalEntry).where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntry.fiscal_year == fiscal_year,
            JournalEntry.status.in_(["validated", "posted"]),
        ).order_by(JournalEntry.entry_date, JournalEntry.entry_number)
    )
    entries = list(result.scalars().all())

    # Build FEC content
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t', quoting=csv.QUOTE_MINIMAL)

    # Header row
    writer.writerow(FEC_COLUMNS)

    for entry in entries:
        # Load lines
        lines_result = await db.execute(
            select(JournalEntryLine).where(
                JournalEntryLine.entry_id == entry.id,
            ).order_by(JournalEntryLine.line_number)
        )
        lines = list(lines_result.scalars().all())

        journal_lib = JOURNAL_CODES.get(entry.journal_code, entry.journal_code)

        for line in lines:
            row = [
                entry.journal_code,                          # JournalCode
                journal_lib,                                 # JournalLib
                entry.entry_number,                          # EcritureNum
                format_fec_date(entry.entry_date),          # EcritureDate
                line.account_code,                           # CompteNum
                line.account_name or "",                     # CompteLib
                "",                                          # CompAuxNum (auxiliary)
                "",                                          # CompAuxLib
                entry.entry_number,                          # PieceRef
                format_fec_date(entry.entry_date),          # PieceDate
                line.label or entry.description or "",       # EcritureLib
                format_fec_amount(line.debit),              # Debit
                format_fec_amount(line.credit),             # Credit
                line.lettering_code or "",                   # EcrtureLet
                format_fec_date(line.lettered_at.date()) if line.lettered_at else "",  # DateLet
                format_fec_date(entry.validated_at.date()) if entry.validated_at else "",  # ValidDate
                "",                                          # Montantdevise
                line.currency or "EUR",                      # Idevise
            ]
            writer.writerow(row)

    content = output.getvalue()
    logger.info("fec_exported", fiscal_year=fiscal_year, entries=len(entries))
    return content


def get_fec_filename(siren: str, fiscal_year: int) -> str:
    """Generate FEC filename per legal convention."""
    closing_date = date(fiscal_year, 12, 31)
    return f"{siren}FEC{format_fec_date(closing_date)}.txt"
