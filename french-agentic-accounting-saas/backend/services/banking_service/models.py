"""
SQLAlchemy ORM models for the Banking Service.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from common.models import Base


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    account_name = Column(String(255), nullable=False)
    iban = Column(String(34))
    bic = Column(String(11))
    bank_name = Column(String(255))
    currency = Column(String(3), default="EUR")
    balance = Column(DECIMAL(15, 2), default=0)
    balance_date = Column(Date)
    pcg_account_code = Column(String(10), default="512000")
    connection_type = Column(String(20), default="manual")
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True))
    settings = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    statements = relationship("BankStatement", back_populates="bank_account", cascade="all, delete-orphan")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")


class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False)
    statement_date = Column(Date, nullable=False)
    period_start = Column(Date)
    period_end = Column(Date)
    opening_balance = Column(DECIMAL(15, 2))
    closing_balance = Column(DECIMAL(15, 2))
    transaction_count = Column(Integer, default=0)
    file_path = Column(String(500))
    file_format = Column(String(20))
    import_status = Column(String(20), default="pending")
    error_message = Column(Text)
    imported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    bank_account = relationship("BankAccount", back_populates="statements")
    transactions = relationship("BankTransaction", back_populates="statement")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False)
    statement_id = Column(UUID(as_uuid=True), ForeignKey("bank_statements.id"))
    transaction_date = Column(Date, nullable=False)
    value_date = Column(Date)
    amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(3), default="EUR")
    label = Column(Text, nullable=False)
    reference = Column(String(100))
    counterparty_name = Column(String(255))
    counterparty_iban = Column(String(34))
    transaction_type = Column(String(50))
    category = Column(String(100))
    reconciliation_status = Column(String(20), default="unmatched")
    matched_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entries.id"))
    match_confidence = Column(DECIMAL(5, 4))
    matched_at = Column(DateTime(timezone=True))
    matched_by = Column(String(20))
    raw_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    bank_account = relationship("BankAccount", back_populates="transactions")
    statement = relationship("BankStatement", back_populates="transactions")


class ReconciliationRule(Base):
    __tablename__ = "reconciliation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    match_criteria = Column(JSONB, nullable=False, default={})
    target_account_code = Column(String(10))
    target_journal_code = Column(String(5), default="BNQ")
    auto_apply = Column(Boolean, default=False)
    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
