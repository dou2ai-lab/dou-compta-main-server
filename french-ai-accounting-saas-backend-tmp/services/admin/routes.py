# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Admin service routes
# -----------------------------------------------------------------------------

"""
Admin routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import ProgrammingError, OperationalError
from typing import Optional, List
from datetime import datetime
import structlog
import uuid as uuid_lib

from common.database import get_db
from common.models import User, Expense, PolicyViolation, Role, UserRole
from services.auth.dependencies import get_current_user, get_user_permissions
from services.policy_service.service import PolicyService
from .models import ExpenseCategory, GLAccount, ExpensePolicy, VatRule, TenantSettings, SettingsChangelog
from .schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    GLAccountCreate, GLAccountUpdate, GLAccountResponse,
    PolicyCreate, PolicyUpdate, PolicyResponse,
    CategorySuggestionRequest, CategorySuggestionResponse,
    VatRuleCreate, VatRuleUpdate, VatRuleResponse,
    SettingsUpdate, SettingsResponse, ChangelogEntryResponse,
)
from .service import CategorySuggestionService

logger = structlog.get_logger()
router = APIRouter()

async def require_admin_permission(current_user: User, db: AsyncSession):
    """Check if user has admin permissions"""
    permissions = await get_user_permissions(current_user, db)
    if "admin:read" not in permissions and "admin:write" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

@router.get("/vat-rules", response_model=List[VatRuleResponse])
async def list_vat_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all VAT rules"""
    await require_admin_permission(current_user, db)
    
    result = await db.execute(
        select(VatRule).where(
            VatRule.tenant_id == current_user.tenant_id,
            VatRule.deleted_at.is_(None)
        ).order_by(VatRule.is_default.desc(), VatRule.created_at.desc())
    )
    rules = result.scalars().all()
    return [VatRuleResponse.model_validate(r) for r in rules]

@router.post("/vat-rules", response_model=VatRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_vat_rule(
    rule_data: VatRuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new VAT rule"""
    await require_admin_permission(current_user, db)
    
    # If this is set as default, unset other defaults
    if rule_data.is_default:
        await db.execute(
            select(VatRule).where(
                VatRule.tenant_id == current_user.tenant_id,
                VatRule.is_default == True,
                VatRule.deleted_at.is_(None)
            )
        )
        existing_defaults = await db.execute(
            select(VatRule).where(
                VatRule.tenant_id == current_user.tenant_id,
                VatRule.is_default == True,
                VatRule.deleted_at.is_(None)
            )
        )
        for rule in existing_defaults.scalars().all():
            rule.is_default = False
    
    rule = VatRule(
        tenant_id=current_user.tenant_id,
        category=rule_data.category,
        merchant_pattern=rule_data.merchant_pattern,
        vat_rate=rule_data.vat_rate,
        vat_code=rule_data.vat_code,
        is_default=rule_data.is_default,
        effective_from=rule_data.effective_from,
        effective_to=rule_data.effective_to
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return VatRuleResponse.model_validate(rule)

@router.put("/vat-rules/{rule_id}", response_model=VatRuleResponse)
async def update_vat_rule(
    rule_id: str,
    rule_data: VatRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a VAT rule"""
    await require_admin_permission(current_user, db)
    
    result = await db.execute(
        select(VatRule).where(
            VatRule.id == uuid_lib.UUID(rule_id),
            VatRule.tenant_id == current_user.tenant_id,
            VatRule.deleted_at.is_(None)
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="VAT rule not found")
    
    # If setting as default, unset other defaults
    if rule_data.is_default is True:
        existing_defaults = await db.execute(
            select(VatRule).where(
                VatRule.tenant_id == current_user.tenant_id,
                VatRule.is_default == True,
                VatRule.id != rule.id,
                VatRule.deleted_at.is_(None)
            )
        )
        for existing_rule in existing_defaults.scalars().all():
            existing_rule.is_default = False
    
    if rule_data.category is not None:
        rule.category = rule_data.category
    if rule_data.merchant_pattern is not None:
        rule.merchant_pattern = rule_data.merchant_pattern
    if rule_data.vat_rate is not None:
        rule.vat_rate = rule_data.vat_rate
    if rule_data.vat_code is not None:
        rule.vat_code = rule_data.vat_code
    if rule_data.is_default is not None:
        rule.is_default = rule_data.is_default
    if rule_data.effective_from is not None:
        rule.effective_from = rule_data.effective_from
    if rule_data.effective_to is not None:
        rule.effective_to = rule_data.effective_to
    
    await db.commit()
    await db.refresh(rule)
    return VatRuleResponse.model_validate(rule)

@router.delete("/vat-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vat_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a VAT rule (soft delete)"""
    await require_admin_permission(current_user, db)
    
    result = await db.execute(
        select(VatRule).where(
            VatRule.id == uuid_lib.UUID(rule_id),
            VatRule.tenant_id == current_user.tenant_id,
            VatRule.deleted_at.is_(None)
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="VAT rule not found")
    
    from datetime import datetime
    rule.deleted_at = datetime.utcnow()
    await db.commit()

# Categories
@router.get("/categories", response_model=List[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all expense categories (read-only for any authenticated user, e.g. expense form dropdown).

    In development, if the categories table/schema is not ready, we return an empty list instead of a 500
    so that frontend UIs can still load.
    """
    try:
        result = await db.execute(
            select(ExpenseCategory).where(
                ExpenseCategory.tenant_id == current_user.tenant_id,
                ExpenseCategory.deleted_at.is_(None)
            ).order_by(ExpenseCategory.name)
        )
        categories = result.scalars().all()
        return [CategoryResponse.model_validate(c) for c in categories]
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("list_categories_failed", error=str(e))
        # Graceful fallback: no categories rather than hard 500
        return []

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new expense category"""
    await require_admin_permission(current_user, db)
    
    category = ExpenseCategory(
        tenant_id=current_user.tenant_id,
        name=category_data.name,
        code=category_data.code,
        description=category_data.description,
        gl_account_id=category_data.gl_account_id,
        parent_id=category_data.parent_id
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)

@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an expense category"""
    await require_admin_permission(current_user, db)
    
    result = await db.execute(
        select(ExpenseCategory).where(
            ExpenseCategory.id == uuid_lib.UUID(category_id),
            ExpenseCategory.tenant_id == current_user.tenant_id,
            ExpenseCategory.deleted_at.is_(None)
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category_data.name is not None:
        category.name = category_data.name
    if category_data.code is not None:
        category.code = category_data.code
    if category_data.description is not None:
        category.description = category_data.description
    if category_data.gl_account_id is not None:
        category.gl_account_id = category_data.gl_account_id
    if category_data.parent_id is not None:
        category.parent_id = category_data.parent_id
    if category_data.is_active is not None:
        category.is_active = category_data.is_active
    
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Soft-delete an expense category"""
    await require_admin_permission(current_user, db)

    result = await db.execute(
        select(ExpenseCategory).where(
            ExpenseCategory.id == uuid_lib.UUID(category_id),
            ExpenseCategory.tenant_id == current_user.tenant_id,
            ExpenseCategory.deleted_at.is_(None)
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.deleted_at = datetime.utcnow()
    await db.commit()


# GL Accounts
@router.get("/gl-accounts", response_model=List[GLAccountResponse])
async def list_gl_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all GL accounts.

    NOTE: This is intentionally readable by any authenticated user so that
    expense/category UIs can render GL mappings, while create/update/delete
    operations remain admin-only.
    """
    try:
        result = await db.execute(
            select(GLAccount).where(
                GLAccount.tenant_id == current_user.tenant_id,
                GLAccount.deleted_at.is_(None)
            ).order_by(GLAccount.account_code)
        )
        accounts = result.scalars().all()
        return [GLAccountResponse.model_validate(a) for a in accounts]
    except Exception as e:
        logger = structlog.get_logger()
        logger.error("list_gl_accounts_failed", error=str(e))
        # Graceful fallback: no GL accounts rather than hard 500
        return []

@router.post("/gl-accounts", response_model=GLAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_gl_account(
    account_data: GLAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new GL account"""
    await require_admin_permission(current_user, db)
    
    account = GLAccount(
        tenant_id=current_user.tenant_id,
        account_code=account_data.account_code,
        account_name=account_data.account_name,
        account_type=account_data.account_type,
        description=account_data.description,
        parent_account_id=account_data.parent_account_id
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return GLAccountResponse.model_validate(account)

# Policies (stats and violations before /policies/{id} to avoid path param capturing "stats"/"violations")
@router.get("/policy-stats")
async def get_policy_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Return expense counts for policy dashboard: total, compliant (no violations), with violations."""
    await require_admin_permission(current_user, db)
    tenant_id = current_user.tenant_id
    # Total expenses (submitted/approved/rejected, not draft; exclude deleted)
    total_q = select(func.count()).select_from(Expense).where(
        Expense.tenant_id == tenant_id,
        Expense.deleted_at.is_(None),
        Expense.status != "draft",
    )
    compliant_q = select(func.count()).select_from(Expense).where(
        Expense.tenant_id == tenant_id,
        Expense.deleted_at.is_(None),
        Expense.status != "draft",
        Expense.has_policy_violations == False,
    )
    violations_q = select(func.count()).select_from(Expense).where(
        Expense.tenant_id == tenant_id,
        Expense.deleted_at.is_(None),
        Expense.status != "draft",
        Expense.has_policy_violations == True,
    )
    total_r = await db.execute(total_q)
    compliant_r = await db.execute(compliant_q)
    violations_r = await db.execute(violations_q)
    total = total_r.scalar() or 0
    compliant = compliant_r.scalar() or 0
    violations = violations_r.scalar() or 0
    return {
        "total_expenses": total,
        "compliant_count": compliant,
        "violations_count": violations,
        "compliant_percent": round(100.0 * compliant / total, 1) if total else 0,
        "violations_percent": round(100.0 * violations / total, 1) if total else 0,
    }


@router.get("/policy-violations")
async def list_recent_policy_violations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """List recent policy violations with expense and policy details for the Policies dashboard."""
    await require_admin_permission(current_user, db)
    tenant_id = current_user.tenant_id
    # Join policy_violations -> expenses (tenant, amount, date, submitted_by) -> users (name), expense_policies (name)
    q = (
        select(
            PolicyViolation.id,
            PolicyViolation.expense_id,
            PolicyViolation.violation_message,
            PolicyViolation.violation_severity,
            PolicyViolation.created_at,
            Expense.amount,
            Expense.expense_date,
            ExpensePolicy.name.label("policy_name"),
            User.first_name,
            User.last_name,
        )
        .select_from(PolicyViolation)
        .join(Expense, PolicyViolation.expense_id == Expense.id)
        .join(ExpensePolicy, PolicyViolation.policy_id == ExpensePolicy.id)
        .join(User, Expense.submitted_by == User.id)
        .where(
            Expense.tenant_id == tenant_id,
            Expense.deleted_at.is_(None),
            PolicyViolation.is_resolved == False,
        )
        .order_by(PolicyViolation.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "id": str(r.id),
            "expense_id": str(r.expense_id),
            "date": r.expense_date.isoformat() if r.expense_date else None,
            "employee": f"{r.first_name or ''} {r.last_name or ''}".strip() or "Unknown",
            "policy": r.policy_name or "Policy",
            "violation": r.violation_message or "",
            "amount": float(r.amount) if r.amount is not None else 0,
            "severity": (r.violation_severity or "warning").capitalize(),
        }
        for r in rows
    ]


@router.get("/policies", response_model=List[PolicyResponse])
async def list_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all expense policies"""
    await require_admin_permission(current_user, db)
    
    result = await db.execute(
        select(ExpensePolicy).where(
            ExpensePolicy.tenant_id == current_user.tenant_id,
            ExpensePolicy.deleted_at.is_(None)
        ).order_by(ExpensePolicy.created_at.desc())
    )
    policies = result.scalars().all()
    return [PolicyResponse.model_validate(p) for p in policies]

@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new expense policy"""
    await require_admin_permission(current_user, db)
    
    policy = ExpensePolicy(
        tenant_id=current_user.tenant_id,
        name=policy_data.name,
        description=policy_data.description,
        policy_type=policy_data.policy_type,
        policy_rules=policy_data.policy_rules,
        applies_to_roles=[str(r) for r in policy_data.applies_to_roles],
        effective_from=policy_data.effective_from,
        effective_until=policy_data.effective_until,
        created_by=current_user.id
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return PolicyResponse.model_validate(policy)

@router.put("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    policy_data: PolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an expense policy"""
    await require_admin_permission(current_user, db)
    
    result = await db.execute(
        select(ExpensePolicy).where(
            ExpensePolicy.id == uuid_lib.UUID(policy_id),
            ExpensePolicy.tenant_id == current_user.tenant_id,
            ExpensePolicy.deleted_at.is_(None)
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if policy_data.name is not None:
        policy.name = policy_data.name
    if policy_data.description is not None:
        policy.description = policy_data.description
    if policy_data.policy_type is not None:
        policy.policy_type = policy_data.policy_type
    if policy_data.policy_rules is not None:
        policy.policy_rules = policy_data.policy_rules
    if policy_data.applies_to_roles is not None:
        policy.applies_to_roles = [str(r) for r in policy_data.applies_to_roles]
    if policy_data.is_active is not None:
        policy.is_active = policy_data.is_active
    if policy_data.effective_from is not None:
        policy.effective_from = policy_data.effective_from
    if policy_data.effective_until is not None:
        policy.effective_until = policy_data.effective_until
    
    await db.commit()
    await db.refresh(policy)
    return PolicyResponse.model_validate(policy)

@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an expense policy (soft delete)"""
    await require_admin_permission(current_user, db)
    
    result = await db.execute(
        select(ExpensePolicy).where(
            ExpensePolicy.id == uuid_lib.UUID(policy_id),
            ExpensePolicy.tenant_id == current_user.tenant_id,
            ExpensePolicy.deleted_at.is_(None)
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    from datetime import datetime
    policy.deleted_at = datetime.utcnow()
    await db.commit()

# Category Suggestion
@router.post("/categories/suggest", response_model=CategorySuggestionResponse)
async def suggest_category(
    request: CategorySuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Suggest expense category based on merchant, description, and amount"""
    service = CategorySuggestionService(db)
    return await service.suggest_category(request, str(current_user.tenant_id))

@router.get("/permissions")
async def list_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all permissions (for Roles & Permissions matrix)."""
    await require_admin_permission(current_user, db)

    from common.models import Permission as PermissionModel

    result = await db.execute(select(PermissionModel).order_by(PermissionModel.resource, PermissionModel.name))
    perms = result.scalars().all()
    return {
        "success": True,
        "data": {
            "permissions": [
                {"id": str(p.id), "name": p.name, "description": p.description or "", "resource": p.resource, "action": p.action}
                for p in perms
            ]
        }
    }


@router.get("/roles")
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List roles for the current tenant (for user management and role assignment). Includes permission_ids for matrix."""
    await require_admin_permission(current_user, db)

    from common.models import Role as RoleModel, UserRole, RolePermission as RolePermissionModel

    role_query = select(RoleModel).where(
        RoleModel.tenant_id == current_user.tenant_id,
        RoleModel.deleted_at.is_(None)
    )
    role_result = await db.execute(role_query)
    roles = role_result.scalars().all()

    # User count per role (only non-deleted users)
    from common.models import User as UserModel
    role_ids = [r.id for r in roles]
    user_count_subq = (
        select(UserRole.role_id, func.count(UserRole.user_id).label("cnt"))
        .join(UserModel, UserModel.id == UserRole.user_id)
        .where(
            UserRole.role_id.in_(role_ids),
            UserModel.deleted_at.is_(None),
        )
        .group_by(UserRole.role_id)
    )
    count_result = await db.execute(user_count_subq)
    count_map = {}
    for row in count_result.all():
        key = str(row.role_id)
        val = row.cnt
        count_map[key] = int(val) if val is not None else 0

    # Permission IDs per role
    rp_result = await db.execute(
        select(RolePermissionModel.role_id, RolePermissionModel.permission_id).where(
            RolePermissionModel.role_id.in_(role_ids)
        )
    )
    rp_rows = rp_result.all()
    perm_ids_by_role = {}
    for rid, pid in rp_rows:
        rid_str = str(rid)
        if rid_str not in perm_ids_by_role:
            perm_ids_by_role[rid_str] = []
        perm_ids_by_role[rid_str].append(str(pid))

    role_list = [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description or "",
            "is_system_role": r.is_system_role,
            "user_count": count_map.get(str(r.id), 0),
            "permission_ids": perm_ids_by_role.get(str(r.id), []),
        }
        for r in roles
    ]

    return {
        "success": True,
        "data": {"roles": role_list}
    }


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set permissions for a role. Body: { \"permission_ids\": [\"uuid\", ...] }. Replaces existing."""
    await require_admin_permission(current_user, db)

    from common.models import Role as RoleModel, RolePermission as RolePermissionModel

    role_uuid = uuid_lib.UUID(role_id)
    role_result = await db.execute(
        select(RoleModel).where(
            RoleModel.id == role_uuid,
            RoleModel.tenant_id == current_user.tenant_id,
            RoleModel.deleted_at.is_(None)
        )
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    try:
        body = await request.json()
    except Exception:
        body = {}
    permission_ids = body.get("permission_ids")
    if not isinstance(permission_ids, list):
        raise HTTPException(status_code=400, detail="permission_ids must be a list")

    from sqlalchemy import delete as sql_delete

    await db.execute(sql_delete(RolePermissionModel).where(RolePermissionModel.role_id == role_uuid))
    for pid in permission_ids:
        if not pid:
            continue
        try:
            perm_uuid = uuid_lib.UUID(pid)
        except (ValueError, TypeError):
            continue
        db.add(RolePermissionModel(role_id=role_uuid, permission_id=perm_uuid))

    await db.commit()

    from .models import UserManagementActivity
    role_name = role.name if role else ""
    db.add(UserManagementActivity(
        tenant_id=current_user.tenant_id,
        performed_by_id=current_user.id,
        action="role_permissions_updated",
        target_role_id=role_uuid,
        details={"role_name": role_name},
    ))
    await db.commit()

    return {"success": True, "data": {"role_id": role_id, "permission_ids": [str(p) for p in permission_ids if p]}}


async def _log_user_activity(
    db: AsyncSession,
    current_user: User,
    action: str,
    target_user_id=None,
    target_role_id=None,
    details=None,
):
    try:
        from .models import UserManagementActivity
        db.add(UserManagementActivity(
            tenant_id=current_user.tenant_id,
            performed_by_id=current_user.id,
            action=action,
            target_user_id=target_user_id,
            target_role_id=target_role_id,
            details=details or {},
        ))
        await db.flush()
    except Exception as e:
        logger.warning("activity_log_failed", action=action, error=str(e))


@router.get("/activity")
async def list_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent user management activity (Users & Roles Activity tab)."""
    await require_admin_permission(current_user, db)

    from .models import UserManagementActivity
    from common.models import User as UserModel, Role as RoleModel

    try:
        query = (
            select(UserManagementActivity)
            .where(UserManagementActivity.tenant_id == current_user.tenant_id)
            .order_by(UserManagementActivity.created_at.desc())
        )
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        activities = result.scalars().all()
    except Exception as e:
        # Table may not exist (e.g. old DB or stale image); asyncpg may raise different types
        logger.warning("activity_table_missing_or_error", error=str(e))
        return {
            "success": True,
            "data": {"activities": [], "total": 0, "page": page, "page_size": page_size},
        }

    performer_ids = list({a.performed_by_id for a in activities})
    target_user_ids = list({a.target_user_id for a in activities if a.target_user_id})
    role_ids = list({a.target_role_id for a in activities if a.target_role_id})

    performers = {}
    if performer_ids:
        p_result = await db.execute(
            select(UserModel.id, UserModel.email, UserModel.first_name, UserModel.last_name).where(
                UserModel.id.in_(performer_ids)
            )
        )
        for row in p_result.all():
            uid, email, fn, ln = row
            performers[str(uid)] = {"email": email, "name": f"{fn or ''} {ln or ''}".strip() or email}

    target_users = {}
    if target_user_ids:
        t_result = await db.execute(
            select(UserModel.id, UserModel.email, UserModel.first_name, UserModel.last_name).where(
                UserModel.id.in_(target_user_ids)
            )
        )
        for row in t_result.all():
            uid, email, fn, ln = row
            target_users[str(uid)] = {"email": email, "name": f"{fn or ''} {ln or ''}".strip() or email}

    role_names = {}
    if role_ids:
        r_result = await db.execute(select(RoleModel.id, RoleModel.name).where(RoleModel.id.in_(role_ids)))
        for row in r_result.all():
            role_names[str(row.id)] = row.name

    activity_list = []
    for a in activities:
        action_label = {
            "user_created": "User created",
            "user_updated": "User updated",
            "user_deleted": "User deleted",
            "user_status_changed": "User status changed",
            "role_permissions_updated": "Role permissions updated",
        }.get(a.action, a.action.replace("_", " ").title())
        performer = performers.get(str(a.performed_by_id), {})
        target_user = target_users.get(str(a.target_user_id), {}) if a.target_user_id else None
        role_name = role_names.get(str(a.target_role_id), "") if a.target_role_id else (a.details or {}).get("role_name", "")
        activity_list.append({
            "id": str(a.id),
            "action": a.action,
            "action_label": action_label,
            "performed_by_id": str(a.performed_by_id),
            "performed_by_email": performer.get("email", ""),
            "performed_by_name": performer.get("name", ""),
            "target_user_id": str(a.target_user_id) if a.target_user_id else None,
            "target_user_email": target_user.get("email", "") if target_user else None,
            "target_user_name": target_user.get("name", "") if target_user else None,
            "target_role_name": role_name,
            "details": a.details or {},
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return {
        "success": True,
        "data": {
            "activities": activity_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List users with roles. Optional filters: search (email/name), role_id, status."""
    await require_admin_permission(current_user, db)

    from common.models import User as UserModel, UserRole, Role as RoleModel

    query = select(UserModel).where(
        UserModel.tenant_id == current_user.tenant_id,
        UserModel.deleted_at.is_(None)
    )
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            (UserModel.email.ilike(term))
            | (UserModel.first_name.ilike(term))
            | (UserModel.last_name.ilike(term))
        )
    if status_filter and status_filter.lower() != "all":
        query = query.where(UserModel.status == status_filter)
    if role_id:
        subq = select(UserRole.user_id).where(UserRole.role_id == uuid_lib.UUID(role_id))
        query = query.where(UserModel.id.in_(subq))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(UserModel.email).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    user_ids = [u.id for u in users]

    # Load roles for these users
    ur_query = (
        select(UserRole.user_id, RoleModel.id, RoleModel.name)
        .join(RoleModel, RoleModel.id == UserRole.role_id)
        .where(UserRole.user_id.in_(user_ids), RoleModel.deleted_at.is_(None))
    )
    ur_result = await db.execute(ur_query)
    rows = ur_result.all()
    user_roles_map = {}
    for uid, rid, rname in rows:
        uid_str = str(uid)
        if uid_str not in user_roles_map:
            user_roles_map[uid_str] = []
        user_roles_map[uid_str].append({"id": str(rid), "name": rname})

    user_list = [
        {
            "id": str(u.id),
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "status": u.status,
            "roles": user_roles_map.get(str(u.id), []),
        }
        for u in users
    ]

    return {
        "success": True,
        "data": {
            "users": user_list,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single user with roles (for edit form)."""
    await require_admin_permission(current_user, db)

    from common.models import User as UserModel, UserRole, Role as RoleModel

    result = await db.execute(
        select(UserModel).where(
            UserModel.id == uuid_lib.UUID(user_id),
            UserModel.tenant_id == current_user.tenant_id,
            UserModel.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ur_result = await db.execute(
        select(RoleModel.id, RoleModel.name)
        .join(UserRole, UserRole.role_id == RoleModel.id)
        .where(UserRole.user_id == user.id, RoleModel.deleted_at.is_(None))
    )
    roles = [{"id": str(r.id), "name": r.name} for r in ur_result.all()]

    return {
        "success": True,
        "data": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "status": user.status,
            "roles": roles,
        }
    }

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user. Optional body: role_ids (list of UUIDs) to assign roles."""
    await require_admin_permission(current_user, db)

    from common.models import User as UserModel, UserRole, Role as RoleModel
    from services.auth.utils import get_password_hash

    # Check if user already exists
    result = await db.execute(
        select(UserModel).where(
            UserModel.email == user_data.get("email"),
            UserModel.tenant_id == current_user.tenant_id,
            UserModel.deleted_at.is_(None)
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_user = UserModel(
        id=uuid_lib.uuid4(),
        tenant_id=current_user.tenant_id,
        email=user_data.get("email"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        password_hash=get_password_hash(user_data.get("password", "password")),
        status=user_data.get("status", "active")
    )
    db.add(new_user)
    await db.flush()

    role_ids = user_data.get("role_ids") or []
    if role_ids:
        # Validate roles belong to tenant
        role_result = await db.execute(
            select(RoleModel.id).where(
                RoleModel.id.in_([uuid_lib.UUID(r) for r in role_ids if r]),
                RoleModel.tenant_id == current_user.tenant_id,
                RoleModel.deleted_at.is_(None)
            )
        )
        valid_role_ids = list(role_result.scalars().all())
        for rid in valid_role_ids:
            db.add(UserRole(user_id=new_user.id, role_id=rid, assigned_by=current_user.id))

    await db.commit()
    await db.refresh(new_user)

    await _log_user_activity(
        db, current_user, "user_created",
        target_user_id=new_user.id,
        details={"email": new_user.email, "first_name": new_user.first_name, "last_name": new_user.last_name},
    )
    await db.commit()

    # Load roles for response
    ur_result = await db.execute(
        select(RoleModel.id, RoleModel.name)
        .join(UserRole, UserRole.role_id == RoleModel.id)
        .where(UserRole.user_id == new_user.id)
    )
    roles = [{"id": str(r.id), "name": r.name} for r in ur_result.all()]

    return {
        "success": True,
        "data": {
            "id": str(new_user.id),
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "status": new_user.status,
            "roles": roles,
        }
    }

@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a user. Optional body: role_ids (list of UUIDs) to replace assigned roles."""
    await require_admin_permission(current_user, db)

    from common.models import User as UserModel, UserRole, Role as RoleModel
    from services.auth.utils import get_password_hash
    from sqlalchemy import delete as sql_delete

    result = await db.execute(
        select(UserModel).where(
            UserModel.id == uuid_lib.UUID(user_id),
            UserModel.tenant_id == current_user.tenant_id,
            UserModel.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "email" in user_data:
        email_result = await db.execute(
            select(UserModel).where(
                UserModel.email == user_data["email"],
                UserModel.id != user.id,
                UserModel.tenant_id == current_user.tenant_id,
                UserModel.deleted_at.is_(None)
            )
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_data["email"]

    if "first_name" in user_data:
        user.first_name = user_data["first_name"]
    if "last_name" in user_data:
        user.last_name = user_data["last_name"]
    if "status" in user_data:
        user.status = user_data["status"]
    if "password" in user_data and user_data["password"]:
        user.password_hash = get_password_hash(user_data["password"])

    if "role_ids" in user_data:
        await db.execute(sql_delete(UserRole).where(UserRole.user_id == user.id))
        role_ids = user_data.get("role_ids") or []
        if role_ids:
            role_result = await db.execute(
                select(RoleModel.id).where(
                    RoleModel.id.in_([uuid_lib.UUID(r) for r in role_ids if r]),
                    RoleModel.tenant_id == current_user.tenant_id,
                    RoleModel.deleted_at.is_(None)
                )
            )
            for rid in role_result.scalars().all():
                db.add(UserRole(user_id=user.id, role_id=rid, assigned_by=current_user.id))

    await db.commit()
    await db.refresh(user)

    action_type = "user_status_changed" if set(user_data.keys()) <= {"status"} else "user_updated"
    await _log_user_activity(
        db, current_user, action_type,
        target_user_id=user.id,
        details={"email": user.email, "status": user.status},
    )
    await db.commit()

    ur_result = await db.execute(
        select(RoleModel.id, RoleModel.name)
        .join(UserRole, UserRole.role_id == RoleModel.id)
        .where(UserRole.user_id == user.id)
    )
    roles = [{"id": str(r.id), "name": r.name} for r in ur_result.all()]

    return {
        "success": True,
        "data": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "status": user.status,
            "roles": roles,
        }
    }

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (soft delete)"""
    await require_admin_permission(current_user, db)
    
    from common.models import User as UserModel
    
    result = await db.execute(
        select(UserModel).where(
            UserModel.id == uuid_lib.UUID(user_id),
            UserModel.tenant_id == current_user.tenant_id,
            UserModel.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await _log_user_activity(
        db, current_user, "user_deleted",
        target_user_id=user.id,
        details={"email": user.email},
    )

    from datetime import datetime
    user.deleted_at = datetime.utcnow()
    user.status = "inactive"
    await db.commit()


# -----------------------------------------------------------------------------
# Company Settings (Settings page backend)
# -----------------------------------------------------------------------------

def _default_settings():
    """Default settings structure matching the frontend form."""
    return {
        "general": {
            "company_name": "Dou France SAS",
            "company_address": "123 Rue de la République, 75001 Paris, France",
            "tax_id_siret": "123 456 789 00012",
            "vat_number": "FR12 345678901",
            "default_currency": "EUR",
        },
        "users": {
            "default_user_role": "employee",
            "require_email_verification": True,
        },
        "security": {
            "two_factor_enabled": True,
            "session_timeout_minutes": 30,
        },
        "notifications": {
            "email_approvals": True,
            "push_mobile": True,
        },
        "billing": {
            "billing_email": "billing@company.com",
            "plan": "Professional",
            "plan_details": "€99/month • 50 users",
        },
    }


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get company settings for the current tenant."""
    await require_admin_permission(current_user, db)
    result = await db.execute(
        select(TenantSettings).where(TenantSettings.tenant_id == current_user.tenant_id)
    )
    row = result.scalar_one_or_none()
    defaults = _default_settings()
    if not row or not row.settings:
        return SettingsResponse(settings=defaults, updated_at=None)
    # Merge with defaults so frontend always gets full shape (general, users, security, notifications, billing)
    merged = dict(defaults)
    for section, data in (row.settings or {}).items():
        if isinstance(data, dict) and section in merged and isinstance(merged[section], dict):
            merged[section] = {**merged[section], **data}
        else:
            merged[section] = data
    return SettingsResponse(settings=merged, updated_at=row.updated_at)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    payload: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update company settings. Records changelog per section."""
    await require_admin_permission(current_user, db)
    from datetime import datetime

    result = await db.execute(
        select(TenantSettings).where(TenantSettings.tenant_id == current_user.tenant_id)
    )
    row = result.scalar_one_or_none()
    defaults = _default_settings()
    if not row:
        row = TenantSettings(
            tenant_id=current_user.tenant_id,
            settings=defaults,
        )
        db.add(row)
        await db.flush()

    current = dict(row.settings) if row.settings else {}
    for section in ("general", "users", "security", "notifications", "billing"):
        new_val = getattr(payload, section)
        if new_val is None:
            continue
        old_val = current.get(section)
        current[section] = new_val
        # Changelog only when section actually changed
        if old_val != new_val:
            log = SettingsChangelog(
                tenant_id=current_user.tenant_id,
                changed_by=current_user.id,
                section=section,
                action="update",
                old_value=old_val,
                new_value=new_val,
            )
            db.add(log)
    row.settings = current
    row.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(row)
    return SettingsResponse(settings=dict(row.settings), updated_at=row.updated_at)


@router.get("/settings/changelog", response_model=List[ChangelogEntryResponse])
async def get_settings_changelog(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get settings change log for the current tenant."""
    await require_admin_permission(current_user, db)
    from common.models import User as UserModel
    sub = (
        select(SettingsChangelog)
        .where(SettingsChangelog.tenant_id == current_user.tenant_id)
        .order_by(SettingsChangelog.changed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(sub)
    entries = result.scalars().all()
    out = []
    for e in entries:
        user_result = await db.execute(
            select(UserModel.email).where(UserModel.id == e.changed_by)
        )
        email_val = user_result.scalar_one_or_none()
        out.append(
            ChangelogEntryResponse(
                id=e.id,
                changed_at=e.changed_at,
                section=e.section,
                action=e.action,
                changed_by_email=email_val,
                old_value=e.old_value,
                new_value=e.new_value,
            )
        )
    return out