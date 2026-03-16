"""
Dossier Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .service import DossierService
from .schemas import (
    DossierCreate, DossierUpdate, DossierResponse, DossierListResponse,
    DossierDocumentCreate, DossierDocumentResponse,
    TimelineEventResponse, DossierSummaryResponse,
)

logger = structlog.get_logger()
router = APIRouter()


def dossier_to_response(d) -> DossierResponse:
    return DossierResponse(
        id=d.id, tenant_id=d.tenant_id, client_name=d.client_name,
        siren=d.siren, siret=d.siret, legal_form=d.legal_form,
        naf_code=d.naf_code, fiscal_year_start=d.fiscal_year_start,
        fiscal_year_end=d.fiscal_year_end, regime_tva=d.regime_tva,
        regime_is=d.regime_is, accountant_id=d.accountant_id,
        status=d.status, settings=d.settings,
        address_line1=d.address_line1, address_line2=d.address_line2,
        postal_code=d.postal_code, city=d.city, country=d.country,
        phone=d.phone, email=d.email,
        created_at=d.created_at, updated_at=d.updated_at,
    )


@router.get("", response_model=DossierListResponse)
async def list_dossiers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    accountant_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    dossiers, total = await svc.list_dossiers(
        current_user.tenant_id, page, page_size, status, search, accountant_id,
    )
    return DossierListResponse(
        data=[dossier_to_response(d) for d in dossiers],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=DossierResponse)
async def create_dossier(
    payload: DossierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    dossier = await svc.create_dossier(
        tenant_id=current_user.tenant_id,
        **payload.model_dump(exclude_none=True),
    )
    await db.commit()
    return dossier_to_response(dossier)


@router.get("/{dossier_id}", response_model=DossierResponse)
async def get_dossier(
    dossier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    dossier = await svc.get_dossier(current_user.tenant_id, dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouve")
    return dossier_to_response(dossier)


@router.put("/{dossier_id}", response_model=DossierResponse)
async def update_dossier(
    dossier_id: UUID,
    payload: DossierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    dossier = await svc.update_dossier(
        current_user.tenant_id, dossier_id, current_user.id,
        **payload.model_dump(exclude_none=True),
    )
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouve")
    await db.commit()
    return dossier_to_response(dossier)


@router.get("/{dossier_id}/summary", response_model=DossierSummaryResponse)
async def get_dossier_summary(
    dossier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    summary = await svc.get_summary(current_user.tenant_id, dossier_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Dossier non trouve")
    return DossierSummaryResponse(
        dossier=dossier_to_response(summary["dossier"]),
        document_count=summary["document_count"],
        recent_events=[
            TimelineEventResponse(
                id=e.id, dossier_id=e.dossier_id, event_type=e.event_type,
                title=e.title, description=e.description,
                performed_by=e.performed_by, entity_type=e.entity_type,
                entity_id=e.entity_id, meta_data=e.meta_data,
                created_at=e.created_at,
            ) for e in summary["recent_events"]
        ],
        entry_count=summary["entry_count"],
        total_debit=summary["total_debit"],
        total_credit=summary["total_credit"],
    )


@router.get("/{dossier_id}/timeline", response_model=list[TimelineEventResponse])
async def get_timeline(
    dossier_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    events = await svc.get_timeline(dossier_id, page, page_size)
    return [
        TimelineEventResponse(
            id=e.id, dossier_id=e.dossier_id, event_type=e.event_type,
            title=e.title, description=e.description,
            performed_by=e.performed_by, entity_type=e.entity_type,
            entity_id=e.entity_id, meta_data=e.meta_data,
            created_at=e.created_at,
        ) for e in events
    ]


@router.get("/{dossier_id}/documents", response_model=list[DossierDocumentResponse])
async def list_documents(
    dossier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    docs = await svc.list_documents(dossier_id)
    return [
        DossierDocumentResponse(
            id=d.id, dossier_id=d.dossier_id, document_type=d.document_type,
            title=d.title, description=d.description,
            file_path=d.file_path, file_size=d.file_size,
            mime_type=d.mime_type, created_at=d.created_at,
        ) for d in docs
    ]


@router.post("/{dossier_id}/documents", response_model=DossierDocumentResponse)
async def add_document(
    dossier_id: UUID,
    payload: DossierDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = DossierService(db)
    doc = await svc.add_document(
        dossier_id, current_user.id,
        **payload.model_dump(),
    )
    await db.commit()
    return DossierDocumentResponse(
        id=doc.id, dossier_id=doc.dossier_id, document_type=doc.document_type,
        title=doc.title, description=doc.description,
        file_path=doc.file_path, file_size=doc.file_size,
        mime_type=doc.mime_type, created_at=doc.created_at,
    )
