"""
SQLAlchemy ORM models for the Accounting Service.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, Date, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from common.models import Base


class PCGAccount(Base):
    __tablename__ = "pcg_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    account_code = Column(String(10), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_class = Column(Integer, nullable=False)
    account_type = Column(String(50), nullable=False)
    parent_code = Column(String(10))
    is_system = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ThirdParty(Base):
    __tablename__ = "third_parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    type = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    siren = Column(String(9))
    siret = Column(String(14))
    vat_number = Column(String(20))
    default_account_code = Column(String(10))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class FiscalPeriod(Base):
    __tablename__ = "fiscal_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    period_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="open")
    closed_at = Column(DateTime(timezone=True))
    closed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entry_number = Column(String(50), nullable=False)
    journal_code = Column(String(5), nullable=False)
    entry_date = Column(Date, nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")
    source_type = Column(String(50))
    source_id = Column(UUID(as_uuid=True))
    fiscal_year = Column(Integer, nullable=False)
    fiscal_period = Column(Integer, nullable=False)
    total_debit = Column(DECIMAL(15, 2), default=0)
    total_credit = Column(DECIMAL(15, 2), default=0)
    is_balanced = Column(Boolean, default=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    validated_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    account_code = Column(String(10), nullable=False)
    account_name = Column(String(255))
    debit = Column(DECIMAL(15, 2), default=0)
    credit = Column(DECIMAL(15, 2), default=0)
    label = Column(Text)
    vat_rate = Column(DECIMAL(5, 2))
    vat_amount = Column(DECIMAL(15, 2))
    third_party_id = Column(UUID(as_uuid=True), ForeignKey("third_parties.id"))
    lettering_code = Column(String(10))
    lettered_at = Column(DateTime(timezone=True))
    currency = Column(String(3), default="EUR")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    entry = relationship("JournalEntry", back_populates="lines")
