# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Policy service API routes
# -----------------------------------------------------------------------------

"""
Policy service routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from common.database import get_db
from common.models import Expense, User, UserRole, Role
from services.auth.dependencies import get_current_user
from services.policy_service.evaluator import PolicyEvaluator
from services.policy_service.models import (
    PolicyEvaluationRequest, PolicyEvaluationResponse
)

logger = structlog.get_logger()
router = APIRouter()

@router.post("/evaluate", response_model=PolicyEvaluationResponse)
async def evaluate_expense_policies(
    expense_id: str = Query(..., description="Expense ID to evaluate"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Evaluate an expense against applicable policies
    
    Args:
        expense_id: UUID of the expense to evaluate
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PolicyEvaluationResponse with violations and recommendations
    """
    try:
        # Get expense
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Check access
        if expense.submitted_by != current_user.id:
            # TODO: Check if user has admin/approver role
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Get user roles
        user_roles_result = await db.execute(
            select(Role.name).join(UserRole).where(
                UserRole.user_id == current_user.id
            )
        )
        user_roles = [role[0] for role in user_roles_result.all()]
        
        # Create evaluation request
        eval_request = PolicyEvaluationRequest(
            expense_id=expense.id,
            amount=expense.amount,
            currency=expense.currency,
            expense_date=expense.expense_date,
            category=expense.category,
            merchant_name=expense.merchant_name,
            description=expense.description,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            user_roles=user_roles
        )
        
        # Evaluate policies
        evaluator = PolicyEvaluator(db)
        evaluation_result = await evaluator.evaluate_expense(eval_request)
        
        logger.info(
            "policy_evaluation_completed",
            expense_id=str(expense_id),
            violation_count=evaluation_result.total_violations
        )
        
        return evaluation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("policy_evaluation_api_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to evaluate policies"
        )

