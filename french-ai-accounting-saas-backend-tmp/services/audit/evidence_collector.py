# -----------------------------------------------------------------------------
# File: evidence_collector.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Evidence collection service
# -----------------------------------------------------------------------------

"""
Evidence Collection Service
Maps audit samples to receipts and approval chains
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from common.models import Expense, User, ApprovalWorkflow, ApprovalStep
from .models import AuditEvidence, AuditReport
from services.file_service.models import ReceiptDocument
import structlog
import zipfile
import io
import os
import uuid
import json

logger = structlog.get_logger()

class EvidenceCollector:
    """Collect evidence for audit reports"""
    
    def __init__(self, db: AsyncSession, tenant_id: str, storage_service=None):
        self.db = db
        self.tenant_id = tenant_id
        self.storage_service = storage_service
    
    async def collect_evidence_for_sample(
        self,
        audit_report_id: str,
        expense_ids: List[str],
        created_by: str
    ) -> Dict[str, Any]:
        """
        Collect evidence for a list of expenses
        Maps: expense → receipts → approval chain
        """
        try:
            evidence_items = []
            
            for expense_id in expense_ids:
                result = await self.db.execute(
                    select(Expense).where(
                        and_(
                            Expense.id == expense_id,
                            Expense.tenant_id == self.tenant_id
                        )
                    )
                )
                expense = result.scalar_one_or_none()
                
                if not expense:
                    continue
                
                expense_evidence = await self._collect_expense_evidence(
                    audit_report_id, expense, created_by
                )
                evidence_items.append(expense_evidence)
                
                receipt_evidence = await self._collect_receipt_evidence(
                    audit_report_id, expense, created_by
                )
                evidence_items.extend(receipt_evidence)
                
                approval_evidence = await self._collect_approval_evidence(
                    audit_report_id, expense, created_by
                )
                evidence_items.extend(approval_evidence)
            
            return {
                "success": True,
                "audit_report_id": audit_report_id,
                "expenses_processed": len(expense_ids),
                "evidence_items_collected": len(evidence_items),
                "evidence_items": evidence_items
            }
            
        except Exception as e:
            logger.error("evidence_collection_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _collect_expense_evidence(
        self,
        audit_report_id: str,
        expense: Expense,
        created_by: str
    ) -> Dict[str, Any]:
        """Collect expense data as evidence"""
        evidence = AuditEvidence(
            id=uuid.uuid4(),
            audit_report_id=audit_report_id,
            tenant_id=self.tenant_id,
            expense_id=expense.id,
            evidence_type="expense_data",
            evidence_category="primary",
            description=f"Expense data for {expense.merchant_name or 'Unknown merchant'}",
            collected_by=created_by,
            metadata_={
                "amount": float(expense.amount),
                "currency": expense.currency,
                "date": expense.expense_date.isoformat(),
                "category": expense.category,
                "merchant": expense.merchant_name,
                "status": expense.status,
                "approval_status": expense.approval_status
            }
        )
        
        self.db.add(evidence)
        await self.db.flush()
        
        return {
            "id": str(evidence.id),
            "type": "expense_data",
            "expense_id": str(expense.id)
        }
    
    async def _collect_receipt_evidence(
        self,
        audit_report_id: str,
        expense: Expense,
        created_by: str
    ) -> List[Dict[str, Any]]:
        """Collect receipt documents as evidence"""
        evidence_items = []
        
        try:
            receipt_result = await self.db.execute(
                select(ReceiptDocument).where(
                    and_(
                        ReceiptDocument.expense_id == expense.id,
                        ReceiptDocument.tenant_id == self.tenant_id,
                        ReceiptDocument.deleted_at.is_(None)
                    )
                )
            )
            receipts = receipt_result.scalars().all()
            
            if not receipts:
                logger.info("no_receipts_found", expense_id=str(expense.id))
                return evidence_items
            
            for receipt in receipts:
                try:
                    evidence = AuditEvidence(
                        id=uuid.uuid4(),
                        audit_report_id=audit_report_id,
                        tenant_id=self.tenant_id,
                        expense_id=expense.id,
                        receipt_id=receipt.id,
                        evidence_type="receipt",
                        evidence_category="primary",
                        description=f"Receipt document: {receipt.file_name}",
                        file_name=receipt.file_name,
                        file_size=receipt.file_size,
                        mime_type=receipt.mime_type,
                        storage_path=receipt.storage_path,
                        storage_provider=(getattr(receipt, "meta_data", None) or {}).get("storage_provider", "s3"),
                        storage_key=receipt.storage_path,
                        collected_by=created_by,
                        metadata_={
                            "receipt_id": str(receipt.id),
                            "file_id": str(receipt.file_id),
                            "linked_to_expense": str(expense.id),
                            "upload_status": receipt.upload_status,
                            "ocr_status": receipt.ocr_status
                        }
                    )
                    
                    self.db.add(evidence)
                    await self.db.flush()
                    
                    evidence_items.append({
                        "id": str(evidence.id),
                        "type": "receipt",
                        "receipt_id": str(receipt.id),
                        "expense_id": str(expense.id),
                        "file_name": receipt.file_name
                    })
                    
                except Exception as e:
                    logger.error("receipt_evidence_error", receipt_id=str(receipt.id), error=str(e))
                    continue
            
        except Exception as e:
            logger.error("collect_receipt_evidence_error", expense_id=str(expense.id), error=str(e))
        
        return evidence_items
    
    async def _collect_approval_evidence(
        self,
        audit_report_id: str,
        expense: Expense,
        created_by: str
    ) -> List[Dict[str, Any]]:
        """Collect approval chain as evidence. Use SYSTEM_AUTO_RULE_ENGINE when auto-approved (5.2.4)."""
        evidence_items = []
        
        try:
            workflow_result = await self.db.execute(
                select(ApprovalWorkflow).where(
                    and_(
                        ApprovalWorkflow.entity_type == "expense",
                        ApprovalWorkflow.entity_id == expense.id,
                        ApprovalWorkflow.tenant_id == self.tenant_id
                    )
                )
            )
            workflow = workflow_result.scalar_one_or_none()
            
            if not workflow and expense.approval_status == "approved":
                # Auto-approved: do not use LLM name; use system identity (5.2.4)
                evidence = AuditEvidence(
                    id=uuid.uuid4(),
                    audit_report_id=audit_report_id,
                    tenant_id=self.tenant_id,
                    expense_id=expense.id,
                    evidence_type="approval_chain",
                    evidence_category="supporting",
                    description="Auto-approved by SYSTEM_AUTO_RULE_ENGINE",
                    collected_by=created_by,
                    metadata_={
                        "step_number": 1,
                        "approver_id": "SYSTEM_AUTO_RULE_ENGINE",
                        "approver_email": None,
                        "status": "approved",
                        "approved_at": expense.approved_at.isoformat() if getattr(expense, "approved_at", None) else None,
                        "notes": "System auto-approval rule"
                    }
                )
                self.db.add(evidence)
                await self.db.flush()
                evidence_items.append({
                    "id": str(evidence.id),
                    "type": "approval_chain",
                    "step_number": 1,
                    "approver": "SYSTEM_AUTO_RULE_ENGINE",
                    "status": "approved"
                })
                return evidence_items
            
            if workflow:
                steps_result = await self.db.execute(
                    select(ApprovalStep).where(
                        ApprovalStep.workflow_id == workflow.id
                    ).order_by(ApprovalStep.step_number)
                )
                steps = steps_result.scalars().all()
                
                for step in steps:
                    approver_result = await self.db.execute(
                        select(User).where(User.id == step.approver_id)
                    )
                    approver = approver_result.scalar_one_or_none()
                    
                    evidence = AuditEvidence(
                        id=uuid.uuid4(),
                        audit_report_id=audit_report_id,
                        tenant_id=self.tenant_id,
                        expense_id=expense.id,
                        approval_step_id=step.id,
                        evidence_type="approval_chain",
                        evidence_category="supporting",
                        description=f"Approval step {step.step_number} by {approver.email if approver else 'Unknown'}",
                        collected_by=created_by,
                        metadata_={
                            "step_number": step.step_number,
                            "approver_id": str(step.approver_id),
                            "approver_email": approver.email if approver else None,
                            "status": step.status,
                            "approved_at": step.approved_at.isoformat() if step.approved_at else None,
                            "rejected_at": step.rejected_at.isoformat() if step.rejected_at else None,
                            "notes": step.approval_notes
                        }
                    )
                    
                    self.db.add(evidence)
                    await self.db.flush()
                    
                    evidence_items.append({
                        "id": str(evidence.id),
                        "type": "approval_chain",
                        "step_number": step.step_number,
                        "approver": approver.email if approver else "Unknown",
                        "status": step.status
                    })
            
        except Exception as e:
            logger.error("collect_approval_evidence_error", expense_id=str(expense.id), error=str(e))
        
        return evidence_items
    
    async def generate_evidence_zip(
        self,
        audit_report_id: str,
        include_receipts: bool = True,
        include_approvals: bool = True
    ) -> bytes:
        try:
            result = await self.db.execute(
                select(AuditEvidence).where(
                    and_(
                        AuditEvidence.audit_report_id == audit_report_id,
                        AuditEvidence.tenant_id == self.tenant_id
                    )
                )
            )
            evidence_items = result.scalars().all()
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for evidence in evidence_items:
                    zip_file.writestr(
                        f"evidence/{evidence.id}/metadata.json",
                        json.dumps(evidence.metadata_, indent=2)
                    )
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error("generate_evidence_zip_error", error=str(e))
            raise
