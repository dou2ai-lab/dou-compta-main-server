# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: URSSAF service business logic
# -----------------------------------------------------------------------------

"""
URSSAF Service
Main service layer for URSSAF compliance
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from typing import List, Optional, Dict, Any
from uuid import UUID
import structlog

from .evaluator import URSSAFEvaluator
from .models import URSSAFComplianceCheck, URSSAFRule
from common.models import Expense

logger = structlog.get_logger()


class URSSAFService:
    """URSSAF compliance service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.evaluator = URSSAFEvaluator(db, tenant_id)
    
    async def evaluate_and_save_compliance(
        self,
        expense: Expense,
        user_roles: Optional[List[str]] = None
    ) -> URSSAFComplianceCheck:
        """
        Evaluate expense and save compliance check
        
        Args:
            expense: Expense to evaluate
            user_roles: User roles
        
        Returns:
            URSSAFComplianceCheck with evaluation result
        """
        try:
            # Delete existing checks for this expense
            await self.db.execute(
                delete(URSSAFComplianceCheck).where(
                    and_(
                        URSSAFComplianceCheck.expense_id == expense.id,
                        URSSAFComplianceCheck.tenant_id == self.tenant_id
                    )
                )
            )
            
            # Evaluate and save
            compliance_check = await self.evaluator.evaluate_expense(expense, user_roles)
            
            await self.db.flush()
            
            logger.info(
                "urssaf_compliance_saved",
                expense_id=str(expense.id),
                is_compliant=compliance_check.is_compliant,
                compliance_status=compliance_check.compliance_status
            )
            
            return compliance_check
            
        except Exception as e:
            logger.error("urssaf_evaluation_save_failed", expense_id=str(expense.id), error=str(e))
            raise
    
    async def get_expense_compliance(
        self,
        expense_id: UUID
    ) -> Optional[URSSAFComplianceCheck]:
        """Get URSSAF compliance check for expense"""
        return await self.evaluator.get_expense_compliance(expense_id)
    
    async def list_compliance_checks(
        self,
        limit: int = 20,
        offset: int = 0,
        compliance_status: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> List[URSSAFComplianceCheck]:
        """List URSSAF compliance checks"""
        query = select(URSSAFComplianceCheck).where(
            URSSAFComplianceCheck.tenant_id == self.tenant_id
        )
        
        if compliance_status:
            query = query.where(URSSAFComplianceCheck.compliance_status == compliance_status)
        
        if risk_level:
            query = query.where(URSSAFComplianceCheck.risk_level == risk_level)
        
        query = query.order_by(URSSAFComplianceCheck.checked_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_compliance_summary(
        self
    ) -> Dict[str, Any]:
        """Get URSSAF compliance summary for tenant"""
        from sqlalchemy import func
        
        # Get compliance statistics
        result = await self.db.execute(
            select(
                func.count(URSSAFComplianceCheck.id).label('total_checks'),
                func.sum(
                    func.cast(URSSAFComplianceCheck.is_compliant, func.Integer)
                ).label('compliant_count'),
                func.sum(
                    func.cast(URSSAFComplianceCheck.contribution_applicable, func.Integer)
                ).label('contribution_count'),
                func.sum(URSSAFComplianceCheck.contribution_amount).label('total_contribution')
            ).where(
                URSSAFComplianceCheck.tenant_id == self.tenant_id
            )
        )
        stats = result.one()
        
        total = stats.total_checks or 0
        compliant = stats.compliant_count or 0
        compliance_rate = (compliant / total * 100) if total > 0 else 0
        
        return {
            "total_checks": total,
            "compliant_count": compliant,
            "non_compliant_count": total - compliant,
            "compliance_rate": round(compliance_rate, 2),
            "contribution_applicable_count": stats.contribution_count or 0,
            "total_contribution_amount": float(stats.total_contribution or 0)
        }

