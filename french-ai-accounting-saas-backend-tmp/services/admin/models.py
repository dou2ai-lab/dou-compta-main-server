# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: SQLAlchemy database models for admin module including categories, GL accounts, and policies
# -----------------------------------------------------------------------------

"""
SQLAlchemy models for Admin Service
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base

class ExpenseCategory(Base):
    """Expense category model"""
    __tablename__ = "expense_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False)  # Category code (e.g., "MEALS", "TRAVEL")
    description = Column(Text)
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("expense_categories.id"), nullable=True)
    meta_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class GLAccount(Base):
    """General Ledger account model"""
    __tablename__ = "gl_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    account_code = Column(String(50), nullable=False)  # GL account code (e.g., "6001", "6002")
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # expense, asset, liability, etc.
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_accounts.id"), nullable=True)
    meta_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class ExpensePolicy(Base):
    """Expense policy model"""
    __tablename__ = "expense_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    policy_type = Column(String(50), nullable=False)  # amount_limit, category_restriction, approval_required, etc.
    policy_rules = Column(JSONB, default={})  # Flexible rules storage
    applies_to_roles = Column(JSONB, default=[])  # List of role IDs this policy applies to
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_until = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Underlying DB column is named "metadata" (without underscore).
    # Map to Python attribute "meta_data" for consistency with other models.
    meta_data = Column("metadata", JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class VatRule(Base):
    """VAT rule model"""
    __tablename__ = "vat_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    category = Column(String(100))
    merchant_pattern = Column(String(255))  # Pattern matching for merchant names
    vat_rate = Column(DECIMAL(5, 2), nullable=False)
    vat_code = Column(String(50))  # French VAT code
    is_default = Column(Boolean, default=False, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class TenantSettings(Base):
    """Tenant/company settings (general, users, security, notifications, billing)"""
    __tablename__ = "tenant_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    settings = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SettingsChangelog(Base):
    """Audit log of settings changes"""
    __tablename__ = "settings_changelog"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    section = Column(String(50), nullable=False)
    action = Column(String(20), nullable=False, default="update")
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)


class UserManagementActivity(Base):
    """Activity log for user and role management (Users & Roles Activity tab)."""
    __tablename__ = "user_management_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    performed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(80), nullable=False)  # user_created, user_updated, user_deleted, user_status_changed, role_permissions_updated
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    target_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    details = Column(JSONB, default=dict)  # e.g. {"email": "...", "role_name": "..."}
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)




























