# -----------------------------------------------------------------------------
# File: data_minimization.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Data minimization service
# -----------------------------------------------------------------------------

"""
Data Minimization Service
Implements data minimization principles (GDPR Article 5)
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from datetime import datetime, timedelta
import structlog

from .models import DataMinimizationJob
from .config import settings
from common.models import Expense, Receipt, User

logger = structlog.get_logger()

class DataMinimizationService:
    """Data minimization service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.enabled = settings.ENABLE_DATA_MINIMIZATION
    
    async def run_minimization_pass(self) -> Dict[str, Any]:
        """Run data minimization pass"""
        try:
            if not self.enabled:
                return {"success": True, "message": "Data minimization disabled"}
            
            cutoff_date = datetime.utcnow() - timedelta(days=settings.ANONYMIZE_AFTER_YEARS * 365)
            
            # Create job
            job = DataMinimizationJob(
                tenant_id=self.tenant_id,
                entity_type="all",
                action="anonymize",
                status="running",
                started_at=datetime.utcnow()
            )
            
            self.db.add(job)
            await self.db.flush()
            
            summary = {
                "users_anonymized": 0,
                "expenses_anonymized": 0,
                "receipts_anonymized": 0
            }
            
            # Anonymize inactive users
            user_result = await self._anonymize_inactive_users(cutoff_date)
            summary["users_anonymized"] = user_result.get("count", 0)
            
            # Anonymize old expense personal data (keep accounting data)
            expense_result = await self._minimize_expense_data(cutoff_date)
            summary["expenses_anonymized"] = expense_result.get("count", 0)
            
            # Archive old receipts
            receipt_result = await self._minimize_receipt_data(cutoff_date)
            summary["receipts_anonymized"] = receipt_result.get("count", 0)
            
            # Update job
            job.status = "completed"
            job.records_processed = sum(summary.values())
            job.records_affected = sum(summary.values())
            job.completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "job_id": str(job.id),
                "summary": summary
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("run_minimization_pass_error", error=str(e))
            raise
    
    async def _anonymize_inactive_users(
        self,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Anonymize inactive users"""
        try:
            result = await self.db.execute(
                text("""
                    UPDATE users
                    SET email = 'anonymized_' || id::text || '@anonymized.local',
                        first_name = 'Anonymized',
                        last_name = 'User',
                        phone = NULL
                    WHERE tenant_id = :tenant_id
                    AND (last_login_at IS NULL OR last_login_at < :cutoff_date)
                    AND email NOT LIKE 'anonymized_%@anonymized.local'
                    AND email NOT LIKE 'deleted_%@deleted.local'
                """),
                {
                    "tenant_id": self.tenant_id,
                    "cutoff_date": cutoff_date
                }
            )
            
            return {"count": result.rowcount}
            
        except Exception as e:
            logger.error("anonymize_inactive_users_error", error=str(e))
            return {"count": 0}
    
    async def _minimize_expense_data(
        self,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Minimize expense data (remove unnecessary personal data)"""
        try:
            # Remove personal notes/comments from old expenses
            # Keep accounting data (amount, VAT, dates, categories)
            result = await self.db.execute(
                text("""
                    UPDATE expenses
                    SET description = CASE
                        WHEN description IS NOT NULL THEN 'Expense data anonymized'
                        ELSE description
                    END,
                    meta_data = jsonb_set(
                        COALESCE(meta_data, '{}'::jsonb),
                        '{anonymized}',
                        'true'::jsonb
                    )
                    WHERE tenant_id = :tenant_id
                    AND expense_date < :cutoff_date
                    AND (meta_data->>'anonymized') IS NULL
                """),
                {
                    "tenant_id": self.tenant_id,
                    "cutoff_date": cutoff_date.date()
                }
            )
            
            return {"count": result.rowcount}
            
        except Exception as e:
            logger.error("minimize_expense_data_error", error=str(e))
            return {"count": 0}
    
    async def _minimize_receipt_data(
        self,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Minimize receipt data"""
        try:
            # Archive old receipts (soft delete)
            result = await self.db.execute(
                text("""
                    UPDATE receipts
                    SET deleted_at = CURRENT_TIMESTAMP
                    WHERE tenant_id = :tenant_id
                    AND created_at < :cutoff_date
                    AND deleted_at IS NULL
                """),
                {
                    "tenant_id": self.tenant_id,
                    "cutoff_date": cutoff_date
                }
            )
            
            return {"count": result.rowcount}
            
        except Exception as e:
            logger.error("minimize_receipt_data_error", error=str(e))
            return {"count": 0}




