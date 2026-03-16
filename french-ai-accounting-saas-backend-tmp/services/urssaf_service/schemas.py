# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: URSSAF service schemas
# -----------------------------------------------------------------------------

"""
URSSAF Service Schemas
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date
from uuid import UUID


class URSSAFComplianceCheckResponse(BaseModel):
    """URSSAF compliance check response"""
    id: str
    expense_id: str
    is_compliant: bool
    compliance_status: str
    risk_level: str
    expense_classification: str
    employee_classification: str
    contribution_applicable: bool
    contribution_rate: Optional[Decimal]
    contribution_amount: Optional[Decimal]
    exemption_applicable: bool
    exemption_reason: Optional[str]
    exemption_threshold_met: bool
    rule_name: Optional[str]
    explanation: str
    recommendations: List[str]
    checked_at: str
    
    class Config:
        from_attributes = True


class URSSAFComplianceSummaryResponse(BaseModel):
    """URSSAF compliance summary response"""
    total_checks: int
    compliant_count: int
    non_compliant_count: int
    compliance_rate: float
    contribution_applicable_count: int
    total_contribution_amount: float


class URSSAFRuleCreate(BaseModel):
    """Create URSSAF rule request"""
    rule_name: str = Field(..., min_length=1, max_length=255)
    rule_type: str = Field(..., pattern="^(exemption|contribution|exemption_threshold|classification)$")
    description: Optional[str] = None
    expense_category: Optional[str] = None
    expense_type: Optional[str] = None
    amount_threshold: Optional[Decimal] = None
    employee_type: Optional[str] = None
    contribution_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    exemption_applicable: bool = False
    is_mandatory: bool = True
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    meta_data: Dict[str, Any] = {}


class URSSAFRuleUpdate(BaseModel):
    """Update URSSAF rule request"""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    contribution_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    exemption_applicable: Optional[bool] = None
    is_active: Optional[bool] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    meta_data: Optional[Dict[str, Any]] = None


class URSSAFRuleResponse(BaseModel):
    """URSSAF rule response"""
    id: str
    tenant_id: str
    rule_name: str
    rule_type: str
    description: Optional[str]
    expense_category: Optional[str]
    expense_type: Optional[str]
    amount_threshold: Optional[Decimal]
    employee_type: Optional[str]
    contribution_rate: Optional[Decimal]
    exemption_applicable: bool
    is_mandatory: bool
    effective_from: Optional[date]
    effective_to: Optional[date]
    is_active: bool
    meta_data: Dict[str, Any]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

