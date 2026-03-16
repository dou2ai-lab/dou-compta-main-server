# -----------------------------------------------------------------------------
# File: retention_service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Data retention service
# -----------------------------------------------------------------------------

"""
Data Retention Service
Implements retention rules including 10-year accounting retention
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from datetime import datetime, timedelta
import structlog

from .models import RetentionRule, DataMinimizationJob
from .config import settings
from common.models import Expense, Receipt, User

logger = structlog.get_logger()

class RetentionService:
    """Data retention service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def initialize_default_rules(self):
        """Initialize default retention rules"""
        try:
            # Check if rules already exist
            result = await self.db.execute(
                select(RetentionRule).where(
                    and_(
                        RetentionRule.tenant_id == self.tenant_id,
                        RetentionRule.deleted_at.is_(None)
                    )
                )
            )
            existing = result.scalars().all()
            
            if existing:
                return {"success": True, "message": "Rules already exist"}
            
            # Create default rules
            default_rules = [
                {
                    "entity_type": "expense",
                    "retention_years": settings.ACCOUNTING_RETENTION_YEARS,
                    "action_on_expiry": "archive"
                },
                {
                    "entity_type": "receipt",
                    "retention_years": settings.ACCOUNTING_RETENTION_YEARS,
                    "action_on_expiry": "archive"
                },
                {
                    "entity_type": "user",
                    "retention_years": settings.PERSONAL_DATA_RETENTION_YEARS,
                    "action_on_expiry": "anonymize"
                },
                {
                    "entity_type": "privacy_log",
                    "retention_days": settings.LOG_RETENTION_DAYS,
                    "action_on_expiry": "delete"
                }
            ]
            
            for rule_data in default_rules:
                rule = RetentionRule(
                    tenant_id=self.tenant_id,
                    entity_type=rule_data["entity_type"],
                    retention_years=rule_data.get("retention_years", 0),
                    retention_days=rule_data.get("retention_days"),
                    action_on_expiry=rule_data["action_on_expiry"],
                    is_active=True
                )
                self.db.add(rule)
            
            await self.db.commit()
            
            return {"success": True, "rules_created": len(default_rules)}
            
        except Exception as e:
            await self.db.rollback()
            logger.error("initialize_default_rules_error", error=str(e))
            raise
    
    async def apply_retention_rules(self) -> Dict[str, Any]:
        """Apply retention rules to all entities"""
        try:
            result = await self.db.execute(
                select(RetentionRule).where(
                    and_(
                        RetentionRule.tenant_id == self.tenant_id,
                        RetentionRule.is_active == True,
                        RetentionRule.deleted_at.is_(None)
                    )
                )
            )
            rules = result.scalars().all()
            
            summary = {
                "processed": 0,
                "archived": 0,
                "deleted": 0,
                "anonymized": 0
            }
            
            for rule in rules:
                rule_result = await self._apply_rule(rule)
                summary["processed"] += rule_result.get("processed", 0)
                summary["archived"] += rule_result.get("archived", 0)
                summary["deleted"] += rule_result.get("deleted", 0)
                summary["anonymized"] += rule_result.get("anonymized", 0)
                
                # Update rule last run
                rule.last_run_at = datetime.utcnow()
                rule.next_run_at = datetime.utcnow() + timedelta(days=30)  # Run monthly
            
            await self.db.commit()
            
            return {
                "success": True,
                "summary": summary
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("apply_retention_rules_error", error=str(e))
            raise
    
    async def _apply_rule(self, rule: RetentionRule) -> Dict[str, Any]:
        """Apply a single retention rule"""
        try:
            cutoff_date = datetime.utcnow()
            
            if rule.retention_years:
                cutoff_date = cutoff_date - timedelta(days=rule.retention_years * 365)
            elif rule.retention_days:
                cutoff_date = cutoff_date - timedelta(days=rule.retention_days)
            else:
                return {"processed": 0}
            
            result = {
                "processed": 0,
                "archived": 0,
                "deleted": 0,
                "anonymized": 0
            }
            
            if rule.entity_type == "expense":
                result = await self._apply_expense_retention(rule, cutoff_date)
            elif rule.entity_type == "receipt":
                result = await self._apply_receipt_retention(rule, cutoff_date)
            elif rule.entity_type == "user":
                result = await self._apply_user_retention(rule, cutoff_date)
            elif rule.entity_type == "privacy_log":
                result = await self._apply_log_retention(rule, cutoff_date)
            
            return result
            
        except Exception as e:
            logger.error("apply_rule_error", rule_id=str(rule.id), error=str(e))
            return {"processed": 0}
    
    async def _apply_expense_retention(
        self,
        rule: RetentionRule,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Apply retention to expenses"""
        try:
            # For accounting retention, we archive (soft delete) but keep data
            if rule.action_on_expiry == "archive":
                result = await self.db.execute(
                    text("""
                        UPDATE expenses
                        SET deleted_at = CURRENT_TIMESTAMP
                        WHERE tenant_id = :tenant_id
                        AND expense_date < :cutoff_date
                        AND deleted_at IS NULL
                    """),
                    {
                        "tenant_id": self.tenant_id,
                        "cutoff_date": cutoff_date.date()
                    }
                )
                count = result.rowcount
                return {"processed": count, "archived": count}
            
            return {"processed": 0}
            
        except Exception as e:
            logger.error("apply_expense_retention_error", error=str(e))
            return {"processed": 0}
    
    async def _apply_receipt_retention(
        self,
        rule: RetentionRule,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Apply retention to receipts"""
        try:
            if rule.action_on_expiry == "archive":
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
                count = result.rowcount
                return {"processed": count, "archived": count}
            
            return {"processed": 0}
            
        except Exception as e:
            logger.error("apply_receipt_retention_error", error=str(e))
            return {"processed": 0}
    
    async def _apply_user_retention(
        self,
        rule: RetentionRule,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Apply retention to users (anonymize)"""
        try:
            if rule.action_on_expiry == "anonymize":
                # Anonymize users who haven't been active
                result = await self.db.execute(
                    text("""
                        UPDATE users
                        SET email = 'deleted_' || id::text || '@deleted.local',
                            first_name = 'Deleted',
                            last_name = 'User'
                        WHERE tenant_id = :tenant_id
                        AND last_login_at < :cutoff_date
                        AND email NOT LIKE 'deleted_%@deleted.local'
                    """),
                    {
                        "tenant_id": self.tenant_id,
                        "cutoff_date": cutoff_date
                    }
                )
                count = result.rowcount
                return {"processed": count, "anonymized": count}
            
            return {"processed": 0}
            
        except Exception as e:
            logger.error("apply_user_retention_error", error=str(e))
            return {"processed": 0}
    
    async def _apply_log_retention(
        self,
        rule: RetentionRule,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Apply retention to privacy logs (delete)"""
        try:
            if rule.action_on_expiry == "delete":
                from .models import PrivacyLog
                
                result = await self.db.execute(
                    text("""
                        DELETE FROM privacy_logs
                        WHERE tenant_id = :tenant_id
                        AND created_at < :cutoff_date
                    """),
                    {
                        "tenant_id": self.tenant_id,
                        "cutoff_date": cutoff_date
                    }
                )
                count = result.rowcount
                return {"processed": count, "deleted": count}
            
            return {"processed": 0}
            
        except Exception as e:
            logger.error("apply_log_retention_error", error=str(e))
            return {"processed": 0}




