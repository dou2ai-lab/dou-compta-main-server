# -----------------------------------------------------------------------------
# File: offline_service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Offline support for expense draft creation
# -----------------------------------------------------------------------------

"""
Offline Support Service
Handles expense draft creation and synchronization for mobile apps
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime
import structlog
import json

from common.models import Expense
from .models import ExpenseCreate, ExpenseUpdate

logger = structlog.get_logger()

class OfflineExpenseService:
    """Offline expense service for mobile apps"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def create_draft(
        self,
        draft_data: Dict[str, Any],
        user_id: str,
        client_id: Optional[str] = None  # Client-side ID for offline sync
    ) -> Dict[str, Any]:
        """Create expense draft (can be created offline)"""
        try:
            expense = Expense(
                tenant_id=self.tenant_id,
                submitted_by=user_id,
                amount=draft_data.get("amount", 0),
                currency=draft_data.get("currency", "EUR"),
                expense_date=draft_data.get("expense_date", datetime.utcnow().date()),
                category=draft_data.get("category"),
                description=draft_data.get("description"),
                merchant_name=draft_data.get("merchant_name"),
                status="draft",
                meta_data={
                    "client_id": client_id,
                    "offline_created": True,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(expense)
            await self.db.flush()
            
            return {
                "success": True,
                "expense_id": str(expense.id),
                "client_id": client_id,
                "status": "draft",
                "synced": False
            }
            
        except Exception as e:
            logger.error("create_draft_error", error=str(e))
            raise
    
    async def sync_drafts(
        self,
        drafts: List[Dict[str, Any]],
        user_id: str
    ) -> Dict[str, Any]:
        """Sync multiple drafts from offline storage"""
        try:
            synced = []
            failed = []
            
            for draft in drafts:
                try:
                    client_id = draft.get("client_id")
                    
                    # Check if already synced
                    if client_id:
                        existing = await self.db.execute(
                            select(Expense).where(
                                and_(
                                    Expense.tenant_id == self.tenant_id,
                                    Expense.submitted_by == user_id,
                                    Expense.meta_data["client_id"].astext == client_id,
                                    Expense.deleted_at.is_(None)
                                )
                            )
                        )
                        if existing.scalar_one_or_none():
                            synced.append({"client_id": client_id, "status": "already_synced"})
                            continue
                    
                    # Create draft
                    result = await self.create_draft(
                        draft_data=draft,
                        user_id=user_id,
                        client_id=client_id
                    )
                    synced.append(result)
                    
                except Exception as e:
                    failed.append({
                        "client_id": draft.get("client_id"),
                        "error": str(e)
                    })
            
            await self.db.commit()
            
            return {
                "success": True,
                "synced": synced,
                "failed": failed,
                "total": len(drafts),
                "synced_count": len(synced),
                "failed_count": len(failed)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("sync_drafts_error", error=str(e))
            raise
    
    async def get_pending_drafts(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get pending drafts for user"""
        try:
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.submitted_by == user_id,
                        Expense.status == "draft",
                        Expense.deleted_at.is_(None)
                    )
                ).order_by(Expense.created_at.desc())
            )
            expenses = result.scalars().all()
            
            return [
                {
                    "id": str(e.id),
                    "amount": float(e.amount),
                    "currency": e.currency,
                    "expense_date": e.expense_date.isoformat() if e.expense_date else None,
                    "category": e.category,
                    "description": e.description,
                    "merchant_name": e.merchant_name,
                    "client_id": e.meta_data.get("client_id") if e.meta_data else None,
                    "offline_created": e.meta_data.get("offline_created", False) if e.meta_data else False,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in expenses
            ]
            
        except Exception as e:
            logger.error("get_pending_drafts_error", error=str(e))
            return []




