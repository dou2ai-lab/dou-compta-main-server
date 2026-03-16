# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: VAT service API routes
# -----------------------------------------------------------------------------

"""
VAT Service Routes
API endpoints for VAT rate determination
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .service import VATService
from pydantic import BaseModel, Field

router = APIRouter()
logger = structlog.get_logger()


class VATRateRequest(BaseModel):
    """Request for VAT rate determination"""
    category: Optional[str] = None
    merchant_name: Optional[str] = None
    expense_date: Optional[date] = None
    description: Optional[str] = None


class VATRateResponse(BaseModel):
    """VAT rate determination response"""
    vat_rate: float
    vat_code: str
    rule_applied: str
    confidence: str
    explanation: str
    is_recoverable: bool


class VATValidationRequest(BaseModel):
    """Request for VAT calculation validation"""
    total_amount: Decimal = Field(..., gt=0)
    vat_rate: Decimal = Field(..., ge=0, le=100)
    vat_amount: Decimal = Field(..., ge=0)
    tolerance: Optional[Decimal] = Field(Decimal("0.01"), ge=0)


class VATValidationResponse(BaseModel):
    """VAT validation response"""
    is_valid: bool
    expected_vat: float
    actual_vat: float
    difference: float
    tolerance: float
    explanation: str


class MixedVATRequest(BaseModel):
    """Request for mixed VAT receipt handling"""
    line_items: List[Dict[str, Any]] = Field(..., min_items=1)


class MixedVATResponse(BaseModel):
    """Mixed VAT receipt response"""
    total_amount: float
    total_vat: float
    by_rate: Dict[str, Dict[str, Any]]
    is_valid: bool
    explanation: str


@router.post("/determine-rate", response_model=VATRateResponse)
async def determine_vat_rate(
    request: VATRateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Determine VAT rate based on rules"""
    try:
        service = VATService(db, str(current_user.tenant_id))
        result = await service.determine_vat_rate(
            category=request.category,
            merchant_name=request.merchant_name,
            expense_date=request.expense_date,
            description=request.description
        )
        
        return VATRateResponse(
            vat_rate=float(result["vat_rate"]),
            vat_code=result["vat_code"],
            rule_applied=result["rule_applied"],
            confidence=result["confidence"],
            explanation=result["explanation"],
            is_recoverable=result["is_recoverable"]
        )
        
    except Exception as e:
        logger.error("determine_vat_rate_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to determine VAT rate")


@router.post("/validate", response_model=VATValidationResponse)
async def validate_vat_calculation(
    request: VATValidationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Validate VAT calculation"""
    try:
        service = VATService(db, str(current_user.tenant_id))
        result = await service.validate_vat_calculation(
            total_amount=request.total_amount,
            vat_rate=request.vat_rate,
            vat_amount=request.vat_amount,
            tolerance=request.tolerance
        )
        
        return VATValidationResponse(
            is_valid=result["is_valid"],
            expected_vat=float(result["expected_vat"]),
            actual_vat=float(result["actual_vat"]),
            difference=float(result["difference"]),
            tolerance=float(result["tolerance"]),
            explanation=result["explanation"]
        )
        
    except Exception as e:
        logger.error("validate_vat_calculation_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to validate VAT calculation")


@router.post("/mixed-receipt", response_model=MixedVATResponse)
async def handle_mixed_vat_receipt(
    request: MixedVATRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Handle receipt with multiple VAT rates"""
    try:
        service = VATService(db, str(current_user.tenant_id))
        result = await service.handle_mixed_vat_receipt(request.line_items)
        
        return MixedVATResponse(
            total_amount=float(result["total_amount"]),
            total_vat=float(result["total_vat"]),
            by_rate=result["by_rate"],
            is_valid=result["is_valid"],
            explanation=result["explanation"]
        )
        
    except Exception as e:
        logger.error("handle_mixed_vat_receipt_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to handle mixed VAT receipt")

