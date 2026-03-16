# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: URSSAF service API routes
# -----------------------------------------------------------------------------

"""
URSSAF Service Routes
API endpoints for URSSAF compliance
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .service import URSSAFService
from .schemas import (
    URSSAFComplianceCheckResponse,
    URSSAFComplianceSummaryResponse,
    URSSAFRuleCreate,
    URSSAFRuleUpdate,
    URSSAFRuleResponse
)
from .models import URSSAFRule, URSSAFComplianceCheck
from sqlalchemy import select, and_

router = APIRouter()
logger = structlog.get_logger()


async def require_admin_permission(user: User, db: AsyncSession):
    """Require admin permission for URSSAF rule management"""
    # Check if user has admin role
    from common.models import UserRole, Role
    result = await db.execute(
        select(Role).join(UserRole).where(
            and_(
                UserRole.user_id == user.id,
                Role.name.in_(["admin", "super_admin"])
            )
        )
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=403, detail="Admin permission required")


@router.post("/expenses/{expense_id}/evaluate", response_model=URSSAFComplianceCheckResponse)
async def evaluate_expense_compliance(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Evaluate expense for URSSAF compliance"""
    try:
        from common.models import Expense
        
        # Get expense
        result = await db.execute(
            select(Expense).where(
                and_(
                    Expense.id == expense_id,
                    Expense.tenant_id == current_user.tenant_id,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        # Evaluate
        service = URSSAFService(db, str(current_user.tenant_id))
        compliance_check = await service.evaluate_and_save_compliance(expense)
        
        await db.commit()
        
        return URSSAFComplianceCheckResponse(
            id=str(compliance_check.id),
            expense_id=str(compliance_check.expense_id),
            is_compliant=compliance_check.is_compliant,
            compliance_status=compliance_check.compliance_status,
            risk_level=compliance_check.risk_level,
            expense_classification=compliance_check.expense_classification,
            employee_classification=compliance_check.employee_classification,
            contribution_applicable=compliance_check.contribution_applicable,
            contribution_rate=compliance_check.contribution_rate,
            contribution_amount=compliance_check.contribution_amount,
            exemption_applicable=compliance_check.exemption_applicable,
            exemption_reason=compliance_check.exemption_reason,
            exemption_threshold_met=compliance_check.exemption_threshold_met,
            rule_name=compliance_check.rule_name,
            explanation=compliance_check.explanation,
            recommendations=compliance_check.recommendations or [],
            checked_at=compliance_check.checked_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("evaluate_expense_compliance_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to evaluate URSSAF compliance")


@router.get("/expenses/{expense_id}/compliance", response_model=URSSAFComplianceCheckResponse)
async def get_expense_compliance(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get URSSAF compliance check for expense"""
    try:
        service = URSSAFService(db, str(current_user.tenant_id))
        compliance_check = await service.get_expense_compliance(UUID(expense_id))
        
        if not compliance_check:
            raise HTTPException(status_code=404, detail="Compliance check not found")
        
        return URSSAFComplianceCheckResponse(
            id=str(compliance_check.id),
            expense_id=str(compliance_check.expense_id),
            is_compliant=compliance_check.is_compliant,
            compliance_status=compliance_check.compliance_status,
            risk_level=compliance_check.risk_level,
            expense_classification=compliance_check.expense_classification,
            employee_classification=compliance_check.employee_classification,
            contribution_applicable=compliance_check.contribution_applicable,
            contribution_rate=compliance_check.contribution_rate,
            contribution_amount=compliance_check.contribution_amount,
            exemption_applicable=compliance_check.exemption_applicable,
            exemption_reason=compliance_check.exemption_reason,
            exemption_threshold_met=compliance_check.exemption_threshold_met,
            rule_name=compliance_check.rule_name,
            explanation=compliance_check.explanation,
            recommendations=compliance_check.recommendations or [],
            checked_at=compliance_check.checked_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_expense_compliance_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get compliance check")


@router.get("/compliance/summary", response_model=URSSAFComplianceSummaryResponse)
async def get_compliance_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get URSSAF compliance summary"""
    try:
        service = URSSAFService(db, str(current_user.tenant_id))
        summary = await service.get_compliance_summary()
        
        return URSSAFComplianceSummaryResponse(**summary)
        
    except Exception as e:
        logger.error("get_compliance_summary_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get compliance summary")


@router.get("/rules", response_model=List[URSSAFRuleResponse])
async def list_rules(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List URSSAF rules"""
    try:
        query = select(URSSAFRule).where(
            and_(
                URSSAFRule.tenant_id == current_user.tenant_id,
                URSSAFRule.deleted_at.is_(None)
            )
        )
        
        if is_active is not None:
            query = query.where(URSSAFRule.is_active == is_active)
        
        query = query.order_by(URSSAFRule.created_at.desc()).limit(limit).offset(offset)
        
        result = await db.execute(query)
        rules = result.scalars().all()
        
        return [
            URSSAFRuleResponse(
                id=str(rule.id),
                tenant_id=str(rule.tenant_id),
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                description=rule.description,
                expense_category=rule.expense_category,
                expense_type=rule.expense_type,
                amount_threshold=rule.amount_threshold,
                employee_type=rule.employee_type,
                contribution_rate=rule.contribution_rate,
                exemption_applicable=rule.exemption_applicable,
                is_mandatory=rule.is_mandatory,
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
                is_active=rule.is_active,
                meta_data=rule.meta_data or {},
                created_at=rule.created_at.isoformat(),
                updated_at=rule.updated_at.isoformat()
            )
            for rule in rules
        ]
        
    except Exception as e:
        logger.error("list_rules_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list rules")


@router.post("/rules", response_model=URSSAFRuleResponse)
async def create_rule(
    rule_data: URSSAFRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create URSSAF rule"""
    await require_admin_permission(current_user, db)
    
    try:
        rule = URSSAFRule(
            tenant_id=current_user.tenant_id,
            rule_name=rule_data.rule_name,
            rule_type=rule_data.rule_type,
            description=rule_data.description,
            expense_category=rule_data.expense_category,
            expense_type=rule_data.expense_type,
            amount_threshold=rule_data.amount_threshold,
            employee_type=rule_data.employee_type,
            contribution_rate=rule_data.contribution_rate,
            exemption_applicable=rule_data.exemption_applicable,
            is_mandatory=rule_data.is_mandatory,
            effective_from=rule_data.effective_from,
            effective_to=rule_data.effective_to,
            is_active=True,
            meta_data=rule_data.meta_data
        )
        
        db.add(rule)
        await db.flush()
        await db.commit()
        
        return URSSAFRuleResponse(
            id=str(rule.id),
            tenant_id=str(rule.tenant_id),
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            description=rule.description,
            expense_category=rule.expense_category,
            expense_type=rule.expense_type,
            amount_threshold=rule.amount_threshold,
            employee_type=rule.employee_type,
            contribution_rate=rule.contribution_rate,
            exemption_applicable=rule.exemption_applicable,
            is_mandatory=rule.is_mandatory,
            effective_from=rule.effective_from,
            effective_to=rule.effective_to,
            is_active=rule.is_active,
            meta_data=rule.meta_data or {},
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat()
        )
        
    except Exception as e:
        await db.rollback()
        logger.error("create_rule_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create rule")


@router.put("/rules/{rule_id}", response_model=URSSAFRuleResponse)
async def update_rule(
    rule_id: str,
    rule_data: URSSAFRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update URSSAF rule"""
    await require_admin_permission(current_user, db)
    
    try:
        result = await db.execute(
            select(URSSAFRule).where(
                and_(
                    URSSAFRule.id == rule_id,
                    URSSAFRule.tenant_id == current_user.tenant_id,
                    URSSAFRule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        # Update fields
        if rule_data.rule_name is not None:
            rule.rule_name = rule_data.rule_name
        if rule_data.description is not None:
            rule.description = rule_data.description
        if rule_data.contribution_rate is not None:
            rule.contribution_rate = rule_data.contribution_rate
        if rule_data.exemption_applicable is not None:
            rule.exemption_applicable = rule_data.exemption_applicable
        if rule_data.is_active is not None:
            rule.is_active = rule_data.is_active
        if rule_data.effective_from is not None:
            rule.effective_from = rule_data.effective_from
        if rule_data.effective_to is not None:
            rule.effective_to = rule_data.effective_to
        if rule_data.meta_data is not None:
            rule.meta_data = {**(rule.meta_data or {}), **rule_data.meta_data}
        
        await db.flush()
        await db.commit()
        
        return URSSAFRuleResponse(
            id=str(rule.id),
            tenant_id=str(rule.tenant_id),
            rule_name=rule.rule_name,
            rule_type=rule.rule_type,
            description=rule.description,
            expense_category=rule.expense_category,
            expense_type=rule.expense_type,
            amount_threshold=rule.amount_threshold,
            employee_type=rule.employee_type,
            contribution_rate=rule.contribution_rate,
            exemption_applicable=rule.exemption_applicable,
            is_mandatory=rule.is_mandatory,
            effective_from=rule.effective_from,
            effective_to=rule.effective_to,
            is_active=rule.is_active,
            meta_data=rule.meta_data or {},
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("update_rule_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update rule")


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete URSSAF rule (soft delete)"""
    await require_admin_permission(current_user, db)
    
    try:
        from datetime import datetime
        
        result = await db.execute(
            select(URSSAFRule).where(
                and_(
                    URSSAFRule.id == rule_id,
                    URSSAFRule.tenant_id == current_user.tenant_id,
                    URSSAFRule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        
        rule.deleted_at = datetime.utcnow()
        rule.is_active = False
        
        await db.flush()
        await db.commit()
        
        return {"success": True, "message": "Rule deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("delete_rule_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete rule")

