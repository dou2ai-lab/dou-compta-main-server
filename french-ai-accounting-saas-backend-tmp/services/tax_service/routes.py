"""
Tax Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .service import TaxService
from .schemas import (
    ComputeDeclarationRequest, TaxDeclarationResponse, TaxDeclarationListResponse,
    TaxCalendarResponse, PenaltyWarning,
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/declarations", response_model=TaxDeclarationListResponse)
async def list_declarations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = TaxService(db)
    declarations, total = await svc.list_declarations(
        current_user.tenant_id, page, page_size, type, status,
    )
    return TaxDeclarationListResponse(
        data=[TaxDeclarationResponse(
            id=d.id, tenant_id=d.tenant_id, dossier_id=d.dossier_id,
            type=d.type, period_start=d.period_start, period_end=d.period_end,
            due_date=d.due_date, status=d.status, computed_data=d.computed_data,
            total_amount=d.total_amount, edi_file_path=d.edi_file_path,
            submitted_at=d.submitted_at, validated_at=d.validated_at,
            notes=d.notes, created_at=d.created_at,
        ) for d in declarations],
        total=total, page=page, page_size=page_size,
    )


@router.get("/declarations/{declaration_id}", response_model=TaxDeclarationResponse)
async def get_declaration(
    declaration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = TaxService(db)
    decl = await svc.get_declaration(current_user.tenant_id, declaration_id)
    if not decl:
        raise HTTPException(status_code=404, detail="Declaration non trouvee")
    return TaxDeclarationResponse(
        id=decl.id, tenant_id=decl.tenant_id, dossier_id=decl.dossier_id,
        type=decl.type, period_start=decl.period_start, period_end=decl.period_end,
        due_date=decl.due_date, status=decl.status, computed_data=decl.computed_data,
        total_amount=decl.total_amount, edi_file_path=decl.edi_file_path,
        submitted_at=decl.submitted_at, validated_at=decl.validated_at,
        notes=decl.notes, created_at=decl.created_at,
    )


@router.post("/declarations/compute", response_model=TaxDeclarationResponse)
async def compute_declaration(
    request: ComputeDeclarationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute a tax declaration from journal entries."""
    svc = TaxService(db)
    decl = await svc.compute_declaration(
        current_user.tenant_id,
        request.type.value,
        request.period_start,
        request.period_end,
        request.dossier_id,
    )
    await db.commit()
    return TaxDeclarationResponse(
        id=decl.id, tenant_id=decl.tenant_id, dossier_id=decl.dossier_id,
        type=decl.type, period_start=decl.period_start, period_end=decl.period_end,
        due_date=decl.due_date, status=decl.status, computed_data=decl.computed_data,
        total_amount=decl.total_amount, edi_file_path=decl.edi_file_path,
        submitted_at=decl.submitted_at, validated_at=decl.validated_at,
        notes=decl.notes, created_at=decl.created_at,
    )


@router.post("/declarations/{declaration_id}/validate")
async def validate_declaration(
    declaration_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = TaxService(db)
    decl = await svc.validate_declaration(current_user.tenant_id, declaration_id, current_user.id)
    if not decl:
        raise HTTPException(status_code=404, detail="Declaration non trouvee")
    await db.commit()
    return {"success": True, "status": decl.status}


@router.get("/calendar", response_model=list[TaxCalendarResponse])
async def get_calendar(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = TaxService(db)
    items = await svc.get_calendar(current_user.tenant_id, year)
    return [TaxCalendarResponse(
        id=i.id, declaration_type=i.declaration_type, due_date=i.due_date,
        status=i.status, declaration_id=i.declaration_id,
        reminder_sent=i.reminder_sent, notes=i.notes, created_at=i.created_at,
    ) for i in items]


@router.get("/penalties", response_model=list[PenaltyWarning])
async def get_penalties(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detect overdue declarations and estimate penalties."""
    svc = TaxService(db)
    warnings = await svc.get_penalties(current_user.tenant_id)
    return [PenaltyWarning(**w) for w in warnings]


@router.get("/upcoming")
async def get_upcoming(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get upcoming tax deadlines."""
    svc = TaxService(db)
    return await svc.get_upcoming(current_user.tenant_id, days)
