# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: GDPR service models
# -----------------------------------------------------------------------------

"""
GDPR Service Models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base

class DataSubjectRequest(Base):
    """Data subject request (GDPR Article 15, 16, 17, 20)"""
    __tablename__ = "data_subject_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Request details
    request_type = Column(String(50), nullable=False)  # access, rectification, erasure, portability
    subject_email = Column(String(255), nullable=False)
    subject_name = Column(String(255))
    subject_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))  # If user exists
    
    # Request status
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, rejected
    requested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    
    # Response
    response_data = Column(JSONB)  # Exported data
    response_file_path = Column(String(500))  # Path to exported file
    
    # Verification
    verification_token = Column(String(100), unique=True)
    verified_at = Column(DateTime(timezone=True))
    
    # Processing
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason = Column(Text)
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))

class RetentionRule(Base):
    """Data retention rules"""
    __tablename__ = "retention_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Rule details
    entity_type = Column(String(100), nullable=False)  # expense, receipt, user, log, etc.
    retention_years = Column(Integer, nullable=False)
    retention_days = Column(Integer)  # Additional days if needed
    
    # Action
    action_on_expiry = Column(String(50), nullable=False, default="archive")  # archive, delete, anonymize
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True))
    next_run_at = Column(DateTime(timezone=True))
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))

class PrivacyLog(Base):
    """Privacy access logging"""
    __tablename__ = "privacy_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Access details
    accessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(100), nullable=False)  # expense, receipt, user, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Access type
    access_type = Column(String(50), nullable=False)  # read, update, delete, export
    contains_pii = Column(Boolean, default=False)
    
    # Context
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    request_path = Column(String(500))
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class DataMinimizationJob(Base):
    """Data minimization job tracking"""
    __tablename__ = "data_minimization_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Job details
    entity_type = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # anonymize, delete, archive
    records_processed = Column(Integer, default=0)
    records_affected = Column(Integer, default=0)
    
    # Status
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Error handling
    error_message = Column(Text)
    
    # Metadata
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)




