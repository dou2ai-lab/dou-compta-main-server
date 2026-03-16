# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: SQLAlchemy database models for receipt documents and file metadata
# -----------------------------------------------------------------------------

"""
SQLAlchemy models for File Service
"""
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base

class ReceiptDocument(Base):
    """Receipt document model"""
    __tablename__ = "receipt_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"), nullable=True)
    file_name = Column(String(255), nullable=False)  # Encrypted in production
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    storage_path = Column(String(500), nullable=False)
    encryption_key_id = Column(String(255))
    file_hash = Column(String(64))  # SHA-256
    upload_status = Column(String(50), default="pending")
    ocr_status = Column(String(50), default="pending")
    ocr_job_id = Column(UUID(as_uuid=True), nullable=True)
    ocr_completed_at = Column(DateTime(timezone=True), nullable=True)
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)









