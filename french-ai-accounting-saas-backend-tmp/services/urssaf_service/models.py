# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: URSSAF service models
# -----------------------------------------------------------------------------

"""
URSSAF Service Models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, DECIMAL, Integer, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base


class URSSAFRule(Base):
    """URSSAF compliance rule"""
    
    __tablename__ = "urssaf_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Rule definition
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # exemption_threshold, contribution_rate, classification
    description = Column(Text)
    
    # Rule conditions
    expense_category = Column(String(100))
    expense_type = Column(String(100))  # benefit, reimbursement, etc.
    amount_threshold = Column(DECIMAL(12, 2))  # Threshold for exemptions
    employee_type = Column(String(50))  # employee, contractor, intern
    
    # Rule values
    contribution_rate = Column(DECIMAL(5, 2))  # Percentage rate
    exemption_applicable = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=True)
    
    # Effective dates
    effective_from = Column(Date)
    effective_to = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    meta_data = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))


class URSSAFComplianceCheck(Base):
    """URSSAF compliance check result"""
    
    __tablename__ = "urssaf_compliance_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expense_id = Column(UUID(as_uuid=True), ForeignKey("expenses.id"), nullable=False)
    
    # Check result
    is_compliant = Column(Boolean, nullable=False)
    compliance_status = Column(String(50), nullable=False)  # compliant, non_compliant, requires_review
    risk_level = Column(String(20), default="low")  # low, medium, high
    
    # Classification
    expense_classification = Column(String(50))  # benefit, reimbursement, exempt
    employee_classification = Column(String(50))  # employee, contractor, intern
    
    # Contribution calculation
    contribution_applicable = Column(Boolean, default=False)
    contribution_rate = Column(DECIMAL(5, 2))
    contribution_amount = Column(DECIMAL(12, 2))
    
    # Exemption check
    exemption_applicable = Column(Boolean, default=False)
    exemption_reason = Column(Text)
    exemption_threshold_met = Column(Boolean, default=False)
    
    # Rule applied
    rule_id = Column(UUID(as_uuid=True), ForeignKey("urssaf_rules.id"))
    rule_name = Column(String(255))
    
    # Explanation
    explanation = Column(Text)
    recommendations = Column(JSONB, default=[])
    
    # Metadata
    checked_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    checked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    meta_data = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

