# -----------------------------------------------------------------------------
# File: privacy_logger.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Privacy logging service
# -----------------------------------------------------------------------------

"""
Privacy Logging Service
Logs all access to personal data for GDPR compliance
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import structlog
from fastapi import Request

from .models import PrivacyLog
from .config import settings

logger = structlog.get_logger()

class PrivacyLogger:
    """Privacy access logger"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.enabled = settings.ENABLE_PRIVACY_LOGGING
    
    async def log_access(
        self,
        accessed_by: str,
        entity_type: str,
        entity_id: str,
        access_type: str,
        contains_pii: bool = False,
        request: Optional[Request] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log access to personal data"""
        try:
            if not self.enabled:
                return
            
            # Get IP and user agent from request
            ip_address = None
            user_agent = None
            request_path = None
            
            if request:
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                request_path = str(request.url.path)
            
            # Only log if contains PII or log_pii_access is enabled
            if not contains_pii and not settings.LOG_PII_ACCESS:
                return
            
            log_entry = PrivacyLog(
                tenant_id=self.tenant_id,
                accessed_by=accessed_by,
                entity_type=entity_type,
                entity_id=entity_id,
                access_type=access_type,
                contains_pii=contains_pii,
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                metadata=metadata or {}
            )
            
            self.db.add(log_entry)
            await self.db.flush()
            
            logger.info(
                "privacy_access_logged",
                tenant_id=self.tenant_id,
                accessed_by=accessed_by,
                entity_type=entity_type,
                entity_id=entity_id,
                access_type=access_type
            )
            
        except Exception as e:
            logger.error("privacy_logging_error", error=str(e))
            # Don't raise - logging should not break the application




