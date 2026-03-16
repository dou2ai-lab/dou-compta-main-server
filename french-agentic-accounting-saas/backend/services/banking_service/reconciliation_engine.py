"""
BANKA Agent - Reconciliation Engine.
Multi-pass matching of bank transactions to journal entries.
Pass 1: Exact match (reference + amount)
Pass 2: Fuzzy match (amount + date window + label similarity)
Pass 3: Rule-based matching
"""
import structlog
from decimal import Decimal
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional

from common.agent_base import AgentBase, AgentResult, AgentStatus
from .models import BankTransaction, BankAccount, ReconciliationRule
from services.accounting_service.models import JournalEntry, JournalEntryLine

logger = structlog.get_logger()


def label_similarity(a: str, b: str) -> float:
    """Simple token-based similarity between two labels."""
    if not a or not b:
        return 0.0
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


async def reconcile_pass1_exact(
    db: AsyncSession,
    tenant_id: UUID,
    bank_account_id: UUID,
) -> int:
    """Pass 1: Match by exact reference + amount."""
    matched = 0

    # Get unmatched transactions
    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.bank_account_id == bank_account_id,
            BankTransaction.reconciliation_status == "unmatched",
            BankTransaction.reference.isnot(None),
        )
    )
    transactions = list(result.scalars().all())

    for txn in transactions:
        # Look for journal entry with matching reference and amount
        entry_result = await db.execute(
            select(JournalEntry).where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.journal_code == "BNQ",
                JournalEntry.entry_number.contains(txn.reference) if txn.reference else False,
            )
        )
        entry = entry_result.scalar_one_or_none()

        if entry:
            # Verify amount match
            entry_amount = entry.total_debit if txn.amount < 0 else entry.total_credit
            if abs(abs(txn.amount) - entry_amount) < Decimal("0.01"):
                txn.reconciliation_status = "matched"
                txn.matched_entry_id = entry.id
                txn.match_confidence = Decimal("1.0")
                txn.matched_by = "auto"
                from datetime import datetime
                txn.matched_at = datetime.utcnow()
                matched += 1

    if matched > 0:
        await db.flush()
        logger.info("reconcile_pass1", matched=matched)

    return matched


async def reconcile_pass2_fuzzy(
    db: AsyncSession,
    tenant_id: UUID,
    bank_account_id: UUID,
    date_window_days: int = 5,
    min_label_similarity: float = 0.3,
) -> int:
    """Pass 2: Match by amount + date proximity + label similarity."""
    matched = 0

    result = await db.execute(
        select(BankTransaction).where(
            BankTransaction.bank_account_id == bank_account_id,
            BankTransaction.reconciliation_status == "unmatched",
        )
    )
    transactions = list(result.scalars().all())

    for txn in transactions:
        abs_amount = abs(txn.amount)
        date_start = txn.transaction_date - timedelta(days=date_window_days)
        date_end = txn.transaction_date + timedelta(days=date_window_days)

        # Find candidate entries by amount and date range
        candidates = await db.execute(
            select(JournalEntry).where(
                JournalEntry.tenant_id == tenant_id,
                JournalEntry.status.in_(["validated", "posted"]),
                JournalEntry.entry_date.between(date_start, date_end),
            )
        )
        entries = list(candidates.scalars().all())

        best_match = None
        best_confidence = 0.0

        for entry in entries:
            # Check if already matched to another transaction
            existing = await db.execute(
                select(func.count(BankTransaction.id)).where(
                    BankTransaction.matched_entry_id == entry.id,
                    BankTransaction.reconciliation_status == "matched",
                )
            )
            if existing.scalar() > 0:
                continue

            # Amount match score
            entry_amount = max(entry.total_debit, entry.total_credit)
            if entry_amount == 0:
                continue
            amount_diff = abs(abs_amount - entry_amount) / entry_amount
            if amount_diff > Decimal("0.01"):  # >1% difference
                continue
            amount_score = float(1.0 - amount_diff)

            # Date proximity score
            date_diff = abs((txn.transaction_date - entry.entry_date).days)
            date_score = max(0, 1.0 - (date_diff / date_window_days))

            # Label similarity score
            sim_score = label_similarity(txn.label, entry.description or "")

            # Combined confidence
            confidence = (amount_score * 0.5) + (date_score * 0.3) + (sim_score * 0.2)

            if confidence > best_confidence and confidence >= 0.6:
                best_confidence = confidence
                best_match = entry

        if best_match:
            txn.reconciliation_status = "matched"
            txn.matched_entry_id = best_match.id
            txn.match_confidence = Decimal(str(round(best_confidence, 4)))
            txn.matched_by = "auto"
            from datetime import datetime
            txn.matched_at = datetime.utcnow()
            matched += 1

    if matched > 0:
        await db.flush()
        logger.info("reconcile_pass2", matched=matched)

    return matched


async def reconcile_all(
    db: AsyncSession,
    tenant_id: UUID,
    bank_account_id: UUID,
) -> dict:
    """Run all reconciliation passes."""
    pass1 = await reconcile_pass1_exact(db, tenant_id, bank_account_id)
    pass2 = await reconcile_pass2_fuzzy(db, tenant_id, bank_account_id)

    # Count final stats
    result = await db.execute(
        select(
            BankTransaction.reconciliation_status,
            func.count(BankTransaction.id),
        ).where(
            BankTransaction.bank_account_id == bank_account_id,
        ).group_by(BankTransaction.reconciliation_status)
    )
    stats = {row[0]: row[1] for row in result.all()}

    return {
        "pass1_exact_matches": pass1,
        "pass2_fuzzy_matches": pass2,
        "total_matched": stats.get("matched", 0),
        "total_unmatched": stats.get("unmatched", 0),
        "total_ignored": stats.get("ignored", 0),
    }


class BANKAAgent(AgentBase):
    """BANKA - Intelligent Banking Reconciliation Agent."""

    agent_code = "BANKA"
    agent_name = "Agent Bancaire"

    async def run(self, context: dict, result: AgentResult) -> dict:
        db = context["db"]
        tenant_id = context["tenant_id"]
        bank_account_id = context["bank_account_id"]

        result.add_log(f"Starting reconciliation for account {bank_account_id}")
        stats = await reconcile_all(db, tenant_id, bank_account_id)

        total = stats["total_matched"] + stats["total_unmatched"]
        if total > 0:
            result.confidence = stats["total_matched"] / total
        else:
            result.confidence = 1.0

        result.add_log(f"Reconciliation complete: {stats['total_matched']} matched, {stats['total_unmatched']} unmatched")
        return stats

    async def validate(self, result: AgentResult) -> bool:
        return result.status == AgentStatus.SUCCESS
