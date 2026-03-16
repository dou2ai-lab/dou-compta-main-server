# -----------------------------------------------------------------------------
# File: audit_trail.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Audit trail tracking service
# -----------------------------------------------------------------------------

"""
Audit Trail Tracking Service
Tracks who added, modified, approved receipts and when extracted
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import Dict, Any, List, Optional
from datetime import datetime
from common.models import Expense, User, ApprovalWorkflow, ApprovalStep
from services.file_service.models import ReceiptDocument
from .models import AuditTrail, AuditSnapshot
import structlog
import json
import hashlib

logger = structlog.get_logger()

class AuditTrailService:
    """Service for tracking audit trails"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def track_receipt_added(
        self,
        receipt_id: str,
        expense_id: Optional[str],
        added_by: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """Track when a receipt is added"""
        try:
            trail = AuditTrail(
                tenant_id=self.tenant_id,
                entity_type="receipt",
                entity_id=receipt_id,
                action="added",
                performed_by=added_by,
                metadata={
                    "expense_id": expense_id,
                    "action_type": "receipt_added",
                    **(metadata or {})
                }
            )
            
            self.db.add(trail)
            await self.db.flush()
            
            # Create immutable snapshot
            await self._create_snapshot("receipt", receipt_id, "added", trail.id)
            
            logger.info("receipt_added_tracked", receipt_id=receipt_id, added_by=added_by)
            return trail
            
        except Exception as e:
            logger.error("track_receipt_added_error", error=str(e))
            raise
    
    async def track_receipt_modified(
        self,
        receipt_id: str,
        modified_by: str,
        changes: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """Track when a receipt is modified"""
        try:
            trail = AuditTrail(
                tenant_id=self.tenant_id,
                entity_type="receipt",
                entity_id=receipt_id,
                action="modified",
                performed_by=modified_by,
                metadata={
                    "changes": changes,
                    "action_type": "receipt_modified",
                    **(metadata or {})
                }
            )
            
            self.db.add(trail)
            await self.db.flush()
            
            # Create immutable snapshot
            await self._create_snapshot("receipt", receipt_id, "modified", trail.id, changes)
            
            logger.info("receipt_modified_tracked", receipt_id=receipt_id, modified_by=modified_by)
            return trail
            
        except Exception as e:
            logger.error("track_receipt_modified_error", error=str(e))
            raise
    
    async def track_receipt_approved(
        self,
        receipt_id: str,
        expense_id: Optional[str],
        approved_by: str,
        approval_step_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """Track when a receipt/expense is approved"""
        try:
            trail = AuditTrail(
                tenant_id=self.tenant_id,
                entity_type="receipt" if receipt_id else "expense",
                entity_id=receipt_id or expense_id,
                action="approved",
                performed_by=approved_by,
                metadata={
                    "expense_id": expense_id,
                    "receipt_id": receipt_id,
                    "approval_step_id": approval_step_id,
                    "action_type": "receipt_approved",
                    **(metadata or {})
                }
            )
            
            self.db.add(trail)
            await self.db.flush()
            
            # Create immutable snapshot
            await self._create_snapshot(
                "receipt" if receipt_id else "expense",
                receipt_id or expense_id,
                "approved",
                trail.id
            )
            
            logger.info("receipt_approved_tracked", receipt_id=receipt_id, approved_by=approved_by)
            return trail
            
        except Exception as e:
            logger.error("track_receipt_approved_error", error=str(e))
            raise
    
    async def track_extraction(
        self,
        receipt_id: str,
        extracted_by: str,
        extraction_method: str,
        extracted_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditTrail:
        """Track when data is extracted from receipt (OCR/LLM)"""
        try:
            trail = AuditTrail(
                tenant_id=self.tenant_id,
                entity_type="receipt",
                entity_id=receipt_id,
                action="extracted",
                performed_by=extracted_by,
                metadata={
                    "extraction_method": extraction_method,
                    "extracted_data": extracted_data,
                    "action_type": "data_extracted",
                    **(metadata or {})
                }
            )
            
            self.db.add(trail)
            await self.db.flush()
            
            # Create immutable snapshot with extracted data
            await self._create_snapshot(
                "receipt",
                receipt_id,
                "extracted",
                trail.id,
                extracted_data
            )
            
            logger.info("extraction_tracked", receipt_id=receipt_id, method=extraction_method)
            return trail
            
        except Exception as e:
            logger.error("track_extraction_error", error=str(e))
            raise
    
    async def get_audit_trail(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> List[AuditTrail]:
        """Get audit trail for an entity"""
        try:
            result = await self.db.execute(
                select(AuditTrail).where(
                    and_(
                        AuditTrail.tenant_id == self.tenant_id,
                        AuditTrail.entity_type == entity_type,
                        AuditTrail.entity_id == entity_id
                    )
                ).order_by(AuditTrail.performed_at.desc()).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error("get_audit_trail_error", error=str(e))
            return []
    
    async def _create_snapshot(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        trail_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> AuditSnapshot:
        """Create immutable snapshot of entity state"""
        try:
            # Get current entity state
            entity_data = await self._get_entity_state(entity_type, entity_id)
            
            if data:
                entity_data = {**entity_data, **data}
            
            # Create hash for immutability verification
            snapshot_hash = self._create_hash(entity_data)
            
            snapshot = AuditSnapshot(
                tenant_id=self.tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                audit_trail_id=trail_id,
                action=action,
                snapshot_data=entity_data,
                snapshot_hash=snapshot_hash
            )
            
            self.db.add(snapshot)
            await self.db.flush()
            
            logger.info("snapshot_created", entity_type=entity_type, entity_id=entity_id, action=action)
            return snapshot
            
        except Exception as e:
            logger.error("create_snapshot_error", error=str(e))
            raise
    
    async def _get_entity_state(
        self,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """Get current state of an entity"""
        try:
            if entity_type == "receipt":
                result = await self.db.execute(
                    select(ReceiptDocument).where(
                        and_(
                            ReceiptDocument.id == entity_id,
                            ReceiptDocument.tenant_id == self.tenant_id
                        )
                    )
                )
                receipt = result.scalar_one_or_none()
                if receipt:
                    return {
                        "id": str(receipt.id),
                        "file_name": receipt.file_name,
                        "file_size": receipt.file_size,
                        "mime_type": receipt.mime_type,
                        "storage_path": receipt.storage_path,
                        "expense_id": str(receipt.expense_id) if receipt.expense_id else None,
                        "upload_status": receipt.upload_status,
                        "ocr_status": receipt.ocr_status,
                        "meta_data": receipt.metadata_ or {}

                    }
            
            elif entity_type == "expense":
                result = await self.db.execute(
                    select(Expense).where(
                        and_(
                            Expense.id == entity_id,
                            Expense.tenant_id == self.tenant_id
                        )
                    )
                )
                expense = result.scalar_one_or_none()
                if expense:
                    return {
                        "id": str(expense.id),
                        "amount": float(expense.amount),
                        "currency": expense.currency,
                        "expense_date": expense.expense_date.isoformat() if expense.expense_date else None,
                        "category": expense.category,
                        "merchant_name": expense.merchant_name,
                        "status": expense.status,
                        "approval_status": expense.approval_status,
                        "vat_amount": float(expense.vat_amount) if expense.vat_amount else None,
                        "vat_rate": float(expense.vat_rate) if expense.vat_rate else None,
                        "meta_data": expense.metadata_ or {}
                    }
            
            return {}
            
        except Exception as e:
            logger.error("get_entity_state_error", error=str(e))
            return {}
    
    def _create_hash(self, data: Dict[str, Any]) -> str:
        """Create SHA-256 hash of data for immutability verification"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def verify_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Verify snapshot integrity"""
        try:
            result = await self.db.execute(
                select(AuditSnapshot).where(
                    and_(
                        AuditSnapshot.id == snapshot_id,
                        AuditSnapshot.tenant_id == self.tenant_id
                    )
                )
            )
            snapshot = result.scalar_one_or_none()
            
            if not snapshot:
                return {"valid": False, "error": "Snapshot not found"}
            
            # Recalculate hash
            current_hash = self._create_hash(snapshot.snapshot_data)
            
            if current_hash != snapshot.snapshot_hash:
                return {
                    "valid": False,
                    "error": "Snapshot hash mismatch - data may have been tampered",
                    "expected_hash": snapshot.snapshot_hash,
                    "calculated_hash": current_hash
                }
            
            return {
                "valid": True,
                "snapshot_id": str(snapshot.id),
                "entity_type": snapshot.entity_type,
                "entity_id": snapshot.entity_id,
                "action": snapshot.action,
                "created_at": snapshot.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error("verify_snapshot_error", error=str(e))
            return {"valid": False, "error": str(e)}

