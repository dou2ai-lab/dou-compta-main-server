# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: ERP service models
# -----------------------------------------------------------------------------

"""
ERP Service Models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from common.models import Base

class ERPConnection(Base):
    """ERP connection configuration"""
    __tablename__ = "erp_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Connection details
    provider = Column(String(50), nullable=False)  # sap, netsuite, odoo
    connection_type = Column(String(20), nullable=False)  # api, sftp
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Configuration (encrypted in production)
    configuration = Column(JSONB, default={})
    
    # Metadata
    last_sync_at = Column(DateTime(timezone=True))
    last_sync_status = Column(String(50))  # success, failed, pending
    last_error = Column(Text)
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))

class AccountingPosting(Base):
    """Accounting posting records"""
    __tablename__ = "accounting_postings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    erp_connection_id = Column(UUID(as_uuid=True), ForeignKey("erp_connections.id"))
    
    # Expense reference
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"), nullable=False)
    
    # Posting details
    posting_date = Column(DateTime(timezone=True), nullable=False)
    posting_type = Column(String(50), nullable=False)  # expense, vat, reimbursement
    gl_account = Column(String(100), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    
    # VAT segmentation
    vat_rate = Column(DECIMAL(5, 2))
    vat_amount = Column(DECIMAL(12, 2))
    vat_account = Column(String(100))
    vat_code = Column(String(50))  # French VAT code
    
    # ERP reference
    erp_document_id = Column(String(255))  # Reference in ERP system
    erp_status = Column(String(50))  # pending, posted, failed
    erp_error = Column(Text)
    
    # Metadata (using metadata_ to avoid SQLAlchemy reserved name conflict)
    metadata_ = Column(JSONB, default={})
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))

class SEPATransaction(Base):
    """SEPA transaction records"""
    __tablename__ = "sepa_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Transaction details
    transaction_id = Column(String(100), unique=True, nullable=False)  # Unique SEPA transaction ID
    creditor_name = Column(String(140), nullable=False)
    creditor_iban = Column(String(34), nullable=False)
    creditor_bic = Column(String(11))
    
    debtor_name = Column(String(140), nullable=False)
    debtor_iban = Column(String(34), nullable=False)
    debtor_bic = Column(String(11))
    
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    execution_date = Column(DateTime(timezone=True), nullable=False)
    
    # Reference
    remittance_info = Column(String(140))  # Payment reference
    expense_ids = Column(JSONB)  # Array of expense IDs
    
    # Status
    status = Column(String(50), nullable=False, default="pending")  # pending, exported, executed, failed
    sepa_file_id = Column(UUID(as_uuid=True), ForeignKey("sepa_files.id"))
    
    # Metadata (using metadata_ to avoid SQLAlchemy reserved name conflict)
    metadata_ = Column(JSONB, default={})
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class SEPAFile(Base):
    """SEPA export file"""
    __tablename__ = "sepa_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # File details
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    transaction_count = Column(Integer, default=0)
    total_amount = Column(DECIMAL(12, 2), default=0)
    
    # Status
    status = Column(String(50), nullable=False, default="pending")  # pending, generated, exported, executed
    exported_at = Column(DateTime(timezone=True))
    executed_at = Column(DateTime(timezone=True))
    
    # Metadata (using metadata_ to avoid SQLAlchemy reserved name conflict)
    metadata_ = Column(JSONB, default={})
    
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transactions = relationship("SEPATransaction", backref="sepa_file")

class CardPaymentReconciliation(Base):
    """Card payment reconciliation records"""
    __tablename__ = "card_payment_reconciliations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Card payment details
    card_transaction_id = Column(String(255), nullable=False)
    card_last_four = Column(String(4))
    merchant_name = Column(String(255))
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    
    # Reconciliation
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"))
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"))
    
    # Matching
    match_confidence = Column(DECIMAL(5, 2))  # 0-100
    match_method = Column(String(50))  # automatic, manual, fuzzy
    match_score = Column(DECIMAL(5, 2))
    
    # Status
    status = Column(String(50), nullable=False, default="pending")  # pending, matched, unmatched, reviewed
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))




