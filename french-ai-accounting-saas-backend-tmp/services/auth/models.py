# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Authentication service models and schemas
# -----------------------------------------------------------------------------

"""
Authentication service models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: Optional[str] = None  # Optional for SSO
    sso_token: Optional[str] = None  # For SSO login

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str

class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    tenant_id: UUID
    roles: List[str] = []
    permissions: List[str] = []
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """Login response model"""
    success: bool = True
    data: dict

class LogoutResponse(BaseModel):
    """Logout response model"""
    success: bool = True
    data: Optional[dict] = None

class PermissionsResponse(BaseModel):
    """Permissions response model"""
    success: bool = True
    data: dict

class SignupRequest(BaseModel):
    """Signup request model"""
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class SignupResponse(BaseModel):
    """Signup response model"""
    success: bool = True
    data: dict






