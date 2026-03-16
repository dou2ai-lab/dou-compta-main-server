# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Security service models
# -----------------------------------------------------------------------------

"""
Security Service Models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base

class SecurityAuditLog(Base):
    """Security audit log"""
    __tablename__ = "security_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Event details
    event_type = Column(String(100), nullable=False)
    event_category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    
    # Request details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    request_path = Column(String(500))
    request_method = Column(String(10))
    
    # Event details
    description = Column(Text)
    metadata = Column(JSONB, default={})
    
    # Result
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class FailedLoginAttempt(Base):
    """Failed login attempt tracking"""
    __tablename__ = "failed_login_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    email = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    attempt_count = Column(Integer, nullable=False, default=1)
    last_attempt_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    locked_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True)
    
    # Device and location
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_type = Column(String(50))
    device_id = Column(String(255))
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Security
    login_method = Column(String(50), default="password")
    mfa_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    revoked_at = Column(DateTime(timezone=True))




