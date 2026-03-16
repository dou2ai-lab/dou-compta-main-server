# -----------------------------------------------------------------------------
# File: audit_logger.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Comprehensive security audit logging
# -----------------------------------------------------------------------------

"""
Security Audit Logger
Comprehensive logging for security events
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta
import structlog
from fastapi import Request

from .models import SecurityAuditLog, FailedLoginAttempt, UserSession

logger = structlog.get_logger()

class SecurityAuditLogger:
    """Security audit logger"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def log_event(
        self,
        event_type: str,
        event_category: str,
        user_id: Optional[str] = None,
        severity: str = "info",
        description: Optional[str] = None,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log security event"""
        try:
            ip_address = None
            user_agent = None
            request_path = None
            request_method = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                request_path = str(request.url.path)
                request_method = request.method
            
            log_entry = SecurityAuditLog(
                tenant_id=self.tenant_id,
                user_id=user_id,
                event_type=event_type,
                event_category=event_category,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                request_method=request_method,
                description=description,
                metadata=metadata or {},
                success=success,
                error_message=error_message
            )
            
            self.db.add(log_entry)
            await self.db.flush()
            
            # Also log to structured logger
            logger.info(
                "security_audit_event",
                tenant_id=self.tenant_id,
                user_id=user_id,
                event_type=event_type,
                event_category=event_category,
                severity=severity,
                success=success
            )
            
        except Exception as e:
            logger.error("security_audit_log_error", error=str(e))
            # Don't raise - logging should not break the application
    
    async def log_login_attempt(
        self,
        email: str,
        success: bool,
        user_id: Optional[str] = None,
        request: Optional[Request] = None,
        error_message: Optional[str] = None
    ):
        """Log login attempt"""
        await self.log_event(
            event_type="login" if success else "login_failed",
            event_category="authentication",
            user_id=user_id,
            severity="error" if not success else "info",
            description=f"Login attempt for {email}",
            request=request,
            success=success,
            error_message=error_message
        )
        
        # Track failed attempts
        if not success:
            await self._track_failed_login(email, request)
    
    async def log_permission_denied(
        self,
        user_id: str,
        resource: str,
        action: str,
        request: Optional[Request] = None
    ):
        """Log permission denied event"""
        await self.log_event(
            event_type="permission_denied",
            event_category="authorization",
            user_id=user_id,
            severity="warning",
            description=f"Permission denied: {action} on {resource}",
            request=request,
            success=False,
            metadata={"resource": resource, "action": action}
        )
    
    async def log_data_access(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        request: Optional[Request] = None
    ):
        """Log data access event"""
        await self.log_event(
            event_type="data_access",
            event_category="data_access",
            user_id=user_id,
            severity="info",
            description=f"{action} on {entity_type}:{entity_id}",
            request=request,
            success=True,
            metadata={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action
            }
        )
    
    async def log_configuration_change(
        self,
        user_id: str,
        config_type: str,
        change_details: Dict[str, Any],
        request: Optional[Request] = None
    ):
        """Log configuration change"""
        await self.log_event(
            event_type="configuration_change",
            event_category="configuration",
            user_id=user_id,
            severity="warning",
            description=f"Configuration change: {config_type}",
            request=request,
            success=True,
            metadata={
                "config_type": config_type,
                "changes": change_details
            }
        )
    
    async def _track_failed_login(
        self,
        email: str,
        request: Optional[Request] = None
    ):
        """Track failed login attempts"""
        try:
            ip_address = request.client.host if request and request.client else None
            
            # Check existing record
            result = await self.db.execute(
                select(FailedLoginAttempt).where(
                    and_(
                        FailedLoginAttempt.email == email,
                        FailedLoginAttempt.tenant_id == self.tenant_id,
                        FailedLoginAttempt.last_attempt_at > datetime.utcnow() - timedelta(minutes=15)
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.attempt_count += 1
                existing.last_attempt_at = datetime.utcnow()
                
                # Lock account after 5 failed attempts
                if existing.attempt_count >= 5:
                    existing.locked_until = datetime.utcnow() + timedelta(minutes=30)
            else:
                failed_attempt = FailedLoginAttempt(
                    tenant_id=self.tenant_id,
                    email=email,
                    ip_address=ip_address,
                    user_agent=request.headers.get("user-agent") if request else None,
                    attempt_count=1
                )
                self.db.add(failed_attempt)
            
            await self.db.flush()
            
        except Exception as e:
            logger.error("track_failed_login_error", error=str(e))
    
    async def check_account_locked(self, email: str) -> bool:
        """Check if account is locked due to failed login attempts"""
        try:
            result = await self.db.execute(
                select(FailedLoginAttempt).where(
                    and_(
                        FailedLoginAttempt.email == email,
                        FailedLoginAttempt.tenant_id == self.tenant_id,
                        FailedLoginAttempt.locked_until > datetime.utcnow()
                    )
                )
            )
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error("check_account_locked_error", error=str(e))
            return False
    
    async def clear_failed_attempts(self, email: str):
        """Clear failed login attempts after successful login"""
        try:
            result = await self.db.execute(
                select(FailedLoginAttempt).where(
                    and_(
                        FailedLoginAttempt.email == email,
                        FailedLoginAttempt.tenant_id == self.tenant_id
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                await self.db.delete(existing)
                await self.db.flush()
        except Exception as e:
            logger.error("clear_failed_attempts_error", error=str(e))




