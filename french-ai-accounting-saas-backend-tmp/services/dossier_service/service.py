"""
Dossier Service - Business logic layer.
"""
import structlog
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID
from datetime import datetime

from .models import ClientDossier, DossierDocument, DossierTimeline

logger = structlog.get_logger()


class DossierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_dossiers(
        self,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
        accountant_id: Optional[UUID] = None,
    ) -> tuple[list[ClientDossier], int]:
        query = select(ClientDossier).where(ClientDossier.tenant_id == tenant_id)
        count_query = select(func.count(ClientDossier.id)).where(ClientDossier.tenant_id == tenant_id)

        if status:
            query = query.where(ClientDossier.status == status)
            count_query = count_query.where(ClientDossier.status == status)
        if search:
            like = f"%{search}%"
            query = query.where(
                ClientDossier.client_name.ilike(like) | ClientDossier.siren.ilike(like)
            )
            count_query = count_query.where(
                ClientDossier.client_name.ilike(like) | ClientDossier.siren.ilike(like)
            )
        if accountant_id:
            query = query.where(ClientDossier.accountant_id == accountant_id)
            count_query = count_query.where(ClientDossier.accountant_id == accountant_id)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(ClientDossier.client_name)
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_dossier(self, tenant_id: UUID, dossier_id: UUID) -> Optional[ClientDossier]:
        result = await self.db.execute(
            select(ClientDossier).where(
                ClientDossier.id == dossier_id,
                ClientDossier.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_dossier(self, tenant_id: UUID, **kwargs) -> ClientDossier:
        dossier = ClientDossier(tenant_id=tenant_id, **kwargs)
        self.db.add(dossier)
        await self.db.flush()

        # Add timeline event
        await self._add_timeline(
            dossier.id,
            "created",
            f"Dossier cree: {dossier.client_name}",
            performed_by=kwargs.get("accountant_id"),
        )
        return dossier

    async def update_dossier(
        self, tenant_id: UUID, dossier_id: UUID, user_id: UUID, **kwargs
    ) -> Optional[ClientDossier]:
        dossier = await self.get_dossier(tenant_id, dossier_id)
        if not dossier:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(dossier, key):
                setattr(dossier, key, value)
        dossier.updated_at = datetime.utcnow()
        await self.db.flush()

        await self._add_timeline(
            dossier_id, "updated", "Dossier mis a jour",
            performed_by=user_id,
        )
        return dossier

    async def get_summary(self, tenant_id: UUID, dossier_id: UUID) -> Optional[dict]:
        dossier = await self.get_dossier(tenant_id, dossier_id)
        if not dossier:
            return None

        # Document count
        doc_result = await self.db.execute(
            select(func.count(DossierDocument.id)).where(
                DossierDocument.dossier_id == dossier_id
            )
        )
        doc_count = doc_result.scalar() or 0

        # Recent timeline events
        timeline_result = await self.db.execute(
            select(DossierTimeline).where(
                DossierTimeline.dossier_id == dossier_id
            ).order_by(DossierTimeline.created_at.desc()).limit(10)
        )
        recent_events = list(timeline_result.scalars().all())

        # Journal entry stats (if dossier has SIREN linked to entries)
        entry_count = 0
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        try:
            from services.accounting_service.models import JournalEntry
            entry_result = await self.db.execute(
                select(
                    func.count(JournalEntry.id),
                    func.coalesce(func.sum(JournalEntry.total_debit), 0),
                    func.coalesce(func.sum(JournalEntry.total_credit), 0),
                ).where(JournalEntry.tenant_id == tenant_id)
            )
            row = entry_result.one()
            entry_count = row[0]
            total_debit = row[1]
            total_credit = row[2]
        except Exception:
            pass

        return {
            "dossier": dossier,
            "document_count": doc_count,
            "recent_events": recent_events,
            "entry_count": entry_count,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
        }

    async def get_timeline(
        self, dossier_id: UUID, page: int = 1, page_size: int = 50
    ) -> list[DossierTimeline]:
        result = await self.db.execute(
            select(DossierTimeline).where(
                DossierTimeline.dossier_id == dossier_id
            ).order_by(DossierTimeline.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all())

    async def list_documents(self, dossier_id: UUID) -> list[DossierDocument]:
        result = await self.db.execute(
            select(DossierDocument).where(
                DossierDocument.dossier_id == dossier_id
            ).order_by(DossierDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def add_document(
        self, dossier_id: UUID, user_id: UUID, **kwargs
    ) -> DossierDocument:
        doc = DossierDocument(dossier_id=dossier_id, uploaded_by=user_id, **kwargs)
        self.db.add(doc)
        await self.db.flush()

        await self._add_timeline(
            dossier_id, "document_added",
            f"Document ajoute: {kwargs.get('title', '')}",
            performed_by=user_id,
            entity_type="document",
            entity_id=doc.id,
        )
        return doc

    async def _add_timeline(
        self,
        dossier_id: UUID,
        event_type: str,
        title: str,
        description: str = None,
        performed_by: UUID = None,
        entity_type: str = None,
        entity_id: UUID = None,
    ):
        event = DossierTimeline(
            dossier_id=dossier_id,
            event_type=event_type,
            title=title,
            description=description,
            performed_by=performed_by,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.db.add(event)
        await self.db.flush()
