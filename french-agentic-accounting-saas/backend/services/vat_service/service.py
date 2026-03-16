# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: VAT service business logic
# -----------------------------------------------------------------------------

"""
VAT Service
Main service layer for VAT rate determination and validation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import date
import structlog

from .engine import VATRulesEngine

logger = structlog.get_logger()


class VATService:
    """VAT service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.engine = VATRulesEngine(db, tenant_id)
    
    async def determine_vat_rate(
        self,
        category: Optional[str] = None,
        merchant_name: Optional[str] = None,
        expense_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Determine VAT rate using rules engine"""
        return await self.engine.determine_vat_rate(
            category=category,
            merchant_name=merchant_name,
            expense_date=expense_date,
            description=description
        )
    
    async def validate_vat_calculation(
        self,
        total_amount: Decimal,
        vat_rate: Decimal,
        vat_amount: Decimal,
        tolerance: Decimal = Decimal("0.01")
    ) -> Dict[str, Any]:
        """Validate VAT calculation"""
        return await self.engine.validate_vat_calculation(
            total_amount=total_amount,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            tolerance=tolerance
        )
    
    async def handle_mixed_vat_receipt(
        self,
        line_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle receipt with multiple VAT rates"""
        return await self.engine.handle_mixed_vat_receipt(line_items)

