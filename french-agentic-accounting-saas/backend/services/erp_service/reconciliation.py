# -----------------------------------------------------------------------------
# File: reconciliation.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Card payment reconciliation
# -----------------------------------------------------------------------------

"""
Card Payment Reconciliation
Reconciles card payments with receipts and expenses
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from datetime import datetime, timedelta
from decimal import Decimal
import structlog
from difflib import SequenceMatcher

from .models import CardPaymentReconciliation
from common.models import Expense, Receipt

logger = structlog.get_logger()

class ReconciliationService:
    """Card payment reconciliation service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def import_card_payment(
        self,
        card_transaction_id: str,
        card_last_four: str,
        merchant_name: str,
        transaction_date: datetime,
        amount: Decimal,
        currency: str = "EUR",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Import card payment and attempt automatic reconciliation"""
        try:
            # Check if already imported
            existing = await self.db.execute(
                select(CardPaymentReconciliation).where(
                    and_(
                        CardPaymentReconciliation.tenant_id == self.tenant_id,
                        CardPaymentReconciliation.card_transaction_id == card_transaction_id,
                        CardPaymentReconciliation.deleted_at.is_(None)
                    )
                )
            )
            if existing.scalar_one_or_none():
                return {"success": False, "error": "Card payment already imported"}
            
            # Create reconciliation record
            reconciliation = CardPaymentReconciliation(
                tenant_id=self.tenant_id,
                card_transaction_id=card_transaction_id,
                card_last_four=card_last_four,
                merchant_name=merchant_name,
                transaction_date=transaction_date,
                amount=amount,
                currency=currency,
                status="pending",
                metadata=metadata or {}
            )
            
            self.db.add(reconciliation)
            await self.db.flush()
            
            # Attempt automatic matching
            match_result = await self._attempt_automatic_match(reconciliation)
            
            if match_result["matched"]:
                reconciliation.expense_id = match_result.get("expense_id")
                reconciliation.receipt_id = match_result.get("receipt_id")
                reconciliation.match_confidence = match_result.get("confidence", 0)
                reconciliation.match_method = "automatic"
                reconciliation.match_score = match_result.get("score", 0)
                reconciliation.status = "matched"
            else:
                reconciliation.match_method = "automatic"
                reconciliation.match_score = match_result.get("score", 0)
                reconciliation.status = "unmatched"
            
            await self.db.commit()
            
            return {
                "success": True,
                "reconciliation_id": str(reconciliation.id),
                "matched": match_result["matched"],
                "expense_id": match_result.get("expense_id"),
                "confidence": match_result.get("confidence", 0)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("import_card_payment_error", error=str(e))
            raise
    
    async def _attempt_automatic_match(
        self,
        reconciliation: CardPaymentReconciliation
    ) -> Dict[str, Any]:
        """Attempt to automatically match card payment with expense/receipt"""
        try:
            # Search window: ±7 days from transaction date
            date_from = reconciliation.transaction_date - timedelta(days=7)
            date_to = reconciliation.transaction_date + timedelta(days=7)
            
            # Search for expenses with matching amount and date
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= date_from.date(),
                        Expense.expense_date <= date_to.date(),
                        Expense.amount.between(
                            reconciliation.amount * Decimal('0.95'),  # 5% tolerance
                            reconciliation.amount * Decimal('1.05')
                        ),
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expenses = result.scalars().all()
            
            best_match = None
            best_score = 0.0
            
            for expense in expenses:
                score = self._calculate_match_score(reconciliation, expense)
                if score > best_score:
                    best_score = score
                    best_match = expense
            
            # Threshold for automatic matching: 70%
            if best_match and best_score >= 0.70:
                # Get receipt if available
                receipt_id = None
                if hasattr(best_match, 'receipts') and best_match.receipts:
                    receipt_id = best_match.receipts[0].id
                
                return {
                    "matched": True,
                    "expense_id": str(best_match.id),
                    "receipt_id": str(receipt_id) if receipt_id else None,
                    "confidence": best_score * 100,
                    "score": best_score
                }
            
            return {
                "matched": False,
                "score": best_score if best_match else 0.0
            }
            
        except Exception as e:
            logger.error("attempt_automatic_match_error", error=str(e))
            return {"matched": False, "score": 0.0}
    
    def _calculate_match_score(
        self,
        reconciliation: CardPaymentReconciliation,
        expense: Expense
    ) -> float:
        """Calculate match score between card payment and expense"""
        score = 0.0
        
        # Amount match (40% weight)
        amount_diff = abs(float(reconciliation.amount - expense.amount))
        amount_tolerance = float(reconciliation.amount) * 0.05  # 5% tolerance
        if amount_diff <= amount_tolerance:
            amount_score = 1.0 - (amount_diff / amount_tolerance)
            score += amount_score * 0.4
        
        # Date match (30% weight)
        date_diff = abs((reconciliation.transaction_date.date() - expense.expense_date).days)
        if date_diff == 0:
            date_score = 1.0
        elif date_diff <= 3:
            date_score = 1.0 - (date_diff / 3.0) * 0.5
        else:
            date_score = max(0.0, 1.0 - (date_diff / 7.0))
        score += date_score * 0.3
        
        # Merchant name match (30% weight)
        if reconciliation.merchant_name and expense.merchant_name:
            merchant_similarity = SequenceMatcher(
                None,
                reconciliation.merchant_name.lower(),
                expense.merchant_name.lower()
            ).ratio()
            score += merchant_similarity * 0.3
        
        return min(1.0, score)
    
    async def manual_reconcile(
        self,
        reconciliation_id: str,
        expense_id: str,
        reviewed_by: str
    ) -> Dict[str, Any]:
        """Manually reconcile card payment with expense"""
        try:
            result = await self.db.execute(
                select(CardPaymentReconciliation).where(
                    and_(
                        CardPaymentReconciliation.id == reconciliation_id,
                        CardPaymentReconciliation.tenant_id == self.tenant_id,
                        CardPaymentReconciliation.deleted_at.is_(None)
                    )
                )
            )
            reconciliation = result.scalar_one_or_none()
            
            if not reconciliation:
                raise ValueError("Reconciliation not found")
            
            reconciliation.expense_id = expense_id
            reconciliation.status = "matched"
            reconciliation.match_method = "manual"
            reconciliation.reviewed_by = reviewed_by
            reconciliation.reviewed_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "reconciliation_id": str(reconciliation.id),
                "expense_id": expense_id
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("manual_reconcile_error", error=str(e))
            raise
    
    async def list_unmatched_payments(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List unmatched card payments"""
        try:
            result = await self.db.execute(
                select(CardPaymentReconciliation).where(
                    and_(
                        CardPaymentReconciliation.tenant_id == self.tenant_id,
                        CardPaymentReconciliation.status == "unmatched",
                        CardPaymentReconciliation.deleted_at.is_(None)
                    )
                ).order_by(CardPaymentReconciliation.transaction_date.desc())
                .limit(limit)
            )
            reconciliations = result.scalars().all()
            
            return [
                {
                    "id": str(r.id),
                    "card_transaction_id": r.card_transaction_id,
                    "merchant_name": r.merchant_name,
                    "transaction_date": r.transaction_date.isoformat(),
                    "amount": float(r.amount),
                    "currency": r.currency,
                    "match_score": float(r.match_score) if r.match_score else 0.0
                }
                for r in reconciliations
            ]
            
        except Exception as e:
            logger.error("list_unmatched_payments_error", error=str(e))
            return []




