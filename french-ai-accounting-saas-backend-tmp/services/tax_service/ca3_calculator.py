"""
CA3 Calculator - Monthly/Quarterly VAT Declaration.
Computes TVA collectee vs TVA deductible from journal entries to produce
the CA3 declaration (Cerfa 3310-CA3).
"""
import structlog
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from services.accounting_service.models import JournalEntry, JournalEntryLine

logger = structlog.get_logger()

# PCG accounts for VAT
TVA_COLLECTED_ACCOUNTS = {
    "445710": Decimal("20.0"),   # TVA collectee 20%
    "445711": Decimal("10.0"),   # TVA collectee 10%
    "445712": Decimal("5.5"),    # TVA collectee 5.5%
    "445713": Decimal("2.1"),    # TVA collectee 2.1%
}

TVA_DEDUCTIBLE_ACCOUNTS = {
    "445660": "goods_services",      # TVA deductible sur ABS
    "445620": "immobilisations",     # TVA deductible sur immobilisations
}

TVA_CREDIT_ACCOUNT = "445670"  # Credit de TVA


async def compute_ca3(
    db: AsyncSession,
    tenant_id: UUID,
    period_start: date,
    period_end: date,
) -> dict:
    """
    Compute CA3 VAT declaration from journal entries.

    CA3 = TVA collectee - TVA deductible
    If positive: VAT due (net a payer)
    If negative: VAT credit (credit de TVA)
    """
    # 1. Compute collected VAT (credit side of 4457xx accounts)
    collected = {}
    for account_code, rate in TVA_COLLECTED_ACCOUNTS.items():
        result = await db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.credit), 0)).select_from(
                JournalEntryLine.__table__.join(
                    JournalEntry.__table__,
                    JournalEntryLine.entry_id == JournalEntry.id,
                )
            ).where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.entry_date.between(period_start, period_end),
                JournalEntry.status.in_(["validated", "posted"]),
                JournalEntryLine.account_code == account_code,
            )
        )
        collected[account_code] = result.scalar() or Decimal("0")

    collected_20 = collected.get("445710", Decimal("0"))
    collected_10 = collected.get("445711", Decimal("0"))
    collected_55 = collected.get("445712", Decimal("0"))
    collected_21 = collected.get("445713", Decimal("0"))
    total_collected = collected_20 + collected_10 + collected_55 + collected_21

    # 2. Compute deductible VAT (debit side of 4456xx accounts)
    deductible_goods = Decimal("0")
    deductible_immo = Decimal("0")

    for account_code, category in TVA_DEDUCTIBLE_ACCOUNTS.items():
        result = await db.execute(
            select(func.coalesce(func.sum(JournalEntryLine.debit), 0)).select_from(
                JournalEntryLine.__table__.join(
                    JournalEntry.__table__,
                    JournalEntryLine.entry_id == JournalEntry.id,
                )
            ).where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.entry_date.between(period_start, period_end),
                JournalEntry.status.in_(["validated", "posted"]),
                JournalEntryLine.account_code == account_code,
            )
        )
        amount = result.scalar() or Decimal("0")
        if category == "immobilisations":
            deductible_immo = amount
        else:
            deductible_goods = amount

    total_deductible = deductible_goods + deductible_immo

    # 3. Compute net VAT
    net_amount = total_collected - total_deductible
    vat_due = max(net_amount, Decimal("0"))
    credit_vat = max(-net_amount, Decimal("0"))

    # 4. Compute tax bases (HT amounts for each rate)
    bases = {}
    for account_code, rate in TVA_COLLECTED_ACCOUNTS.items():
        if collected.get(account_code, Decimal("0")) > 0:
            base = (collected[account_code] * Decimal("100") / rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            bases[str(rate)] = base

    result = {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "collected_vat_20": str(collected_20),
        "collected_vat_10": str(collected_10),
        "collected_vat_55": str(collected_55),
        "collected_vat_21": str(collected_21),
        "total_collected": str(total_collected),
        "base_20": str(bases.get("20.0", Decimal("0"))),
        "base_10": str(bases.get("10.0", Decimal("0"))),
        "base_55": str(bases.get("5.5", Decimal("0"))),
        "base_21": str(bases.get("2.1", Decimal("0"))),
        "deductible_vat_goods": str(deductible_goods),
        "deductible_vat_services": str(deductible_goods),  # Same account for ABS
        "deductible_vat_immobilisations": str(deductible_immo),
        "total_deductible": str(total_deductible),
        "vat_due": str(vat_due),
        "credit_vat": str(credit_vat),
        "net_amount": str(net_amount),
    }

    logger.info(
        "ca3_computed",
        period=f"{period_start}/{period_end}",
        collected=str(total_collected),
        deductible=str(total_deductible),
        net=str(net_amount),
    )

    return result
