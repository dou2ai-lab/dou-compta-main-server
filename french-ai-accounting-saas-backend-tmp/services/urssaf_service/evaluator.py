# -----------------------------------------------------------------------------
# File: evaluator.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: URSSAF compliance evaluator service
# -----------------------------------------------------------------------------

"""
URSSAF Compliance Evaluator
Service layer for evaluating expenses against URSSAF rules
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Dict, Any, Optional
from uuid import UUID
import structlog

from .rules import URSSAFRulesEngine
from .models import URSSAFComplianceCheck, URSSAFRule
from common.models import Expense, User

logger = structlog.get_logger()


class URSSAFEvaluator:
    """URSSAF compliance evaluator"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.rules_engine = URSSAFRulesEngine()
    
    async def evaluate_expense(
        self,
        expense: Expense,
        user_roles: Optional[list] = None
    ) -> URSSAFComplianceCheck:
        """
        Evaluate expense for URSSAF compliance
        
        Args:
            expense: Expense to evaluate
            user_roles: User roles (for future role-based rules)
        
        Returns:
            URSSAFComplianceCheck with evaluation result
        """
        try:
            # Prepare expense data for rules engine
            expense_data = {
                "amount": expense.amount,
                "category": expense.category or "",
                "expense_type": self._infer_expense_type(expense),
                "employee_type": self._infer_employee_type(expense),
                "description": expense.description or "",
                "expense_date": expense.expense_date
            }
            
            # Evaluate using rules engine
            evaluation_result = self.rules_engine.evaluate_expense(expense_data)
            
            # Create compliance check record
            compliance_check = URSSAFComplianceCheck(
                tenant_id=self.tenant_id,
                expense_id=expense.id,
                is_compliant=evaluation_result["is_compliant"],
                compliance_status=evaluation_result["compliance_status"],
                risk_level=evaluation_result["risk_level"],
                expense_classification=evaluation_result["expense_classification"],
                employee_classification=evaluation_result["employee_classification"],
                contribution_applicable=evaluation_result["contribution_applicable"],
                contribution_rate=evaluation_result["contribution_rate"],
                contribution_amount=evaluation_result["contribution_amount"],
                exemption_applicable=evaluation_result["exemption_applicable"],
                exemption_reason=evaluation_result.get("exemption_reason"),
                exemption_threshold_met=evaluation_result["exemption_threshold_met"],
                rule_name=evaluation_result.get("rule_applied"),
                explanation=evaluation_result["explanation"],
                recommendations=evaluation_result["recommendations"],
                meta_data={
                    "evaluation_data": expense_data,
                    "evaluation_result": evaluation_result
                }
            )
            
            # Get rule ID if rule name provided
            if evaluation_result.get("rule_applied"):
                rule_result = await self.db.execute(
                    select(URSSAFRule).where(
                        and_(
                            URSSAFRule.tenant_id == self.tenant_id,
                            URSSAFRule.rule_name == evaluation_result["rule_applied"],
                            URSSAFRule.is_active == True,
                            URSSAFRule.deleted_at.is_(None)
                        )
                    )
                )
                rule = rule_result.scalar_one_or_none()
                if rule:
                    compliance_check.rule_id = rule.id
            
            self.db.add(compliance_check)
            await self.db.flush()
            
            logger.info(
                "urssaf_evaluation_completed",
                expense_id=str(expense.id),
                is_compliant=evaluation_result["is_compliant"],
                compliance_status=evaluation_result["compliance_status"]
            )
            
            return compliance_check
            
        except Exception as e:
            logger.error("urssaf_evaluation_error", expense_id=str(expense.id), error=str(e))
            raise
    
    async def get_expense_compliance(
        self,
        expense_id: UUID
    ) -> Optional[URSSAFComplianceCheck]:
        """Get URSSAF compliance check for expense"""
        result = await self.db.execute(
            select(URSSAFComplianceCheck).where(
                and_(
                    URSSAFComplianceCheck.expense_id == expense_id,
                    URSSAFComplianceCheck.tenant_id == self.tenant_id
                )
            ).order_by(URSSAFComplianceCheck.checked_at.desc())
        )
        return result.scalar_one_or_none()
    
    def _infer_expense_type(self, expense: Expense) -> str:
        """Infer expense type from expense data"""
        description = (expense.description or "").lower()
        category = (expense.category or "").lower()
        
        # Check for reimbursement indicators
        if any(word in description for word in ["reimbursement", "remboursement", "refund"]):
            return "reimbursement"
        
        # Check category
        if "reimbursement" in category:
            return "reimbursement"
        
        # Default to benefit
        return "benefit"
    
    def _infer_employee_type(self, expense: Expense) -> str:
        """Infer employee type from expense data"""
        description = (expense.description or "").lower()
        merchant_name = (expense.merchant_name or "").lower()
        
        # Check for contractor indicators
        if any(word in description for word in ["freelance", "consultant", "auto-entrepreneur", "service"]):
            return "contractor"
        
        if any(word in merchant_name for word in ["freelance", "consultant"]):
            return "contractor"
        
        # Check for intern indicators
        if any(word in description for word in ["intern", "stage", "apprentice", "stagiaire"]):
            return "intern"
        
        # Default to employee
        return "employee"

