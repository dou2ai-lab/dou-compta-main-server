# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Audit service routes
# -----------------------------------------------------------------------------

"""
Audit routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
import structlog
import json
import io
import zipfile

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user, get_user_permissions, get_user_roles
from .service import AuditService
from .schemas import (
    AuditReportCreate,
    AuditReportResponse,
    AuditReportUpdate,
    PendingExpenseReportItem,
    AuditMetadataCreate,
    AuditMetadataResponse,
    EvidenceCollectionRequest,
    EvidenceCollectionResponse,
    EvidenceItem,
    SignedUrlResponse,
    PopulateReportRequest,
    AuditTrailResponse,
    SnapshotVerificationResponse,
    BasicReportRequest,
    BasicReportResponse,
    NarrativeGenerationRequest,
    NarrativeGenerationResponse
)
from services.file_service.storage import StorageService
from .models import AuditEvidence, AuditSnapshot

logger = structlog.get_logger()
router = APIRouter()


# -------------------------------------------------------------------
# PERMISSION
# -------------------------------------------------------------------

async def require_audit_permission(current_user: User, db: AsyncSession):
    permissions = await get_user_permissions(current_user, db)
    if "audit:read" in permissions:
        return
    roles = await get_user_roles(current_user, db)
    if roles and any(str(r).lower() == "admin" for r in roles):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized"
    )


# -------------------------------------------------------------------
# DASHBOARD / LOGS / RISKS
# -------------------------------------------------------------------

@router.get("/dashboard")
async def get_dashboard(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    from common.models import Expense

    query = select(Expense).where(
        Expense.tenant_id == current_user.tenant_id,
        Expense.deleted_at.is_(None)
    )

    if start_date:
        query = query.where(Expense.expense_date >= start_date)
    if end_date:
        query = query.where(Expense.expense_date <= end_date)

    result = await db.execute(query)
    expenses = result.scalars().all()

    total_expenses = len(expenses)
    total_amount = sum(float(exp.amount) for exp in expenses)
    approved_count = sum(1 for exp in expenses if exp.approval_status == "approved")
    pending_count = sum(1 for exp in expenses if exp.approval_status == "pending")

    return {
        "success": True,
        "data": {
            "total_expenses": total_expenses,
            "total_amount": total_amount,
            "approved_count": approved_count,
            "pending_count": pending_count,
            "rejected_count": total_expenses - approved_count - pending_count
        }
    }


@router.get("/logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    return {
        "success": True,
        "data": {
            "logs": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        }
    }


@router.get("/risks")
async def list_risks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    return {
        "success": True,
        "data": {"risks": []}
    }


@router.get("/pending-expense-reports", response_model=List[PendingExpenseReportItem])
async def list_pending_expense_reports(
    status_filter: Optional[str] = Query(None, description="Filter: submitted, draft, approved, rejected; default submitted"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List expense reports submitted for approval, for auditor review. Shown on Audit Reports page."""
    await require_audit_permission(current_user, db)

    from common.models import ExpenseReport

    query = select(ExpenseReport).where(
        ExpenseReport.tenant_id == current_user.tenant_id,
        ExpenseReport.deleted_at.is_(None)
    )
    status = status_filter if status_filter else "submitted"
    query = query.where(ExpenseReport.status == status)
    query = query.order_by(ExpenseReport.submitted_at.desc().nullslast(), ExpenseReport.created_at.desc())
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    return [
        PendingExpenseReportItem(
            id=str(r.id),
            report_number=r.report_number,
            title=r.title,
            period_start_date=r.period_start_date,
            period_end_date=r.period_end_date,
            total_amount=float(r.total_amount),
            currency=r.currency or "EUR",
            expense_count=r.expense_count or 0,
            status=r.status,
            approval_status=r.approval_status,
            submitted_at=r.submitted_at,
            created_at=r.created_at,
        )
        for r in reports
    ]


# -------------------------------------------------------------------
# REPORTS
# -------------------------------------------------------------------

@router.post("/reports", response_model=AuditReportResponse)
async def create_audit_report(
    report_data: AuditReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())

        report = await service.create_audit_report(
            title=report_data.title,
            period_start=report_data.period_start,
            period_end=report_data.period_end,
            period_type=report_data.period_type,
            report_type=report_data.report_type,
            created_by=str(current_user.id),
            description=report_data.description
        )

        await db.commit()

        return AuditReportResponse(
            id=str(report.id),
            report_number=report.report_number,
            title=report.title,
            description=report.description,
            audit_period_start=report.audit_period_start,
            audit_period_end=report.audit_period_end,
            period_type=report.period_type,
            report_type=report.report_type,
            status=report.status,
            template_version=report.template_version,
            sample_size=report.sample_size,
            total_expenses_in_scope=report.total_expenses_in_scope,
            total_amount_in_scope=float(report.total_amount_in_scope),
            technical_data=report.technical_data,
            narrative_sections=report.narrative_sections,
            metadata=report.metadata_,
            created_at=report.created_at,
            updated_at=report.updated_at,
            completed_at=report.completed_at,
            published_at=report.published_at
        )

    except Exception as e:
        await db.rollback()
        logger.error("create_audit_report_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create audit report")


@router.get("/reports", response_model=List[AuditReportResponse])
async def list_audit_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        reports = await service.list_audit_reports(limit, offset, status)

        return [
            AuditReportResponse(
                id=str(r.id),
                report_number=r.report_number,
                title=r.title,
                description=r.description,
                audit_period_start=r.audit_period_start,
                audit_period_end=r.audit_period_end,
                period_type=r.period_type,
                report_type=r.report_type,
                status=r.status,
                template_version=r.template_version,
                sample_size=r.sample_size,
                total_expenses_in_scope=r.total_expenses_in_scope,
                total_amount_in_scope=float(r.total_amount_in_scope),
                technical_data=r.technical_data,
                narrative_sections=r.narrative_sections,
                metadata=r.metadata_,
                created_at=r.created_at,
                updated_at=r.updated_at,
                completed_at=r.completed_at,
                published_at=r.published_at
            )
            for r in reports
        ]

    except Exception as e:
        logger.error("list_audit_reports_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list audit reports")


@router.get("/reports/{report_id}", response_model=AuditReportResponse)
async def get_audit_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    service = AuditService(db, str(current_user.tenant_id), StorageService())
    report = await service.get_audit_report(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")

    return AuditReportResponse(
        id=str(report.id),
        report_number=report.report_number,
        title=report.title,
        description=report.description,
        audit_period_start=report.audit_period_start,
        audit_period_end=report.audit_period_end,
        period_type=report.period_type,
        report_type=report.report_type,
        status=report.status,
        template_version=report.template_version,
        sample_size=report.sample_size,
        total_expenses_in_scope=report.total_expenses_in_scope,
        total_amount_in_scope=float(report.total_amount_in_scope),
        technical_data=report.technical_data,
        narrative_sections=report.narrative_sections,
        metadata=report.metadata_,
        created_at=report.created_at,
        updated_at=report.updated_at,
        completed_at=report.completed_at,
        published_at=report.published_at
    )


@router.patch("/reports/{report_id}", response_model=AuditReportResponse)
async def update_audit_report(
    report_id: str,
    updates: AuditReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        report = await service.update_audit_report(report_id, updates.dict(exclude_unset=True))

        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")

        await db.commit()

        return AuditReportResponse(
            id=str(report.id),
            report_number=report.report_number,
            title=report.title,
            description=report.description,
            audit_period_start=report.audit_period_start,
            audit_period_end=report.audit_period_end,
            period_type=report.period_type,
            report_type=report.report_type,
            status=report.status,
            template_version=report.template_version,
            sample_size=report.sample_size,
            total_expenses_in_scope=report.total_expenses_in_scope,
            total_amount_in_scope=float(report.total_amount_in_scope),
            technical_data=report.technical_data,
            narrative_sections=report.narrative_sections,
            metadata=report.metadata_,
            created_at=report.created_at,
            updated_at=report.updated_at,
            completed_at=report.completed_at,
            published_at=report.published_at
        )

    except Exception as e:
        await db.rollback()
        logger.error("update_audit_report_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update audit report")


# -------------------------------------------------------------------
# EVIDENCE
# -------------------------------------------------------------------

@router.get("/reports/{report_id}/evidence", response_model=List[EvidenceItem])
async def list_evidence(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    result = await db.execute(
        select(AuditEvidence)
        .where(
            AuditEvidence.audit_report_id == report_id,
            AuditEvidence.tenant_id == current_user.tenant_id
        )
        .order_by(AuditEvidence.collected_at.desc())
    )

    evidence_items = result.scalars().all()

    return [
        EvidenceItem(
            id=str(e.id),
            evidence_type=e.evidence_type,
            evidence_category=e.evidence_category,
            description=e.description,
            expense_id=str(e.expense_id) if e.expense_id else None,
            receipt_id=str(e.receipt_id) if e.receipt_id else None,
            file_name=e.file_name,
            file_size=e.file_size,
            mime_type=e.mime_type,
            metadata=e.metadata_,
            collected_at=e.collected_at
        )
        for e in evidence_items
    ]


# -------------------------------------------------------------------
# TRAIL / SNAPSHOT / BASIC REPORT
# -------------------------------------------------------------------

@router.get("/trail/{entity_type}/{entity_id}", response_model=List[AuditTrailResponse])
async def get_audit_trail(
    entity_type: str,
    entity_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    service = AuditService(db, str(current_user.tenant_id), StorageService())
    trails = await service.audit_trail.get_audit_trail(entity_type, entity_id, limit)

    return [
        AuditTrailResponse(
            id=str(t.id),
            entity_type=t.entity_type,
            entity_id=t.entity_id,
            action=t.action,
            performed_by=str(t.performed_by),
            performed_at=t.performed_at,
            metadata=t.metadata_
        )
        for t in trails
    ]


@router.post("/reports/generate-basic", response_model=BasicReportResponse)
async def generate_basic_report(
    request: BasicReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    service = AuditService(db, str(current_user.tenant_id), StorageService())
    report = await service.report_generator.generate_report(
        request.period_start,
        request.period_end,
        request.expense_ids
    )

    return BasicReportResponse(**report)


@router.post("/reports/generate-narrative", response_model=NarrativeGenerationResponse)
async def generate_narrative(
    request: NarrativeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await require_audit_permission(current_user, db)

    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        # Get report data if report_id is provided
        report_data = request.report_data
        if request.report_id:
            report = await service.get_audit_report(request.report_id)
            if report:
                report_data = {
                    "technical_data": report.technical_data,
                    "narrative_sections": report.narrative_sections,
                    "metadata": report.metadata_,
                    "sample_size": report.sample_size,
                    "total_expenses_in_scope": report.total_expenses_in_scope,
                    "total_amount_in_scope": float(report.total_amount_in_scope)
                }
        
        # Generate narrative
        narratives = await service.narrative_generator.generate_report_narrative(
            report_data or {},
            request.period_start,
            request.period_end
        )
        
        # If report_id is provided, update the report with the generated narrative
        if request.report_id:
            report = await service.get_audit_report(request.report_id)
            if report:
                # Merge new narratives with existing ones
                existing_narratives = report.narrative_sections or {}
                updated_narratives = {**existing_narratives, **narratives}
                await service.update_audit_report(
                    request.report_id,
                    {"narrative_sections": updated_narratives}
                )
                await db.commit()
        
        return NarrativeGenerationResponse(
            success=True,
            narratives=narratives,
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        await db.rollback()
        logger.error("generate_narrative_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate narrative: {str(e)}"
        )


# -------------------------------------------------------------------
# METADATA
# -------------------------------------------------------------------

@router.post("/reports/{report_id}/metadata", response_model=AuditMetadataResponse)
async def add_report_metadata(
    report_id: str,
    request: AuditMetadataCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add metadata to audit report"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        # Verify report exists and belongs to tenant
        report = await service.get_audit_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # Add metadata
        metadata = await service.add_metadata(
            report_id=report_id,
            key=request.key,
            value=request.value,
            created_by=str(current_user.id)
        )
        
        await db.commit()
        
        return AuditMetadataResponse(
            id=str(metadata.id),
            key=metadata.key,
            value=metadata.value,
            data_type=metadata.data_type,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("add_metadata_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add metadata")


@router.get("/reports/{report_id}/metadata", response_model=List[AuditMetadataResponse])
async def get_report_metadata(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all metadata for audit report"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        # Verify report exists
        report = await service.get_audit_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # Get metadata
        metadata_list = await service.get_metadata(report_id)
        
        return [
            AuditMetadataResponse(
                id=str(m.id),
                key=m.key,
                value=m.value,
                data_type=m.data_type,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in metadata_list
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_metadata_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get metadata")


# -------------------------------------------------------------------
# POPULATE REPORT
# -------------------------------------------------------------------

@router.post("/reports/{report_id}/populate", response_model=Dict[str, Any])
async def populate_report(
    report_id: str,
    request: PopulateReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Populate audit report from sample expenses"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        result = await service.populate_report_from_sample(
            report_id=report_id,
            sample_expense_ids=request.sample_expense_ids,
            created_by=str(current_user.id)
        )
        
        await db.commit()
        
        return result
        
    except Exception as e:
        await db.rollback()
        logger.error("populate_report_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to populate report")


# -------------------------------------------------------------------
# EVIDENCE COLLECTION
# -------------------------------------------------------------------

@router.post("/reports/{report_id}/evidence/collect", response_model=EvidenceCollectionResponse)
async def collect_evidence(
    report_id: str,
    request: EvidenceCollectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Collect evidence for audit report from expense IDs"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        # Verify report exists
        report = await service.get_audit_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # Collect evidence
        result = await service.evidence_collector.collect_evidence_for_sample(
            audit_report_id=report_id,
            expense_ids=request.expense_ids,
            created_by=str(current_user.id)
        )
        
        await db.commit()
        
        # Format evidence items for response
        evidence_items = []
        if result.get("success"):
            # Get collected evidence items
            evidence_result = await db.execute(
                select(AuditEvidence).where(
                    and_(
                        AuditEvidence.audit_report_id == report_id,
                        AuditEvidence.tenant_id == current_user.tenant_id
                    )
                ).order_by(AuditEvidence.collected_at.desc())
            )
            evidence_list = evidence_result.scalars().all()
            
            evidence_items = [
                {
                    "id": str(e.id),
                    "evidence_type": e.evidence_type,
                    "evidence_category": e.evidence_category,
                    "description": e.description,
                    "expense_id": str(e.expense_id) if e.expense_id else None,
                    "receipt_id": str(e.receipt_id) if e.receipt_id else None,
                    "file_name": e.file_name,
                    "file_size": e.file_size,
                    "mime_type": e.mime_type,
                    "collected_at": e.collected_at.isoformat()
                }
                for e in evidence_list[-result.get("evidence_items_collected", 0):]
            ]
        
        return EvidenceCollectionResponse(
            success=result.get("success", False),
            audit_report_id=report_id,
            expenses_processed=result.get("expenses_processed", 0),
            evidence_items_collected=result.get("evidence_items_collected", 0),
            evidence_items=evidence_items,
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("collect_evidence_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to collect evidence")


@router.get("/reports/{report_id}/evidence/download")
async def download_evidence_zip(
    report_id: str,
    include_receipts: bool = Query(True),
    include_approvals: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download evidence as ZIP file"""
    await require_audit_permission(current_user, db)
    
    try:
        from fastapi.responses import StreamingResponse
        
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        # Verify report exists
        report = await service.get_audit_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # Get evidence items
        evidence_result = await db.execute(
            select(AuditEvidence).where(
                and_(
                    AuditEvidence.audit_report_id == report_id,
                    AuditEvidence.tenant_id == current_user.tenant_id
                )
            )
        )
        evidence_items = evidence_result.scalars().all()
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add evidence metadata
            evidence_metadata = {
                "report_id": report_id,
                "report_number": report.report_number,
                "collected_at": datetime.utcnow().isoformat(),
                "evidence_items": [
                    {
                        "id": str(e.id),
                        "type": e.evidence_type,
                        "category": e.evidence_category,
                        "description": e.description,
                        "expense_id": str(e.expense_id) if e.expense_id else None,
                        "receipt_id": str(e.receipt_id) if e.receipt_id else None,
                        "file_name": e.file_name
                    }
                    for e in evidence_items
                ]
            }
            zip_file.writestr("evidence_metadata.json", json.dumps(evidence_metadata, indent=2))
            
            # Add receipt files if requested
            if include_receipts:
                from services.file_service.models import ReceiptDocument
                for evidence in evidence_items:
                    if evidence.receipt_id:
                        receipt_result = await db.execute(
                            select(ReceiptDocument).where(
                                ReceiptDocument.id == evidence.receipt_id
                            )
                        )
                        receipt = receipt_result.scalar_one_or_none()
                        if receipt and service.storage_service:
                            try:
                                # Get file content from storage
                                if hasattr(service.storage_service, 'download_file'):
                                    file_content = await service.storage_service.download_file(
                                        receipt.storage_path
                                    )
                                    zip_file.writestr(f"receipts/{receipt.file_name}", file_content)
                            except Exception as e:
                                logger.warning("receipt_download_failed", receipt_id=str(evidence.receipt_id), error=str(e))
        
        zip_buffer.seek(0)
        
        # P1: Calculate SHA-256 hash of ZIP
        import hashlib
        zip_content = zip_buffer.getvalue()
        zip_hash = hashlib.sha256(zip_content).hexdigest()
        
        # Store hash in evidence metadata
        from .models import AuditMetadata
        hash_metadata = AuditMetadata(
            audit_report_id=report_id,
            tenant_id=current_user.tenant_id,
            key="evidence_pack_hash",
            value={"hash": zip_hash, "algorithm": "SHA-256", "created_at": datetime.utcnow().isoformat()},
            data_type="string",
            created_by=current_user.id
        )
        db.add(hash_metadata)
        await db.flush()
        
        logger.info(
            "evidence_pack_hash_stored",
            report_id=report_id,
            hash=zip_hash
        )
        
        # Reset buffer position for streaming
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=audit_evidence_{report.report_number}.zip",
                "X-Evidence-Pack-Hash": zip_hash,
                "X-Evidence-Pack-Hash-Algorithm": "SHA-256"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("download_evidence_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to download evidence")


@router.get("/reports/{report_id}/evidence/signed-urls", response_model=List[SignedUrlResponse])
async def get_evidence_signed_urls(
    report_id: str,
    expiration_seconds: int = Query(3600, ge=60, le=86400),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get signed URLs for evidence files"""
    await require_audit_permission(current_user, db)
    
    try:
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        # Verify report exists
        report = await service.get_audit_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Audit report not found")
        
        # Get evidence items with files
        evidence_result = await db.execute(
            select(AuditEvidence).where(
                and_(
                    AuditEvidence.audit_report_id == report_id,
                    AuditEvidence.tenant_id == current_user.tenant_id,
                    AuditEvidence.file_path.isnot(None)
                )
            )
        )
        evidence_items = evidence_result.scalars().all()
        
        signed_urls = []
        for evidence in evidence_items:
            if evidence.file_path and service.storage_service:
                try:
                    # Generate signed URL
                    if hasattr(service.storage_service, 'generate_signed_url'):
                        signed_url = await service.storage_service.generate_signed_url(
                            file_path=evidence.file_path,
                            expiration_seconds=expiration_seconds
                        )
                        
                        expires_at = (datetime.utcnow() + timedelta(seconds=expiration_seconds)).isoformat()
                        
                        signed_urls.append(SignedUrlResponse(
                            evidence_id=str(evidence.id),
                            file_name=evidence.file_name or "unknown",
                            file_size=evidence.file_size,
                            mime_type=evidence.mime_type,
                            signed_url=signed_url,
                            expires_at=expires_at,
                            evidence_type=evidence.evidence_type
                        ))
                except Exception as e:
                    logger.warning("signed_url_generation_failed", evidence_id=str(evidence.id), error=str(e))
        
        return signed_urls
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_signed_urls_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get signed URLs")


# -------------------------------------------------------------------
# SNAPSHOT VERIFICATION
# -------------------------------------------------------------------

@router.post("/snapshots/{snapshot_id}/verify", response_model=SnapshotVerificationResponse)
async def verify_snapshot(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify audit snapshot integrity"""
    await require_audit_permission(current_user, db)
    
    try:
        from .models import AuditSnapshot
        import hashlib
        
        service = AuditService(db, str(current_user.tenant_id), StorageService())
        
        # Get snapshot
        result = await db.execute(
            select(AuditSnapshot).where(
                and_(
                    AuditSnapshot.id == snapshot_id,
                    AuditSnapshot.tenant_id == current_user.tenant_id
                )
            )
        )
        snapshot = result.scalar_one_or_none()
        
        if not snapshot:
            return SnapshotVerificationResponse(
                valid=False,
                error="Snapshot not found"
            )
        
        # Calculate hash of snapshot data
        snapshot_json = json.dumps(snapshot.snapshot_data, sort_keys=True)
        calculated_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()
        
        # Compare with stored hash
        is_valid = calculated_hash == snapshot.snapshot_hash
        
        return SnapshotVerificationResponse(
            valid=is_valid,
            snapshot_id=str(snapshot.id),
            entity_type=snapshot.entity_type,
            entity_id=snapshot.entity_id,
            action=snapshot.action,
            created_at=snapshot.created_at.isoformat(),
            expected_hash=snapshot.snapshot_hash,
            calculated_hash=calculated_hash,
            error=None if is_valid else "Hash mismatch - data may have been tampered with"
        )
        
    except Exception as e:
        logger.error("verify_snapshot_error", error=str(e))
        return SnapshotVerificationResponse(
            valid=False,
            error=str(e)
        )
