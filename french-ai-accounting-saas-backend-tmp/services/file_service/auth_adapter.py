# -----------------------------------------------------------------------------
# Accept JWTs from Node auth service so the frontend (logged in via Node) can
# upload receipts without 401. Uses config.get_node_jwt_secret() (runtime + file).
# -----------------------------------------------------------------------------
from typing import Optional
import uuid
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_node_jwt_secret
from common.database import get_db

logger = structlog.get_logger()
security = HTTPBearer(auto_error=False)


class NodeAuthUser:
    """Minimal user-like object from Node JWT (id + tenant_id only)."""
    __slots__ = ("id", "tenant_id")
    def __init__(self, id: uuid.UUID, tenant_id: uuid.UUID):
        self.id = id
        self.tenant_id = tenant_id


def _decode_node_jwt(token: str) -> Optional[dict]:
    """Decode and verify JWT signed by Node auth service. Returns payload or None."""
    secret = get_node_jwt_secret()
    if not secret:
        logger.debug("node_jwt_skipped", reason="No Node JWT secret (settings/env/auth-service-node/.env)")
        return None
    # Prefer PyJWT for better compatibility with Node's jsonwebtoken
    for lib in ("pyjwt", "jose"):
        try:
            if lib == "pyjwt":
                import jwt as pyjwt
                payload = pyjwt.decode(
                    token,
                    secret,
                    algorithms=["HS256"],
                    options={"verify_exp": True},
                )
            else:
                from jose import jwt as jose_jwt
                from jose import JWTError
                payload = jose_jwt.decode(token, secret, algorithms=["HS256"])
            if payload.get("type") != "access":
                return None
            return payload
        except Exception as e:
            logger.debug("node_jwt_decode_failed", library=lib, error=str(e))
            continue
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Resolve current user: try Node JWT first (if NODE_JWT_SECRET set), then Python auth.
    File service only needs user id and tenant_id; Node JWT provides these without DB lookup.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials

    # 1) Try Node JWT (frontend logged in via auth-service-node)
    payload = _decode_node_jwt(token)
    if payload:
        sub = payload.get("sub")
        tenant_id_raw = payload.get("tenantId") or payload.get("tenant_id")
        if sub and tenant_id_raw:
            try:
                return NodeAuthUser(
                    id=uuid.UUID(sub),
                    tenant_id=uuid.UUID(tenant_id_raw),
                )
            except (ValueError, TypeError):
                pass

    # 2) Fall back to Python auth (decode with Python secret, lookup user in Python DB)
    from services.auth.utils import decode_token
    from common.models import User

    py_payload = decode_token(token)
    if not py_payload or py_payload.get("type") != "access":
        hint = ""
        if not get_node_jwt_secret():
            hint = " File Service could not verify your token. Ensure auth-service-node/.env exists with JWT_SECRET and restart the File Service (port 8005)."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token." + hint,
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = py_payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = uuid.UUID(sub) if isinstance(sub, str) else sub
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
