"""
SQLAlchemy ORM models for the Tax Service.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base


class TaxDeclaration(Base):
    __tablename__ = "tax_declarations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    dossier_id = Column(UUID(as_uuid=True), ForeignKey("client_dossiers.id"))
    type = Column(String(20), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date)
    status = Column(String(20), default="draft")
    computed_data = Column(JSONB, default={})
    total_amount = Column(DECIMAL(15, 2), default=0)
    edi_file_path = Column(String(500))
    edi_transmission_id = Column(String(100))
    submitted_at = Column(DateTime(timezone=True))
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class TaxCalendar(Base):
    __tablename__ = "tax_calendar"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    dossier_id = Column(UUID(as_uuid=True), ForeignKey("client_dossiers.id"))
    declaration_type = Column(String(20), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(20), default="upcoming")
    declaration_id = Column(UUID(as_uuid=True), ForeignKey("tax_declarations.id"))
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
