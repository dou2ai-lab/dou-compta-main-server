# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Policy service business logic
# -----------------------------------------------------------------------------

"""
Policy service business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import structlog

from common.models import Expense, PolicyViolation
from services.policy_service.evaluator import PolicyEvaluator
from services.policy_service.models import PolicyEvaluationRequest, PolicyEvaluationResponse

logger = structlog.get_logger()

class PolicyService:
    """Policy service for managing violations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.evaluator = PolicyEvaluator(db)
    
    async def evaluate_and_save_violations(
        self,
        expense: Expense,
        user_roles: List[str]
    ) -> PolicyEvaluationResponse:
        """
        Evaluate expense and save violations to database
        
        Args:
            expense: Expense to evaluate
            user_roles: List of user role names
            
        Returns:
            PolicyEvaluationResponse with violations
        """
        try:
            # Capture all expense data IMMEDIATELY to avoid accessing detached object
            # This prevents MissingGreenlet errors if the expense becomes detached
            expense_id = expense.id
            expense_amount = expense.amount
            expense_currency = expense.currency
            expense_date_val = expense.expense_date
            expense_category = expense.category
            expense_merchant_name = expense.merchant_name
            expense_description = expense.description
            expense_user_id = expense.submitted_by
            expense_tenant_id = expense.tenant_id
            
            # Create evaluation request using captured values
            eval_request = PolicyEvaluationRequest(
                expense_id=expense_id,
                amount=expense_amount,
                currency=expense_currency,
                expense_date=expense_date_val,
                category=expense_category,
                merchant_name=expense_merchant_name,
                description=expense_description,
                user_id=expense_user_id,
                tenant_id=expense_tenant_id,
                user_roles=user_roles
            )
            
            # Evaluate
            evaluation = await self.evaluator.evaluate_expense(eval_request)
            
            # Delete existing violations for this expense using captured ID
            # Wrap in try/except to handle transaction failures gracefully
            try:
                await self.db.execute(
                    delete(PolicyViolation).where(
                        PolicyViolation.expense_id == expense_id
                    )
                )
            except Exception as delete_error:
                # If delete fails (e.g., transaction already aborted), rollback and re-raise
                # This will be caught by the outer exception handler in submit_expense
                logger.warning(
                    "failed_to_delete_existing_violations",
                    expense_id=str(expense_id),
                    error=str(delete_error)
                )
                # Re-raise to trigger rollback in calling code
                raise
            
            # Save new violations using captured ID
            for violation in evaluation.violations:
                policy_violation = PolicyViolation(
                    expense_id=expense_id,
                    policy_id=violation.policy_id,
                    violation_type=violation.violation_type.value,
                    violation_severity=violation.violation_severity.value,
                    violation_message=violation.violation_message,
                    policy_rule=violation.policy_rule,
                    requires_comment=violation.requires_comment,
                    is_resolved=False
                )
                self.db.add(policy_violation)
            
            # Update expense violation flags
            # Only update if expense is still attached (use try/except)
            try:
                expense.policy_violation_count = evaluation.total_violations
                expense.has_policy_violations = evaluation.has_violations
            except Exception as attr_error:
                # If expense is detached, log warning but continue
                logger.warning(
                    "expense_detached_during_policy_update",
                    expense_id=str(expense_id),
                    error=str(attr_error)
                )
                # The flags will be updated when we re-fetch the expense later
            
            await self.db.flush()
            
            logger.info(
                "policy_violations_saved",
                expense_id=str(expense_id),
                violation_count=evaluation.total_violations
            )
            
            return evaluation
            
        except Exception as e:
            logger.error("policy_evaluation_save_failed", error=str(e), exc_info=True)
            raise
    
    async def get_expense_violations(
        self,
        expense_id: UUID
    ) -> List[PolicyViolation]:
        """Get all violations for an expense"""
        result = await self.db.execute(
            select(PolicyViolation).where(
                PolicyViolation.expense_id == expense_id,
                PolicyViolation.is_resolved == False
            )
        )
        return list(result.scalars().all())
    
    async def resolve_violation(
        self,
        violation_id: UUID,
        resolved_by: UUID,
        comment: Optional[str] = None
    ) -> PolicyViolation:
        """Mark a violation as resolved"""
        result = await self.db.execute(
            select(PolicyViolation).where(
                PolicyViolation.id == violation_id
            )
        )
        violation = result.scalar_one_or_none()
        
        if not violation:
            raise ValueError("Violation not found")
        
        violation.is_resolved = True
        violation.resolved_at = datetime.utcnow()
        violation.resolved_by = resolved_by
        if comment:
            violation.comment_provided = comment
        
        await self.db.flush()
        
        logger.info("policy_violation_resolved", violation_id=str(violation_id))
        
        return violation


















