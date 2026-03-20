# -----------------------------------------------------------------------------
# File: dependencies.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: FastAPI dependencies for authentication service
# -----------------------------------------------------------------------------

"""
Authentication dependencies
"""
import os
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
import structlog

from common.database import get_db
from common.models import User, Tenant
from .utils import decode_token

logger = structlog.get_logger()
security = HTTPBearer()

# Dev-only: UUIDs for mock user when DB is unreachable from host
DEV_MOCK_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
DEV_MOCK_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    # Development mode: Accept mock tokens or bypass invalid tokens for local testing
    if token.startswith("dev_mock_token") or token == "mock_token":
        # Never allow dev auth bypass outside development.
        if env != "development":
            logger.warning("dev_mock_token_rejected", token_prefix=token[:10], env=env)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info("dev_mode_auth", message="Using development mock authentication")
        try:
            # Get or create a development user
            result = await db.execute(
                select(User).where(User.email == "dev@dou.fr").limit(1)
            )
            user = result.scalar_one_or_none()
        except (OperationalError, Exception) as e:
            # DB unreachable (e.g. password auth failed from host) - return mock user
            if "password" in str(e).lower() or "connection" in str(e).lower() or "connect" in str(e).lower():
                logger.warning("dev_mock_no_db", message="DB unreachable, using mock user. Run RAG in Docker for full functionality.")
                user = User(
                    id=DEV_MOCK_USER_ID,
                    email="dev@dou.fr",
                    first_name="Development",
                    last_name="User",
                    status="active",
                    tenant_id=DEV_MOCK_TENANT_ID,
                )
                user._dev_mock_no_db = True  # type: ignore
                return user
            raise
        
        if not user:
            # Get the first tenant for the dev user
            tenant_result = await db.execute(select(Tenant).limit(1))
            tenant = tenant_result.scalar_one_or_none()
            if not tenant:
                # Create a default tenant if none exists
                # IMPORTANT: Tenant.slug is non-nullable and unique, so we must provide it.
                tenant = Tenant(
                    name="Development Tenant",
                    slug="dev-tenant",
                    status="active",
                )
                db.add(tenant)
                await db.flush()
                logger.info("default_tenant_created", tenant_id=str(tenant.id))

            user = User(
                email="dev@dou.fr",
                first_name="Development",
                last_name="User",
                status="active",
                tenant_id=tenant.id  # Assign the tenant_id here
            )
            db.add(user)
            await db.flush()
            logger.info("dev_user_created", user_id=str(user.id), tenant_id=str(user.tenant_id))
        
        return user
    
    # Production mode: Validate JWT
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        logger.warning("invalid_token", token_prefix=token[:10])
        # In strict/production mode, reject invalid tokens
        if env == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # In development, fall back to dev mock user so local frontend works even with bad tokens
        logger.info("dev_mode_auth_fallback", message="Using dev mock user due to invalid token in development")
        try:
            result = await db.execute(
                select(User).where(User.email == "dev@dou.fr").limit(1)
            )
            user = result.scalar_one_or_none()
        except (OperationalError, Exception) as e:
            if "password" in str(e).lower() or "connection" in str(e).lower() or "connect" in str(e).lower():
                logger.warning("dev_mock_no_db", message="DB unreachable, using mock user. Run services in Docker for full functionality.")
                user = User(
                    id=DEV_MOCK_USER_ID,
                    email="dev@dou.fr",
                    first_name="Development",
                    last_name="User",
                    status="active",
                    tenant_id=DEV_MOCK_TENANT_ID,
                )
                user._dev_mock_no_db = True  # type: ignore
                return user
            raise

        if not user:
            tenant_result = await db.execute(select(Tenant).limit(1))
            tenant = tenant_result.scalar_one_or_none()
            if not tenant:
                tenant = Tenant(
                    name="Development Tenant",
                    slug="dev-tenant",
                    status="active",
                )
                db.add(tenant)
                await db.flush()
                logger.info("default_tenant_created", tenant_id=str(tenant.id))

            user = User(
                email="dev@dou.fr",
                first_name="Development",
                last_name="User",
                status="active",
                tenant_id=tenant.id,
            )
            db.add(user)
            await db.flush()
            logger.info("dev_user_created", user_id=str(user.id), tenant_id=str(user.tenant_id))

        return user
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning("user_not_found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user

def _role_name(r) -> str:
    """Extract role name from DB row (Row or scalar)."""
    if r is None:
        return ""
    if isinstance(r, str):
        return r
    if hasattr(r, "__getitem__"):
        return str(r[0]) if r else ""
    return str(r)


async def get_user_roles(user: User, db: AsyncSession) -> list[str]:
    """Get user roles as list of role name strings."""
    from common.models import UserRole, Role

    result = await db.execute(
        select(Role.name)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user.id)
    )
    rows = result.all()
    return [_role_name(r) for r in rows]

async def get_user_permissions(user: User, db: AsyncSession) -> list[str]:
    """Get user permissions based on roles. Dev user and Admin role get full permissions including audit."""
    if getattr(user, "email", None) == "dev@dou.fr":
        return [
            "audit:read", "audit:write", "expense:read", "expense:create", "expense:update",
            "admin:read", "user:read", "user:write",
        ]
    from common.models import UserRole, Role, RolePermission, Permission

    result = await db.execute(
        select(Permission.name)
        .join(RolePermission, Permission.id == RolePermission.permission_id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user.id)
        .distinct()
    )
    rows = result.all()
    def _perm_name(p):
        if p is None:
            return ""
        if isinstance(p, str):
            return p
        if hasattr(p, "__getitem__"):
            return str(p[0]) if p else ""
        return str(p)
    permissions = [_perm_name(r) for r in rows]
    # Ensure Admin role always has audit access (in case role_permissions were missing)
    roles = await get_user_roles(user, db)
    if roles and any(_role_name(r).lower() == "admin" for r in roles):
        for p in ["audit:read", "audit:write", "admin:read", "admin:write",
                   "expense:read", "expense:create", "expense:update", "expense:approve",
                   "user:read", "user:write", "report:read", "report:write"]:
            if p not in permissions:
                permissions.append(p)
    return permissions
