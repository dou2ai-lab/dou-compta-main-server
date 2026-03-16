# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Policy service models and schemas
# -----------------------------------------------------------------------------

"""
Policy service models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

class ViolationSeverity(str, Enum):
    """Policy violation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class ViolationType(str, Enum):
    """Policy violation types"""
    AMOUNT_EXCEEDED = "amount_exceeded"
    CATEGORY_RESTRICTED = "category_restricted"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    MEAL_CAP_EXCEEDED = "meal_cap_exceeded"
    HOTEL_CAP_EXCEEDED = "hotel_cap_exceeded"
    MILEAGE_INVALID = "mileage_invalid"
    DATE_RESTRICTION = "date_restriction"
    MERCHANT_BLACKLISTED = "merchant_blacklisted"

class PolicyEvaluationRequest(BaseModel):
    """Request for policy evaluation"""
    expense_id: UUID
    amount: Decimal
    currency: str
    expense_date: date
    category: Optional[str] = None
    merchant_name: Optional[str] = None
    description: Optional[str] = None
    user_id: UUID
    tenant_id: UUID
    user_roles: List[str] = []

class PolicyViolationResponse(BaseModel):
    """Policy violation response"""
    id: Optional[UUID] = None
    policy_id: UUID
    violation_type: ViolationType
    violation_severity: ViolationSeverity
    violation_message: str
    policy_rule: Dict[str, Any] = {}
    requires_comment: bool = False
    comment_provided: Optional[str] = None
    is_resolved: bool = False

class PolicyEvaluationResponse(BaseModel):
    """Policy evaluation response"""
    has_violations: bool
    violations: List[PolicyViolationResponse] = []
    can_submit: bool = True
    requires_comment: bool = False
    total_violations: int = 0
    warning_count: int = 0
    error_count: int = 0



























