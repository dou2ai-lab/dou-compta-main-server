# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Description: Audit service models
# -----------------------------------------------------------------------------

"""
Audit Service Models
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    DECIMAL,
    Date,
    Integer,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from common.models import Base


class AuditReport(Base):
    """Audit Report model"""

    __tablename__ = "audit_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Identification
    report_number = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)

    # Period
    audit_period_start = Column(Date, nullable=False)
    audit_period_end = Column(Date, nullable=False)
    period_type = Column(String(50))

    # Structure
    report_type = Column(String(50), nullable=False, default="technical")
    template_version = Column(String(20), nullable=False, default="1.0")

    # Workflow
    status = Column(String(50), nullable=False, default="draft")
    completed_at = Column(DateTime(timezone=True))
    published_at = Column(DateTime(timezone=True))

    # JSON fields (CORRECT MAPPING)
    metadata_ = Column("metadata", JSONB, default=dict)
    technical_data = Column(JSONB, default=dict)
    narrative_sections = Column(JSONB, default=dict)

    # Sample info
    sample_size = Column(Integer, default=0)
    total_expenses_in_scope = Column(Integer, default=0)
    total_amount_in_scope = Column(DECIMAL(12, 2), default=0)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    deleted_at = Column(DateTime(timezone=True))

    # Relationships
    evidence_items = relationship(
        "AuditEvidence",
        back_populates="audit_report",
        cascade="all, delete-orphan",
    )
    audit_metadata = relationship(
        "AuditMetadata",
        back_populates="audit_report",
        cascade="all, delete-orphan",
    )


class AuditMetadata(Base):
    """Audit metadata tracking"""

    __tablename__ = "audit_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_report_id = Column(
        UUID(as_uuid=True), ForeignKey("audit_reports.id"), nullable=False
    )
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    key = Column(String(100), nullable=False)
    value = Column(JSONB, nullable=False)
    data_type = Column(String(50))

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    audit_report = relationship("AuditReport", back_populates="audit_metadata")


class AuditEvidence(Base):
    """Audit evidence items"""

    __tablename__ = "audit_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_report_id = Column(
        UUID(as_uuid=True), ForeignKey("audit_reports.id"), nullable=False
    )
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"))
    receipt_id = Column(UUID(as_uuid=True))
    approval_step_id = Column(UUID(as_uuid=True))

    evidence_type = Column(String(50), nullable=False)
    evidence_category = Column(String(50))
    description = Column(Text)

    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    storage_provider = Column(String(50))
    storage_key = Column(String(500))

    collected_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    collected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    metadata_ = Column("metadata", JSONB, default=dict)

    audit_report = relationship("AuditReport", back_populates="evidence_items")


class AuditScope(Base):
    """Audit scope definition"""

    __tablename__ = "audit_scopes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_report_id = Column(
        UUID(as_uuid=True), ForeignKey("audit_reports.id"), nullable=False
    )
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    scope_type = Column(String(50), nullable=False)
    scope_value = Column(String(255))
    scope_criteria = Column(JSONB, default=dict)

    is_included = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class AuditTrail(Base):
    """Audit trail tracking"""

    __tablename__ = "audit_trails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)

    action = Column(String(50), nullable=False)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    metadata_ = Column("metadata", JSONB, default=dict)

    snapshots = relationship(
        "AuditSnapshot",
        back_populates="audit_trail",
        cascade="all, delete-orphan",
    )


class AuditSnapshot(Base):
    """Immutable snapshot storage"""

    __tablename__ = "audit_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    audit_trail_id = Column(
        UUID(as_uuid=True), ForeignKey("audit_trails.id"), nullable=False
    )

    action = Column(String(50), nullable=False)
    snapshot_data = Column(JSONB, nullable=False)
    snapshot_hash = Column(String(64), nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    audit_trail = relationship("AuditTrail", back_populates="snapshots")
