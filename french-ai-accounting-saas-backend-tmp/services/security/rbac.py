"""
Centralized RBAC helpers.

Backend-first authorization:
- admin => full access
- approver/finance => approve + view approvals
- manager relationship (users.manager_id) => approve direct reports
- user => own data only
"""

from __future__ import annotations

from typing import Optional, Sequence

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from common.models import User
from common.roles import is_admin, can_approve, can_view_approvals
from services.auth.dependencies import get_user_roles

logger = structlog.get_logger()


def _roles_debug(roles: Sequence[str] | None) -> list[str]:
    if not roles:
        return []
    return [str(r) for r in roles if r is not None]


def _not_authorized(endpoint: str, user_id: str, roles: Sequence[str]) -> HTTPException:
    # Keep error details consistent for the frontend.
    logger.warning(
        "rbac_denied",
        user_id=str(user_id),
        roles=_roles_debug(roles),
        endpoint=endpoint,
    )
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


async def require_admin(user: User, db: AsyncSession, *, endpoint: str) -> list[str]:
    """
    Require admin role.
    Admin role is the top-level role for sensitive admin endpoints.
    """
    roles = await get_user_roles(user, db)
    if is_admin(roles):
        return roles
    raise _not_authorized(endpoint=endpoint, user_id=str(user.id), roles=roles)


async def require_approver(user: User, db: AsyncSession, *, endpoint: str) -> list[str]:
    """Require permission to approve (admin/approver/finance roles)."""
    roles = await get_user_roles(user, db)
    if can_approve(roles) and can_view_approvals(roles):
        return roles
    raise _not_authorized(endpoint=endpoint, user_id=str(user.id), roles=roles)


async def require_approval_access(
    user: User,
    db: AsyncSession,
    resource_owner_user_id,
    *,
    endpoint: str,
    allow_owner: bool = True,
):
    """
    Require authorization for approval/view flows around a resource owned by another user.

    - user can approve/view if they have approver/finance/admin roles
    - OR if they are manager of the resource owner (resource_owner.manager_id == user.id)
    - OR (optionally) if they are the owner themselves (allow_owner=True)
    """
    roles = await get_user_roles(user, db)
    if can_view_approvals(roles) and can_approve(roles):
        return roles

    # "user can only see/act on their own data"
    if allow_owner and resource_owner_user_id == user.id:
        return roles

    # Manager relationship is derived from users.manager_id.
    owner_q = (
        select(User)
        .where(
            User.id == resource_owner_user_id,
            User.tenant_id == user.tenant_id,
            User.deleted_at.is_(None),
        )
    )
    owner = (await db.execute(owner_q)).scalar_one_or_none()
    if owner and owner.manager_id == user.id:
        return roles

    raise _not_authorized(endpoint=endpoint, user_id=str(user.id), roles=roles)

