"""
SQLAlchemy ORM models for the Dossier Service.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from common.models import Base


class ClientDossier(Base):
    __tablename__ = "client_dossiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_name = Column(String(255), nullable=False)
    siren = Column(String(9))
    siret = Column(String(14))
    legal_form = Column(String(50))
    naf_code = Column(String(10))
    fiscal_year_start = Column(Date)
    fiscal_year_end = Column(Date)
    regime_tva = Column(String(20), default="reel_normal")
    regime_is = Column(String(20), default="is_normal")
    accountant_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(20), default="active")
    settings = Column(JSONB, default={})
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    postal_code = Column(String(10))
    city = Column(String(100))
    country = Column(String(2), default="FR")
    phone = Column(String(20))
    email = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("DossierDocument", back_populates="dossier", cascade="all, delete-orphan")
    timeline = relationship("DossierTimeline", back_populates="dossier", cascade="all, delete-orphan")


class DossierDocument(Base):
    __tablename__ = "dossier_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dossier_id = Column(UUID(as_uuid=True), ForeignKey("client_dossiers.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    dossier = relationship("ClientDossier", back_populates="documents")


class DossierTimeline(Base):
    __tablename__ = "dossier_timeline"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dossier_id = Column(UUID(as_uuid=True), ForeignKey("client_dossiers.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    meta_data = Column("meta_data", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    dossier = relationship("ClientDossier", back_populates="timeline")
