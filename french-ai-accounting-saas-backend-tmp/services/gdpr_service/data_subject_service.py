# -----------------------------------------------------------------------------
# File: data_subject_service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Data subject request service (GDPR)
# -----------------------------------------------------------------------------

"""
Data Subject Request Service
Handles GDPR data subject requests (access, rectification, erasure, portability)
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
import structlog
import json
import secrets
import uuid

from .models import DataSubjectRequest
from common.models import Expense, Receipt, User, PolicyViolation

logger = structlog.get_logger()

class DataSubjectService:
    """Data subject request service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def create_request(
        self,
        request_type: str,
        subject_email: str,
        subject_name: Optional[str] = None,
        subject_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create data subject request"""
        try:
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            
            request = DataSubjectRequest(
                tenant_id=self.tenant_id,
                request_type=request_type,
                subject_email=subject_email,
                subject_name=subject_name,
                subject_id=uuid.UUID(subject_id) if subject_id else None,
                status="pending",
                verification_token=verification_token
            )
            
            self.db.add(request)
            await self.db.flush()
            
            return {
                "success": True,
                "request_id": str(request.id),
                "verification_token": verification_token,
                "status": request.status
            }
            
        except Exception as e:
            logger.error("create_data_subject_request_error", error=str(e))
            raise
    
    async def verify_request(
        self,
        request_id: str,
        verification_token: str
    ) -> Dict[str, Any]:
        """Verify data subject request"""
        try:
            result = await self.db.execute(
                select(DataSubjectRequest).where(
                    and_(
                        DataSubjectRequest.id == request_id,
                        DataSubjectRequest.tenant_id == self.tenant_id,
                        DataSubjectRequest.verification_token == verification_token,
                        DataSubjectRequest.deleted_at.is_(None)
                    )
                )
            )
            request = result.scalar_one_or_none()
            
            if not request:
                return {"success": False, "error": "Invalid request or token"}
            
            request.verified_at = datetime.utcnow()
            await self.db.commit()
            
            return {
                "success": True,
                "request_id": str(request.id),
                "verified": True
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("verify_data_subject_request_error", error=str(e))
            raise
    
    async def process_access_request(
        self,
        request_id: str,
        processed_by: str
    ) -> Dict[str, Any]:
        """Process data access request (GDPR Article 15)"""
        try:
            result = await self.db.execute(
                select(DataSubjectRequest).where(
                    and_(
                        DataSubjectRequest.id == request_id,
                        DataSubjectRequest.tenant_id == self.tenant_id,
                        DataSubjectRequest.deleted_at.is_(None)
                    )
                )
            )
            request = result.scalar_one_or_none()
            
            if not request:
                raise ValueError("Request not found")
            
            if request.request_type != "access":
                raise ValueError("Request is not an access request")
            
            # Collect all data for the subject
            data = await self._collect_subject_data(request)
            
            # Update request
            request.status = "completed"
            request.response_data = data
            request.processed_by = uuid.UUID(processed_by)
            request.completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "request_id": str(request.id),
                "data": data
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("process_access_request_error", error=str(e))
            raise
    
    async def process_erasure_request(
        self,
        request_id: str,
        processed_by: str
    ) -> Dict[str, Any]:
        """Process data erasure request (GDPR Article 17 - Right to be forgotten)"""
        try:
            result = await self.db.execute(
                select(DataSubjectRequest).where(
                    and_(
                        DataSubjectRequest.id == request_id,
                        DataSubjectRequest.tenant_id == self.tenant_id,
                        DataSubjectRequest.deleted_at.is_(None)
                    )
                )
            )
            request = result.scalar_one_or_none()
            
            if not request:
                raise ValueError("Request not found")
            
            if request.request_type != "erasure":
                raise ValueError("Request is not an erasure request")
            
            # Check if erasure is allowed (accounting retention may prevent it)
            can_erase = await self._check_erasure_allowed(request)
            
            if not can_erase["allowed"]:
                request.status = "rejected"
                request.rejection_reason = can_erase["reason"]
                request.processed_by = uuid.UUID(processed_by)
                await self.db.commit()
                
                return {
                    "success": False,
                    "allowed": False,
                    "reason": can_erase["reason"]
                }
            
            # Perform erasure (soft delete or anonymization)
            await self._erase_subject_data(request)
            
            request.status = "completed"
            request.processed_by = uuid.UUID(processed_by)
            request.completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "request_id": str(request.id),
                "erased": True
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("process_erasure_request_error", error=str(e))
            raise
    
    async def process_portability_request(
        self,
        request_id: str,
        processed_by: str
    ) -> Dict[str, Any]:
        """Process data portability request (GDPR Article 20)"""
        try:
            result = await self.db.execute(
                select(DataSubjectRequest).where(
                    and_(
                        DataSubjectRequest.id == request_id,
                        DataSubjectRequest.tenant_id == self.tenant_id,
                        DataSubjectRequest.deleted_at.is_(None)
                    )
                )
            )
            request = result.scalar_one_or_none()
            
            if not request:
                raise ValueError("Request not found")
            
            if request.request_type != "portability":
                raise ValueError("Request is not a portability request")
            
            # Collect data in machine-readable format (JSON)
            data = await self._collect_subject_data(request)
            
            # Generate export file
            export_data = json.dumps(data, indent=2, default=str)
            
            request.status = "completed"
            request.response_data = data
            request.response_file_path = f"/exports/{request.id}.json"
            request.processed_by = uuid.UUID(processed_by)
            request.completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "request_id": str(request.id),
                "data": export_data,
                "file_path": request.response_file_path
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error("process_portability_request_error", error=str(e))
            raise
    
    async def _collect_subject_data(
        self,
        request: DataSubjectRequest
    ) -> Dict[str, Any]:
        """Collect all data for the subject"""
        data = {
            "subject_email": request.subject_email,
            "subject_name": request.subject_name,
            "collected_at": datetime.utcnow().isoformat()
        }
        
        # Get user data if subject_id exists
        if request.subject_id:
            user_result = await self.db.execute(
                select(User).where(
                    and_(
                        User.id == request.subject_id,
                        User.tenant_id == self.tenant_id
                    )
                )
            )
            user = user_result.scalar_one_or_none()
            
            if user:
                data["user"] = {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                }
                
                # Get expenses
                expenses_result = await self.db.execute(
                    select(Expense).where(
                        and_(
                            Expense.submitted_by == request.subject_id,
                            Expense.tenant_id == self.tenant_id,
                            Expense.deleted_at.is_(None)
                        )
                    )
                )
                expenses = expenses_result.scalars().all()
                
                data["expenses"] = [
                    {
                        "id": str(e.id),
                        "amount": float(e.amount),
                        "currency": e.currency,
                        "expense_date": e.expense_date.isoformat() if e.expense_date else None,
                        "category": e.category,
                        "description": e.description,
                        "merchant_name": e.merchant_name,
                        "status": e.status,
                        "created_at": e.created_at.isoformat() if e.created_at else None
                    }
                    for e in expenses
                ]
                
                # Get receipts
                receipts_result = await self.db.execute(
                    select(Receipt).where(
                        and_(
                            Receipt.uploaded_by == request.subject_id,
                            Receipt.tenant_id == self.tenant_id,
                            Receipt.deleted_at.is_(None)
                        )
                    )
                )
                receipts = receipts_result.scalars().all()
                
                data["receipts"] = [
                    {
                        "id": str(r.id),
                        "file_name": r.file_name,
                        "uploaded_at": r.created_at.isoformat() if r.created_at else None
                    }
                    for r in receipts
                ]
        
        return data
    
    async def _check_erasure_allowed(
        self,
        request: DataSubjectRequest
    ) -> Dict[str, Any]:
        """Check if data erasure is allowed (accounting retention)"""
        from .config import settings
        
        # Check if there are expenses within retention period
        if request.subject_id:
            cutoff_date = datetime.utcnow() - timedelta(days=settings.ACCOUNTING_RETENTION_YEARS * 365)
            
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.submitted_by == request.subject_id,
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= cutoff_date.date(),
                        Expense.deleted_at.is_(None)
                    )
                ).limit(1)
            )
            
            if result.scalar_one_or_none():
                return {
                    "allowed": False,
                    "reason": f"Data cannot be erased due to {settings.ACCOUNTING_RETENTION_YEARS}-year accounting retention requirement"
                }
        
        return {"allowed": True}
    
    async def _erase_subject_data(
        self,
        request: DataSubjectRequest
    ):
        """Erase subject data (anonymize or soft delete)"""
        if not request.subject_id:
            return
        
        # Anonymize user data
        user_result = await self.db.execute(
            select(User).where(
                and_(
                    User.id == request.subject_id,
                    User.tenant_id == self.tenant_id
                )
            )
        )
        user = user_result.scalar_one_or_none()
        
        if user:
            # Anonymize personal data
            user.email = f"deleted_{user.id}@deleted.local"
            user.first_name = "Deleted"
            user.last_name = "User"
            # Keep accounting data but anonymize personal identifiers
        
        # Soft delete expenses (keep for accounting but remove personal links)
        # In production, implement proper anonymization




