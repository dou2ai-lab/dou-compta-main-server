"""
Models for human-in-the-loop feedback + training dataset logging + extraction cache.
"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from common.models import Base


class ReceiptFieldCorrection(Base):
    __tablename__ = "receipt_field_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipt_documents.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    field_name = Column(String(100), nullable=False)
    predicted_value = Column(JSONB, nullable=True)
    corrected_value = Column(JSONB, nullable=True)
    predicted_snapshot = Column(JSONB, nullable=True)  # extraction object at time of correction
    ocr_snapshot = Column(JSONB, nullable=True)
    llm_snapshot = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class ReceiptTrainingSnapshot(Base):
    __tablename__ = "receipt_training_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipt_documents.id"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    file_hash = Column(String(64), nullable=True, index=True)
    document_type = Column(String(50), nullable=True)

    ocr_output = Column(JSONB, nullable=True)
    llm_output = Column(JSONB, nullable=True)
    extraction_output = Column(JSONB, nullable=True)
    corrected_output = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ReceiptExtractionCache(Base):
    __tablename__ = "receipt_extraction_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_hash = Column(String(64), nullable=False)
    document_type = Column(String(50), nullable=False)
    extraction_output = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("file_hash", "document_type", name="uq_receipt_extraction_cache_filehash_doctype"),
    )

