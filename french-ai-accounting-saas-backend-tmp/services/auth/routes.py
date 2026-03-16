# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Authentication service routes
# -----------------------------------------------------------------------------

"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import os
import secrets
from urllib.parse import urlencode

import httpx
import structlog

from common.database import get_db
from common.models import User, Tenant
from .models import (
    LoginRequest, LoginResponse, TokenResponse, RefreshTokenRequest,
    UserResponse, LogoutResponse, PermissionsResponse, SignupRequest, SignupResponse
)
from .utils import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token
)
from .dependencies import get_current_user, get_user_permissions, get_user_roles

logger = structlog.get_logger()
router = APIRouter()


def _get_oauth_frontend_url() -> str:
    return os.getenv("FRONTEND_APP_URL", "http://localhost:3000").rstrip("/")


def _get_google_oauth_config() -> dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth is not configured on the server (missing env vars).",
        )
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid email profile",
    }


def _normalize_provider(raw: str) -> str:
    value = raw.lower()
    if value == "google":
        return "google"
    if value in {"microsoft", "azure", "azuread", "azure-ad"}:
        return "microsoft"
    if value == "okta":
        return "okta"
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported OAuth provider")

@router.post("/signup", response_model=SignupResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    Creates a new user in the default tenant and assigns Employee role
    """
    try:
        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == request.email, User.deleted_at.is_(None))
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning("signup_failed", email=request.email, reason="user_already_exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Get or create default tenant
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.slug == "default", Tenant.deleted_at.is_(None))
        )
        tenant = tenant_result.scalar_one_or_none()
        
        if not tenant:
            # Create default tenant if it doesn't exist
            import uuid
            tenant = Tenant(
                id=uuid.uuid4(),
                name="Default Tenant",
                slug="default",
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(tenant)
            await db.flush()
            logger.info("default_tenant_created", tenant_id=str(tenant.id))
        
        # Validate password strength
        if len(request.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Hash password
        password_hash = get_password_hash(request.password)
        
        # Create new user
        import uuid
        new_user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password_hash=password_hash,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(new_user)
        await db.flush()
        
        # Assign Employee role to new user (if it exists)
        from common.models import Role, UserRole
        try:
            from common.roles import DEFAULT_SIGNUP_ROLE
            role_result = await db.execute(
                select(Role).where(
                    Role.tenant_id == tenant.id,
                    Role.name == DEFAULT_SIGNUP_ROLE,
                    Role.deleted_at.is_(None)
                )
            )
            employee_role = role_result.scalar_one_or_none()

            if employee_role:
                # UserRole uses composite primary key (user_id, role_id), no id or tenant_id fields
                user_role = UserRole(
                    user_id=new_user.id,
                    role_id=employee_role.id
                    # assigned_at is set automatically by default
                    # assigned_by can be None for self-registration
                )
                db.add(user_role)
                await db.flush()
                logger.info("employee_role_assigned", user_id=str(new_user.id), role_id=str(employee_role.id))
            else:
                logger.warning("employee_role_not_found", tenant_id=str(tenant.id), message="User created without role - can be assigned later")
        except Exception as role_error:
            # Log but don't fail signup if role assignment fails
            logger.error("role_assignment_failed", error=str(role_error), user_id=str(new_user.id), exc_info=True)
        
        await db.commit()
        
        # Get user roles and permissions
        roles = await get_user_roles(new_user, db)
        permissions = await get_user_permissions(new_user, db)
        
        # Create tokens (auto-login after signup)
        token_data = {
            "sub": str(new_user.id),
            "email": new_user.email,
            "tenant_id": str(new_user.tenant_id),
            "roles": roles
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info("signup_success", user_id=str(new_user.id), email=new_user.email)
        
        return SignupResponse(
            success=True,
            data={
                "token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": str(new_user.id),
                    "email": new_user.email,
                    "first_name": new_user.first_name,
                    "last_name": new_user.last_name,
                    "tenant_id": str(new_user.tenant_id),
                    "roles": roles,
                    "permissions": permissions
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        logger.error("signup_error", error=error_msg, error_type=error_type, exc_info=True)
        await db.rollback()
        
        # In development, return more detailed error info
        import os
        env = os.getenv("ENVIRONMENT", "development")
        if env == "development":
            detail = f"Signup failed: {error_type}: {error_msg}"
        else:
            detail = "Signup failed. Please try again."
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/oauth/{provider}/start")
async def oauth_start(provider: str, request: Request):
    """
    Start OAuth flow (currently implemented for Google).

    Redirects the browser to the provider's authorization page and stores a short-lived
    state cookie (`oauth_state`) for CSRF protection.
    """
    normalized = _normalize_provider(provider)
    if normalized != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{normalized}' is not yet enabled on this environment.",
        )

    cfg = _get_google_oauth_config()

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": cfg["scope"],
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f'{cfg["auth_url"]}?{urlencode(params)}'

    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    # CSRF/state cookie – HTTP-only so JS can't touch it
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=600,
        path="/",
    )

    logger.info("oauth_start", provider=normalized, redirect=cfg["auth_url"])
    return response


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    OAuth callback handler.

    Exchanges auth code for tokens, fetches user info, then:
    - finds or creates a local user by email
    - issues our own JWT access/refresh tokens
    - sets them as cookies
    - redirects back to the frontend app
    """
    normalized = _normalize_provider(provider)
    if normalized != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{normalized}' is not yet enabled on this environment.",
        )

    cfg = _get_google_oauth_config()

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    cookie_state = request.cookies.get("oauth_state")

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing authorization code")
    if not state or not cookie_state or state != cookie_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                cfg["token_url"],
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": cfg["redirect_uri"],
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if token_resp.status_code != 200:
            logger.error("oauth_token_error", provider=normalized, status=token_resp.status_code, body=token_resp.text)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange OAuth code")

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth provider did not return access token")

        async with httpx.AsyncClient(timeout=15.0) as client:
            userinfo_resp = await client.get(
                cfg["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if userinfo_resp.status_code != 200:
            logger.error("oauth_userinfo_error", provider=normalized, status=userinfo_resp.status_code, body=userinfo_resp.text)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to fetch user profile from provider")

        profile = userinfo_resp.json()
        email = (profile.get("email") or "").strip().lower()
        first_name = profile.get("given_name")
        last_name = profile.get("family_name")
        subject = profile.get("sub")

        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth provider did not return an email address")

        # Find or create user in our DB, similar to /signup + /login
        from uuid import uuid4
        from common.models import User, Tenant, Role, UserRole
        from common.roles import DEFAULT_SIGNUP_ROLE

        # Look up user by email
        user_result = await db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        user = user_result.scalar_one_or_none()

        if not user:
            # Get or create default tenant
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.slug == "default", Tenant.deleted_at.is_(None))
            )
            tenant = tenant_result.scalar_one_or_none()
            if not tenant:
                tenant = Tenant(
                    id=uuid4(),
                    name="Default Tenant",
                    slug="default",
                    status="active",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(tenant)
                await db.flush()
                logger.info("default_tenant_created_oauth", tenant_id=str(tenant.id))

            user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                # No local password for SSO users
                password_hash=None,
                sso_provider=normalized,
                sso_subject_id=subject,
                status="active",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(user)
            await db.flush()

            # Assign default signup role if it exists
            try:
                role_result = await db.execute(
                    select(Role).where(
                        Role.tenant_id == tenant.id,
                        Role.name == DEFAULT_SIGNUP_ROLE,
                        Role.deleted_at.is_(None),
                    )
                )
                employee_role = role_result.scalar_one_or_none()
                if employee_role:
                    user_role = UserRole(
                        user_id=user.id,
                        role_id=employee_role.id,
                    )
                    db.add(user_role)
                    await db.flush()
                    logger.info("oauth_employee_role_assigned", user_id=str(user.id), role_id=str(employee_role.id))
                else:
                    logger.warning("oauth_employee_role_not_found", tenant_id=str(tenant.id))
            except Exception as role_error:
                logger.error("oauth_role_assignment_failed", error=str(role_error), user_id=str(user.id), exc_info=True)

            await db.commit()
            logger.info("oauth_user_created", provider=normalized, user_id=str(user.id), email=user.email)
        else:
            # Ensure tenant and user are active
            tenant_result = await db.execute(
                select(Tenant).where(Tenant.id == user.tenant_id, Tenant.deleted_at.is_(None))
            )
            tenant = tenant_result.scalar_one_or_none()
            if not tenant:
                logger.error("oauth_tenant_not_found", user_id=str(user.id), tenant_id=str(user.tenant_id))
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User tenant not found")

            if user.status != "active":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
            if tenant.status != "active":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant account is inactive")

        # Update last login
        try:
            user.last_login_at = datetime.utcnow()
            await db.commit()
        except Exception as update_error:
            logger.warning("oauth_last_login_update_failed", user_id=str(user.id), error=str(update_error))
            try:
                await db.rollback()
            except Exception:
                pass

        # Get roles and permissions
        roles = await get_user_roles(user, db)
        permissions = await get_user_permissions(user, db)

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "roles": roles,
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        frontend_url = _get_oauth_frontend_url()
        redirect_url = f"{frontend_url}/"

        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        # Clear state cookie
        response.delete_cookie("oauth_state", path="/")

        # Match frontend semantics: token & refresh_token cookies (non-HttpOnly, SameSite=Lax)
        # so the React app can read them if needed. In production you may want HttpOnly.
        response.set_cookie(
            key="token",
            value=access_token,
            httponly=False,
            samesite="lax",
            secure=False,
            max_age=30 * 60,
            path="/",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=False,
            samesite="lax",
            secure=False,
            max_age=7 * 24 * 60 * 60,
            path="/",
        )

        logger.info("oauth_login_success", provider=normalized, user_id=str(user.id), email=user.email)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error("oauth_callback_error", provider=normalized, error=str(e), exc_info=True)
        # Redirect back to frontend with error flag, rather than returning JSON (better UX)
        frontend_url = _get_oauth_frontend_url()
        error_redirect = f"{frontend_url}/login?error=sso_failed"
        return RedirectResponse(url=error_redirect, status_code=status.HTTP_302_FOUND)

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens
    
    For development: accepts email/password or SSO token.
    If DEV_LOGIN_EMAIL and DEV_LOGIN_PASSWORD are set in env, that pair is accepted
    and the user is created in DB if missing (so you can log in without signing up).
    """
    import os
    import uuid as uuid_mod

    try:
        # Development bypass: accept configured dev email/password so you can log in without signup
        dev_email = os.getenv("DEV_LOGIN_EMAIL", "").strip()
        dev_password = os.getenv("DEV_LOGIN_PASSWORD", "")
        if dev_email and dev_password and request.email == dev_email and request.password == dev_password:
            user_result = await db.execute(
                select(User).where(User.email == request.email, User.deleted_at.is_(None))
            )
            user = user_result.scalar_one_or_none()
            if not user:
                tenant_result = await db.execute(
                    select(Tenant).where(Tenant.slug == "default", Tenant.deleted_at.is_(None))
                )
                tenant = tenant_result.scalar_one_or_none()
                if not tenant:
                    tenant = Tenant(
                        id=uuid_mod.uuid4(),
                        name="Default Tenant",
                        slug="default",
                        status="active",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    db.add(tenant)
                    await db.flush()
                user = User(
                    id=uuid_mod.uuid4(),
                    tenant_id=tenant.id,
                    email=request.email,
                    first_name="Dev",
                    last_name="User",
                    password_hash=get_password_hash(request.password),
                    status="active",
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(user)
                await db.flush()
                await db.commit()
                logger.info("dev_login_user_created", email=user.email)
            roles = await get_user_roles(user, db)
            permissions = await get_user_permissions(user, db)
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "tenant_id": str(user.tenant_id),
                "roles": roles
            }
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            return LoginResponse(
                success=True,
                data={
                    "token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "tenant_id": str(user.tenant_id),
                        "roles": roles,
                        "permissions": permissions
                    }
                }
            )

        # Find user by email - use simpler query to avoid join timeout
        try:
            # First get user (simpler query, uses index on email)
            user_result = await db.execute(
                select(User)
                .where(User.email == request.email, User.deleted_at.is_(None))
            )
            user = user_result.scalar_one_or_none()
        except Exception as db_error:
            error_str = str(db_error)
            if "TimeoutError" in error_str or "timeout" in error_str.lower() or "asyncpg" in error_str.lower():
                logger.error("login_database_timeout", email=request.email, error=error_str, error_type=type(db_error).__name__)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database connection timeout. Please try again in a moment."
                )
            # Re-raise other database errors
            logger.error("login_database_error", email=request.email, error=error_str, error_type=type(db_error).__name__)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during login"
            )
        
        if not user:
            logger.warning("login_failed", email=request.email, reason="user_not_found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Then get tenant (separate query, faster)
        try:
            tenant_result = await db.execute(
                select(Tenant)
                .where(Tenant.id == user.tenant_id, Tenant.deleted_at.is_(None))
            )
            tenant = tenant_result.scalar_one_or_none()
        except Exception as db_error:
            error_str = str(db_error)
            if "TimeoutError" in error_str or "timeout" in error_str.lower():
                logger.error("login_tenant_timeout", user_id=str(user.id), tenant_id=str(user.tenant_id), error=error_str)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database connection timeout. Please try again."
                )
            # Re-raise other database errors
            logger.error("login_tenant_error", user_id=str(user.id), tenant_id=str(user.tenant_id), error=error_str)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during login"
            )
        
        if not tenant:
            logger.error("tenant_not_found", user_id=str(user.id), tenant_id=str(user.tenant_id))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User tenant not found"
            )
        
        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Check tenant status
        if tenant.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant account is inactive"
            )
        
        # Verify password (if provided, otherwise assume SSO)
        if request.password:
            if not user.password_hash or not verify_password(request.password, user.password_hash):
                logger.warning("login_failed", email=request.email, reason="invalid_password")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
        elif request.sso_token:
            # TODO: Verify SSO token with provider
            # For now, accept any SSO token if user has sso_provider set
            if not user.sso_provider:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="SSO not configured for this user"
                )
        else:
            # For development: create password if user doesn't have one
            if not user.password_hash:
                # Set default password for development
                user.password_hash = get_password_hash("password")
                await db.commit()
                logger.info("default_password_set", user_id=str(user.id))
        
        # Update last login (non-blocking, don't fail login if this times out)
        try:
            user.last_login_at = datetime.utcnow()
            await db.commit()
        except Exception as update_error:
            # Log but don't fail login if last_login update fails
            logger.warning("last_login_update_failed", user_id=str(user.id), error=str(update_error))
            # Rollback the failed update but continue with login
            try:
                await db.rollback()
            except Exception:
                pass
        
        # Get user roles and permissions
        roles = await get_user_roles(user, db)
        permissions = await get_user_permissions(user, db)
        
        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "roles": roles
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info("login_success", user_id=str(user.id), email=user.email)
        
        return LoginResponse(
            success=True,
            data={
                "token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "tenant_id": str(user.tenant_id),
                    "roles": roles,
                    "permissions": permissions
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user (invalidate token on client side)
    
    Note: For stateless JWT, actual invalidation requires token blacklist.
    This endpoint works even without a valid token to allow cleanup on client side.
    """
    # Try to get user if token is provided, but don't fail if token is missing/invalid
    user_id = None
    if credentials and credentials.credentials:
        try:
            from .utils import decode_token
            payload = decode_token(credentials.credentials)
            if payload and payload.get("type") == "access":
                user_id = payload.get("sub")
                if user_id:
                    logger.info("logout", user_id=user_id)
        except Exception:
            # Token invalid or expired - that's okay for logout
            pass
    
    if not user_id:
        logger.info("logout", message="Logout without valid token (client-side cleanup)")
    
    return LogoutResponse(success=True, data=None)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    payload = decode_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Get user roles
    roles = await get_user_roles(user, db)
    
    # Create new access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "tenant_id": str(user.tenant_id),
        "roles": roles
    }
    
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,  # Refresh token remains valid
        token_type="bearer",
        expires_in=30 * 60  # 30 minutes
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user information
    """
    roles = await get_user_roles(current_user, db)
    permissions = await get_user_permissions(current_user, db)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        tenant_id=current_user.tenant_id,
        roles=roles,
        permissions=permissions
    )

@router.get("/permissions", response_model=PermissionsResponse)
async def get_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's permissions
    """
    permissions = await get_user_permissions(current_user, db)
    
    return PermissionsResponse(
        success=True,
        data={"permissions": permissions}
    )


