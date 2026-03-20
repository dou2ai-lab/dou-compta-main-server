# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: GDPR service routes
# -----------------------------------------------------------------------------

"""
GDPR Service Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user, get_user_permissions
from .data_subject_service import DataSubjectService
from .retention_service import RetentionService
from .data_minimization import DataMinimizationService
from .privacy_logger import PrivacyLogger
from .schemas import (
    DataSubjectRequestCreate,
    DataSubjectRequestResponse,
    DataSubjectRequestVerify,
    RetentionRuleResponse,
    PrivacyLogResponse
)

logger = structlog.get_logger()
router = APIRouter()

async def require_gdpr_permission(current_user: User, db: AsyncSession):
    """Check if user has GDPR permissions"""
    permissions = await get_user_permissions(current_user, db)
    if "gdpr:write" not in permissions and "admin:write" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

# Phase 27 Routes

@router.post("/data-subject-request", response_model=DataSubjectRequestResponse)
async def create_data_subject_request(
    request: DataSubjectRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create data subject request (public endpoint)"""
    try:
        # Get tenant from email domain or request
        # For now, use default tenant (in production, determine from email)
        from common.models import Tenant
        tenant_result = await db.execute(
            select(Tenant).limit(1)
        )
        tenant = tenant_result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        service = DataSubjectService(db, str(tenant.id))
        
        result = await service.create_request(
            request_type=request.request_type,
            subject_email=request.subject_email,
            subject_name=request.subject_name,
            subject_id=request.subject_id
        )
        
        await db.commit()
        
        return DataSubjectRequestResponse(**result)
    except Exception as e:
        await db.rollback()
        logger.error("create_data_subject_request_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create request")

@router.post("/data-subject-request/{request_id}/verify", response_model=Dict[str, Any])
async def verify_data_subject_request(
    request_id: str,
    request: DataSubjectRequestVerify,
    db: AsyncSession = Depends(get_db)
):
    """Verify data subject request"""
    try:
        from common.models import Tenant
        tenant_result = await db.execute(select(Tenant).limit(1))
        tenant = tenant_result.scalar_one_or_none()
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        service = DataSubjectService(db, str(tenant.id))
        
        result = await service.verify_request(
            request_id=request_id,
            verification_token=request.verification_token
        )
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("verify_data_subject_request_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to verify request")

@router.post("/data-subject-request/{request_id}/process", response_model=Dict[str, Any])
async def process_data_subject_request(
    request_id: str,
    request_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process data subject request"""
    await require_gdpr_permission(current_user, db)
    
    try:
        service = DataSubjectService(db, str(current_user.tenant_id))
        
        if request_type == "access":
            result = await service.process_access_request(
                request_id=request_id,
                processed_by=str(current_user.id)
            )
        elif request_type == "erasure":
            result = await service.process_erasure_request(
                request_id=request_id,
                processed_by=str(current_user.id)
            )
        elif request_type == "portability":
            result = await service.process_portability_request(
                request_id=request_id,
                processed_by=str(current_user.id)
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid request type")
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("process_data_subject_request_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process request")

@router.post("/retention/initialize", response_model=Dict[str, Any])
async def initialize_retention_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Initialize default retention rules"""
    await require_gdpr_permission(current_user, db)
    
    try:
        service = RetentionService(db, str(current_user.tenant_id))
        
        result = await service.initialize_default_rules()
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("initialize_retention_rules_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to initialize rules")

@router.post("/retention/apply", response_model=Dict[str, Any])
async def apply_retention_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Apply retention rules"""
    await require_gdpr_permission(current_user, db)
    
    try:
        service = RetentionService(db, str(current_user.tenant_id))
        
        result = await service.apply_retention_rules()
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("apply_retention_rules_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to apply rules")

@router.post("/minimization/run", response_model=Dict[str, Any])
async def run_data_minimization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run data minimization pass"""
    await require_gdpr_permission(current_user, db)
    
    try:
        service = DataMinimizationService(db, str(current_user.tenant_id))
        
        result = await service.run_minimization_pass()
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("run_data_minimization_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to run minimization")




