"""
Banking Service - Business logic layer.
"""
import structlog
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID
from datetime import date, datetime

from .models import BankAccount, BankStatement, BankTransaction, ReconciliationRule

logger = structlog.get_logger()


class BankingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Bank Accounts ---

    async def list_accounts(self, tenant_id: UUID) -> list[BankAccount]:
        result = await self.db.execute(
            select(BankAccount).where(
                BankAccount.tenant_id == tenant_id,
            ).order_by(BankAccount.account_name)
        )
        return list(result.scalars().all())

    async def get_account(self, tenant_id: UUID, account_id: UUID) -> Optional[BankAccount]:
        result = await self.db.execute(
            select(BankAccount).where(
                BankAccount.id == account_id,
                BankAccount.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_account(self, tenant_id: UUID, **kwargs) -> BankAccount:
        account = BankAccount(tenant_id=tenant_id, **kwargs)
        self.db.add(account)
        await self.db.flush()
        return account

    async def update_account(self, tenant_id: UUID, account_id: UUID, **kwargs) -> Optional[BankAccount]:
        account = await self.get_account(tenant_id, account_id)
        if not account:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(account, key):
                setattr(account, key, value)
        account.updated_at = datetime.utcnow()
        await self.db.flush()
        return account

    # --- Transactions ---

    async def list_transactions(
        self,
        bank_account_id: UUID,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> tuple[list[BankTransaction], int]:
        query = select(BankTransaction).where(
            BankTransaction.bank_account_id == bank_account_id
        )
        count_query = select(func.count(BankTransaction.id)).where(
            BankTransaction.bank_account_id == bank_account_id
        )

        if status:
            query = query.where(BankTransaction.reconciliation_status == status)
            count_query = count_query.where(BankTransaction.reconciliation_status == status)
        if start_date:
            query = query.where(BankTransaction.transaction_date >= start_date)
            count_query = count_query.where(BankTransaction.transaction_date >= start_date)
        if end_date:
            query = query.where(BankTransaction.transaction_date <= end_date)
            count_query = count_query.where(BankTransaction.transaction_date <= end_date)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(BankTransaction.transaction_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def create_transaction(self, **kwargs) -> BankTransaction:
        txn = BankTransaction(**kwargs)
        self.db.add(txn)
        await self.db.flush()
        return txn

    async def match_transaction(
        self, transaction_id: UUID, entry_id: UUID
    ) -> Optional[BankTransaction]:
        result = await self.db.execute(
            select(BankTransaction).where(BankTransaction.id == transaction_id)
        )
        txn = result.scalar_one_or_none()
        if not txn:
            return None

        txn.reconciliation_status = "matched"
        txn.matched_entry_id = entry_id
        txn.match_confidence = Decimal("1.0")
        txn.matched_by = "manual"
        txn.matched_at = datetime.utcnow()
        await self.db.flush()
        return txn

    async def unmatch_transaction(self, transaction_id: UUID) -> Optional[BankTransaction]:
        result = await self.db.execute(
            select(BankTransaction).where(BankTransaction.id == transaction_id)
        )
        txn = result.scalar_one_or_none()
        if not txn:
            return None

        txn.reconciliation_status = "unmatched"
        txn.matched_entry_id = None
        txn.match_confidence = None
        txn.matched_by = None
        txn.matched_at = None
        await self.db.flush()
        return txn

    # --- Statements ---

    async def list_statements(self, bank_account_id: UUID) -> list[BankStatement]:
        result = await self.db.execute(
            select(BankStatement).where(
                BankStatement.bank_account_id == bank_account_id,
            ).order_by(BankStatement.statement_date.desc())
        )
        return list(result.scalars().all())

    async def create_statement(self, **kwargs) -> BankStatement:
        stmt = BankStatement(**kwargs)
        self.db.add(stmt)
        await self.db.flush()
        return stmt

    # --- Reconciliation summary ---

    async def get_reconciliation_summary(self, bank_account_id: UUID) -> dict:
        result = await self.db.execute(
            select(
                BankTransaction.reconciliation_status,
                func.count(BankTransaction.id),
            ).where(
                BankTransaction.bank_account_id == bank_account_id,
            ).group_by(BankTransaction.reconciliation_status)
        )
        stats = {row[0]: row[1] for row in result.all()}
        total = sum(stats.values())
        matched = stats.get("matched", 0)
        return {
            "total_transactions": total,
            "matched": matched,
            "unmatched": stats.get("unmatched", 0),
            "ignored": stats.get("ignored", 0),
            "match_rate": round(matched / total * 100, 1) if total > 0 else 0,
        }

    # --- Rules ---

    async def list_rules(self, tenant_id: UUID) -> list[ReconciliationRule]:
        result = await self.db.execute(
            select(ReconciliationRule).where(
                ReconciliationRule.tenant_id == tenant_id,
            ).order_by(ReconciliationRule.priority)
        )
        return list(result.scalars().all())

    async def create_rule(self, tenant_id: UUID, user_id: UUID, **kwargs) -> ReconciliationRule:
        rule = ReconciliationRule(tenant_id=tenant_id, created_by=user_id, **kwargs)
        self.db.add(rule)
        await self.db.flush()
        return rule
