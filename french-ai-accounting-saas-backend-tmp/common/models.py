# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: SQLAlchemy database models for common entities
# -----------------------------------------------------------------------------

"""
SQLAlchemy database models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Tenant(Base):
    """Tenant model"""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    domain = Column(String(255))
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    # DB column is named "metadata" but SQLAlchemy reserves "metadata" on models.
    # Keep Python attribute as meta_data while mapping to DB column "metadata".
    meta_data = Column("metadata", JSONB, default={})
    
    users = relationship("User", back_populates="tenant")
    roles = relationship("Role", back_populates="tenant")

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    password_hash = Column(String(255))
    sso_provider = Column(String(50))
    sso_subject_id = Column(String(255))
    status = Column(String(50), nullable=False, default="active")
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    meta_data = Column("metadata", JSONB, default={})
    
    tenant = relationship("Tenant", back_populates="users")
    roles = relationship("UserRole", back_populates="user", foreign_keys="UserRole.user_id")
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    manager = relationship("User", remote_side=[id], foreign_keys=[manager_id])

class Role(Base):
    """Role model"""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_system_role = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    tenant = relationship("Tenant", back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role")

class Permission(Base):
    """Permission model"""
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    roles = relationship("RolePermission", back_populates="permission")

class RolePermission(Base):
    """Role-Permission junction table"""
    __tablename__ = "role_permissions"
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)
    
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")

class UserRole(Base):
    """User-Role junction table"""
    __tablename__ = "user_roles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")

class Expense(Base):
    """Expense model"""
    __tablename__ = "expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(DECIMAL(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    expense_date = Column(Date, nullable=False)
    category = Column(String(100))
    description = Column(Text)
    merchant_name = Column(String(255))
    status = Column(String(50), nullable=False, default="draft")
    approval_status = Column(String(50))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    vat_amount = Column(DECIMAL(12, 2))
    vat_rate = Column(DECIMAL(5, 2))
    expense_report_id = Column(UUID(as_uuid=True), ForeignKey("expense_reports.id"), nullable=True)
    policy_violation_count = Column(Integer, nullable=False, default=0)
    has_policy_violations = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    meta_data = Column("metadata", JSONB, default={})
    # Agentic Audit: risk and anomaly (5.2.2)
    risk_score_line = Column(DECIMAL(5, 4))
    is_anomaly = Column(Boolean, default=False)
    anomaly_reasons = Column(JSONB, default=[])

class ExpenseReport(Base):
    """Expense report model"""
    __tablename__ = "expense_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    report_number = Column(String(50), nullable=False)
    report_type = Column(String(50), nullable=False, default="period")
    title = Column(String(255))
    description = Column(Text)
    period_start_date = Column(Date)
    period_end_date = Column(Date)
    period_type = Column(String(20))
    trip_name = Column(String(255))
    trip_start_date = Column(Date)
    trip_end_date = Column(Date)
    trip_destination = Column(String(255))
    total_amount = Column(DECIMAL(12, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="EUR")
    expense_count = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="draft")
    approval_status = Column(String(50))
    submitted_at = Column(DateTime(timezone=True))
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True))
    rejected_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    approval_notes = Column(Text)
    meta_data = Column("meta_data", JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))
    
    expenses = relationship("Expense", foreign_keys="Expense.expense_report_id")

class ExpenseReportItem(Base):
    """Expense report item junction table"""
    __tablename__ = "expense_report_items"
    
    expense_report_id = Column(UUID(as_uuid=True), ForeignKey("expense_reports.id"), primary_key=True)
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"), primary_key=True)
    added_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

class PolicyViolation(Base):
    """Policy violation model"""
    __tablename__ = "policy_violations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("expense_policies.id"), nullable=False)
    violation_type = Column(String(50), nullable=False)
    violation_severity = Column(String(20), nullable=False, default="warning")
    violation_message = Column(Text, nullable=False)
    policy_rule = Column(JSONB, default={})
    requires_comment = Column(Boolean, nullable=False, default=False)
    comment_provided = Column(Text)
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class ApprovalWorkflow(Base):
    """Approval workflow model"""
    __tablename__ = "approval_workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    workflow_type = Column(String(50), nullable=False, default="single_step")
    current_step = Column(Integer, nullable=False, default=1)
    total_steps = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="pending")
    initiated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    initiated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    meta_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")

class ApprovalStep(Base):
    """Approval step model"""
    __tablename__ = "approval_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("approval_workflows.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    approved_at = Column(DateTime(timezone=True))
    rejected_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    rejection_reason = Column(Text)
    notified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    workflow = relationship("ApprovalWorkflow", back_populates="steps")

class EmailNotification(Base):
    """Email notification model"""
    __tablename__ = "email_notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    status = Column(String(50), nullable=False, default="pending")
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    retry_count = Column(Integer, nullable=False, default=0)
    meta_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class RiskScore(Base):
    """Risk score per entity (employee, merchant, expense_line) - 5.2.1 / 5.2.2"""
    __tablename__ = "risk_scores"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=False)
    risk_score = Column(DECIMAL(5, 4), nullable=False)
    meta_data = Column("metadata", JSONB, default=dict)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeDocument(Base):
    """Raw ingested content for RAG (URSSAF, VAT, GDPR, etc.) - 5.2.5"""
    __tablename__ = "knowledge_documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    title = Column(String(500), nullable=False)
    source_url = Column(String(1000))
    type = Column(String(50), nullable=False)
    language = Column(String(10), default="fr")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))