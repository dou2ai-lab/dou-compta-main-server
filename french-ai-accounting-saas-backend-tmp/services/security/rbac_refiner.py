# -----------------------------------------------------------------------------
# File: rbac_refiner.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Role-based access control refinements
# -----------------------------------------------------------------------------

"""
RBAC Refinements
Enhanced role-based access control with fine-grained permissions
"""
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import structlog

from common.models import User, Role, Permission, UserRole, RolePermission
from common.roles import has_admin_role
from services.security.audit_logger import SecurityAuditLogger

logger = structlog.get_logger()

class RBACRefiner:
    """RBAC refinement service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.audit_logger = SecurityAuditLogger(db, tenant_id)
    
    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has permission for resource and action"""
        try:
            # Get user roles (join via Role; UserRole has no tenant_id)
            user_roles_result = await self.db.execute(
                select(Role.name)
                .select_from(UserRole)
                .join(Role, UserRole.role_id == Role.id)
                .where(
                    and_(
                        UserRole.user_id == user_id,
                        Role.tenant_id == self.tenant_id,
                        Role.deleted_at.is_(None)
                    )
                )
            )
            user_roles = list(user_roles_result.scalars().all())

            # Admin has all permissions
            if has_admin_role(user_roles):
                return True

            # Check permissions for each role
            for role_name in user_roles:
                if await self._role_has_permission(role_name, resource, action, context):
                    return True
            
            # Log permission denied
            await self.audit_logger.log_permission_denied(
                user_id=user_id,
                resource=resource,
                action=action
            )
            
            return False
            
        except Exception as e:
            logger.error("check_permission_error", error=str(e))
            return False
    
    async def _role_has_permission(
        self,
        role_name: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if role has specific permission"""
        try:
            # Get role permissions
            result = await self.db.execute(
                select(Permission.name).join(RolePermission).join(Role).where(
                    and_(
                        Role.name == role_name,
                        Role.tenant_id == self.tenant_id,
                        Permission.name.like(f"{resource}:{action}%")
                    )
                )
            )
            permissions = list(result.scalars().all())
            
            # Check exact match or wildcard
            exact_permission = f"{resource}:{action}"
            wildcard_permission = f"{resource}:*"
            
            return exact_permission in permissions or wildcard_permission in permissions
            
        except Exception as e:
            logger.error("role_has_permission_error", error=str(e))
            return False
    
    async def get_user_permissions(
        self,
        user_id: str
    ) -> Set[str]:
        """Get all permissions for user"""
        try:
            # Get user roles (join via Role; UserRole has no tenant_id)
            user_roles_result = await self.db.execute(
                select(Role.name)
                .select_from(UserRole)
                .join(Role, UserRole.role_id == Role.id)
                .where(
                    and_(
                        UserRole.user_id == user_id,
                        Role.tenant_id == self.tenant_id,
                        Role.deleted_at.is_(None)
                    )
                )
            )
            user_roles = list(user_roles_result.scalars().all())

            # Admin has all permissions
            if has_admin_role(user_roles):
                return {"*:*"}  # Wildcard for all permissions
            
            # Get permissions for all roles
            all_permissions = set()
            for role_name in user_roles:
                result = await self.db.execute(
                    select(Permission.name).join(RolePermission).join(Role).where(
                        and_(
                            Role.name == role_name,
                            Role.tenant_id == self.tenant_id
                        )
                    )
                )
                permissions = set(result.scalars().all())
                all_permissions.update(permissions)
            
            return all_permissions
            
        except Exception as e:
            logger.error("get_user_permissions_error", error=str(e))
            return set()
    
    async def enforce_tenant_isolation(
        self,
        user_id: str,
        resource_tenant_id: str
    ) -> bool:
        """Enforce tenant isolation - user can only access their tenant's resources"""
        try:
            result = await self.db.execute(
                select(User.tenant_id).where(User.id == user_id)
            )
            user_tenant = result.scalar_one()
            
            return user_tenant == resource_tenant_id
            
        except Exception as e:
            logger.error("enforce_tenant_isolation_error", error=str(e))
            return False
    
    async def check_resource_ownership(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        ownership_field: str = "submitted_by"
    ) -> bool:
        """Check if user owns the resource"""
        try:
            # Get user roles (join via Role; UserRole has no tenant_id)
            user_roles_result = await self.db.execute(
                select(Role.name)
                .select_from(UserRole)
                .join(Role, UserRole.role_id == Role.id)
                .where(
                    and_(
                        UserRole.user_id == user_id,
                        Role.tenant_id == self.tenant_id,
                        Role.deleted_at.is_(None)
                    )
                )
            )
            user_roles = list(user_roles_result.scalars().all())

            # Admin can access all resources
            if has_admin_role(user_roles):
                return True

            # Check ownership based on resource type
            if resource_type == "expense":
                from common.models import Expense
                result = await self.db.execute(
                    select(Expense).where(
                        and_(
                            Expense.id == resource_id,
                            Expense.tenant_id == self.tenant_id
                        )
                    )
                )
                expense = result.scalar_one_or_none()
                if expense:
                    return getattr(expense, ownership_field) == user_id
            
            elif resource_type == "receipt":
                from common.models import Receipt
                result = await self.db.execute(
                    select(Receipt).where(
                        and_(
                            Receipt.id == resource_id,
                            Receipt.tenant_id == self.tenant_id
                        )
                    )
                )
                receipt = result.scalar_one_or_none()
                if receipt:
                    return getattr(receipt, ownership_field) == user_id
            
            return False
            
        except Exception as e:
            logger.error("check_resource_ownership_error", error=str(e))
            return False

