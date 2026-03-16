"""
Pydantic schemas for the Dossier Service API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from enum import Enum


class LegalForm(str, Enum):
    SARL = "SARL"
    SAS = "SAS"
    SA = "SA"
    EI = "EI"
    EURL = "EURL"
    SCI = "SCI"
    SNC = "SNC"
    SASU = "SASU"
    AUTO = "AUTO"


class RegimeTVA(str, Enum):
    REEL_NORMAL = "reel_normal"
    REEL_SIMPLIFIE = "reel_simplifie"
    MINI_REEL = "mini_reel"
    FRANCHISE = "franchise"


class RegimeIS(str, Enum):
    IS_NORMAL = "is_normal"
    IS_PME = "is_pme"
    IR = "ir"
    MICRO = "micro"


class DossierStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


# --- Request schemas ---

class DossierCreate(BaseModel):
    client_name: str = Field(..., max_length=255)
    siren: Optional[str] = Field(None, max_length=9)
    siret: Optional[str] = Field(None, max_length=14)
    legal_form: Optional[str] = None
    naf_code: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    regime_tva: Optional[str] = "reel_normal"
    regime_is: Optional[str] = "is_normal"
    accountant_id: Optional[UUID] = None
    settings: Optional[dict] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "FR"
    phone: Optional[str] = None
    email: Optional[str] = None


class DossierUpdate(BaseModel):
    client_name: Optional[str] = None
    siren: Optional[str] = None
    siret: Optional[str] = None
    legal_form: Optional[str] = None
    naf_code: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    regime_tva: Optional[str] = None
    regime_is: Optional[str] = None
    accountant_id: Optional[UUID] = None
    status: Optional[str] = None
    settings: Optional[dict] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class DossierDocumentCreate(BaseModel):
    document_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


# --- Response schemas ---

class DossierDocumentResponse(BaseModel):
    id: UUID
    dossier_id: UUID
    document_type: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TimelineEventResponse(BaseModel):
    id: UUID
    dossier_id: UUID
    event_type: str
    title: str
    description: Optional[str] = None
    performed_by: Optional[UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    meta_data: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DossierResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    client_name: str
    siren: Optional[str] = None
    siret: Optional[str] = None
    legal_form: Optional[str] = None
    naf_code: Optional[str] = None
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None
    regime_tva: Optional[str] = None
    regime_is: Optional[str] = None
    accountant_id: Optional[UUID] = None
    status: str
    settings: Optional[dict] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DossierListResponse(BaseModel):
    data: List[DossierResponse]
    total: int
    page: int
    page_size: int


class DossierSummaryResponse(BaseModel):
    dossier: DossierResponse
    document_count: int
    recent_events: List[TimelineEventResponse]
    entry_count: int
    total_debit: float
    total_credit: float
