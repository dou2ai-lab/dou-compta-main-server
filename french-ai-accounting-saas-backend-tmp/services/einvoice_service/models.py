"""SQLAlchemy ORM models for Electronic Invoicing."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, DECIMAL, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from common.models import Base

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    dossier_id = Column(UUID(as_uuid=True), ForeignKey("client_dossiers.id"))
    invoice_number = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)
    format = Column(String(20), default="facturx")
    status = Column(String(20), default="draft")
    issuer_name = Column(String(255))
    issuer_siren = Column(String(9))
    issuer_vat_number = Column(String(20))
    recipient_name = Column(String(255))
    recipient_siren = Column(String(9))
    recipient_vat_number = Column(String(20))
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date)
    total_ht = Column(DECIMAL(15, 2), default=0)
    total_vat = Column(DECIMAL(15, 2), default=0)
    total_ttc = Column(DECIMAL(15, 2), default=0)
    currency = Column(String(3), default="EUR")
    xml_payload = Column(Text)
    pdf_path = Column(String(500))
    ppf_transmission_id = Column(String(100))
    ppf_status = Column(String(50))
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))
    notes = Column(Text)
    meta_data = Column("meta_data", JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(DECIMAL(12, 4), default=1)
    unit_price = Column(DECIMAL(15, 4), nullable=False)
    vat_rate = Column(DECIMAL(5, 2), default=20)
    line_total_ht = Column(DECIMAL(15, 2), nullable=False)
    line_total_vat = Column(DECIMAL(15, 2), default=0)
    account_code = Column(String(10))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    invoice = relationship("Invoice", back_populates="lines")
