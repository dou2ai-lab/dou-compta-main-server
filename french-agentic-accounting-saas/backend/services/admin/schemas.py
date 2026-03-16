# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: Pydantic schemas for admin module request/response validation
# -----------------------------------------------------------------------------

"""
Pydantic schemas for Admin Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID

class CategoryCreate(BaseModel):
    """Create category request"""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None

class CategoryUpdate(BaseModel):
    """Update category request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    gl_account_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class CategoryResponse(BaseModel):
    """Category response"""
    id: UUID
    tenant_id: UUID
    name: str
    code: str
    description: Optional[str]
    gl_account_id: Optional[UUID]
    is_active: bool
    parent_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GLAccountCreate(BaseModel):
    """Create GL account request"""
    account_code: str = Field(..., min_length=1, max_length=50)
    account_name: str = Field(..., min_length=1, max_length=255)
    account_type: str = Field(..., description="expense, asset, liability, etc.")
    description: Optional[str] = None
    parent_account_id: Optional[UUID] = None

class GLAccountUpdate(BaseModel):
    """Update GL account request"""
    account_code: Optional[str] = Field(None, min_length=1, max_length=50)
    account_name: Optional[str] = Field(None, min_length=1, max_length=255)
    account_type: Optional[str] = None
    description: Optional[str] = None
    parent_account_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class GLAccountResponse(BaseModel):
    """GL account response"""
    id: UUID
    tenant_id: UUID
    account_code: str
    account_name: str
    account_type: str
    description: Optional[str]
    is_active: bool
    parent_account_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PolicyCreate(BaseModel):
    """Create policy request"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    policy_type: str = Field(..., description="amount_limit, category_restriction, approval_required, etc.")
    policy_rules: Dict = Field(default_factory=dict)
    applies_to_roles: List[UUID] = Field(default_factory=list)
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None

class PolicyUpdate(BaseModel):
    """Update policy request"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    policy_type: Optional[str] = None
    policy_rules: Optional[Dict] = None
    applies_to_roles: Optional[List[UUID]] = None
    is_active: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None

class PolicyResponse(BaseModel):
    """Policy response"""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    policy_type: str
    policy_rules: Dict
    applies_to_roles: List[UUID]
    is_active: bool
    effective_from: Optional[datetime]
    effective_until: Optional[datetime]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CategorySuggestionRequest(BaseModel):
    """Request for category suggestion"""
    merchant_name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None

class CategorySuggestionResponse(BaseModel):
    """Category suggestion response"""
    suggested_category: Optional[CategoryResponse] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    alternatives: List[CategoryResponse] = Field(default_factory=list)

class VatRuleCreate(BaseModel):
    """Create VAT rule request"""
    category: Optional[str] = None
    merchant_pattern: Optional[str] = None
    vat_rate: float = Field(..., ge=0.0, le=100.0)
    vat_code: Optional[str] = None
    is_default: bool = False
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

class VatRuleUpdate(BaseModel):
    """Update VAT rule request"""
    category: Optional[str] = None
    merchant_pattern: Optional[str] = None
    vat_rate: Optional[float] = Field(None, ge=0.0, le=100.0)
    vat_code: Optional[str] = None
    is_default: Optional[bool] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None

class VatRuleResponse(BaseModel):
    """VAT rule response"""
    id: UUID
    tenant_id: UUID
    category: Optional[str]
    merchant_pattern: Optional[str]
    vat_rate: float
    vat_code: Optional[str]
    is_default: bool
    effective_from: Optional[datetime]
    effective_to: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# -----------------------------------------------------------------------------
# Tenant Settings (Company Settings page)
# -----------------------------------------------------------------------------

class SettingsUpdate(BaseModel):
    """Update company settings - sections as JSONB dicts"""
    general: Optional[Dict] = None
    users: Optional[Dict] = None
    security: Optional[Dict] = None
    notifications: Optional[Dict] = None
    billing: Optional[Dict] = None


class SettingsResponse(BaseModel):
    """Company settings response"""
    settings: Dict = Field(default_factory=dict)
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangelogEntryResponse(BaseModel):
    """Single changelog entry"""
    id: UUID
    changed_at: datetime
    section: str
    action: str
    changed_by_email: Optional[str] = None
    old_value: Optional[Dict] = None
    new_value: Optional[Dict] = None

    class Config:
        from_attributes = True




























