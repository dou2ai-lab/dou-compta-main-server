# -----------------------------------------------------------------------------
# File: engine.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: VAT rules engine for automatic VAT rate determination
# -----------------------------------------------------------------------------

"""
VAT Rules Engine
Deterministic engine for automatic VAT rate determination based on rules
NO LLMs - all logic is rule-based for compliance accuracy
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, date
import re
import structlog

from services.admin.models import VatRule
from common.models import Expense

logger = structlog.get_logger()


class VATRulesEngine:
    """VAT rules engine for automatic rate determination"""
    
    # Standard French VAT rates
    STANDARD_VAT_RATES = {
        "standard": Decimal("20.0"),
        "intermediate": Decimal("10.0"),
        "reduced": Decimal("5.5"),
        "super_reduced": Decimal("2.1"),
        "zero": Decimal("0.0")
    }
    
    # Category-based VAT rate mapping (default rules)
    CATEGORY_VAT_MAPPING = {
        "restaurant": Decimal("10.0"),  # Restaurants: 10%
        "hotel": Decimal("10.0"),  # Hotels: 10%
        "food": Decimal("5.5"),  # Food: 5.5%
        "book": Decimal("5.5"),  # Books: 5.5%
        "transport": Decimal("5.5"),  # Public transport: 5.5%
        "medicine": Decimal("2.1"),  # Medicines: 2.1%
        "newspaper": Decimal("2.1"),  # Newspapers: 2.1%
        "default": Decimal("20.0")  # Default: 20%
    }
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._rules_cache = None
    
    async def determine_vat_rate(
        self,
        category: Optional[str] = None,
        merchant_name: Optional[str] = None,
        expense_date: Optional[date] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determine VAT rate based on rules
        
        Args:
            category: Expense category
            merchant_name: Merchant name
            expense_date: Expense date (for effective date checks)
            description: Expense description
        
        Returns:
            {
                "vat_rate": Decimal,
                "vat_code": str,
                "rule_applied": str,
                "confidence": str,  # high, medium, low
                "explanation": str,
                "is_recoverable": bool
            }
        """
        try:
            # Load rules if not cached
            if self._rules_cache is None:
                await self._load_rules()
            
            expense_date = expense_date or date.today()
            
            # Step 1: Try merchant pattern matching (highest priority)
            if merchant_name:
                merchant_match = await self._match_merchant_pattern(merchant_name, expense_date)
                if merchant_match:
                    return merchant_match
            
            # Step 2: Try category-based rules
            if category:
                category_match = await self._match_category_rule(category, expense_date)
                if category_match:
                    return category_match
            
            # Step 3: Try default rule
            default_match = await self._get_default_rule(expense_date)
            if default_match:
                return default_match
            
            # Step 4: Fallback to category mapping
            fallback_rate = self._get_category_fallback(category)
            
            return {
                "vat_rate": fallback_rate,
                "vat_code": self._get_vat_code(fallback_rate),
                "rule_applied": "category_fallback",
                "confidence": "medium",
                "explanation": f"Using category-based fallback rate: {fallback_rate}%",
                "is_recoverable": self._is_recoverable(fallback_rate, category)
            }
            
        except Exception as e:
            logger.error("vat_rate_determination_error", error=str(e), category=category, merchant=merchant_name)
            # Return safe default
            return {
                "vat_rate": Decimal("20.0"),
                "vat_code": "FR_STD",
                "rule_applied": "error_fallback",
                "confidence": "low",
                "explanation": f"Error determining VAT rate, using default 20%: {str(e)}",
                "is_recoverable": True
            }
    
    async def _load_rules(self):
        """Load VAT rules from database"""
        try:
            result = await self.db.execute(
                select(VatRule).where(
                    and_(
                        VatRule.tenant_id == self.tenant_id,
                        VatRule.deleted_at.is_(None)
                    )
                )
            )
            self._rules_cache = result.scalars().all()
            logger.info("vat_rules_loaded", count=len(self._rules_cache))
        except Exception as e:
            logger.error("vat_rules_load_error", error=str(e))
            self._rules_cache = []
    
    async def _match_merchant_pattern(
        self,
        merchant_name: str,
        expense_date: date
    ) -> Optional[Dict[str, Any]]:
        """Match merchant name against merchant patterns"""
        if not self._rules_cache:
            return None
        
        merchant_lower = merchant_name.lower()
        
        # Sort rules by specificity (more specific patterns first)
        merchant_rules = [
            rule for rule in self._rules_cache
            if rule.merchant_pattern and self._is_rule_effective(rule, expense_date)
        ]
        
        # Try exact match first, then pattern match
        for rule in merchant_rules:
            pattern = rule.merchant_pattern.lower()
            
            # Exact match
            if pattern == merchant_lower:
                return {
                    "vat_rate": rule.vat_rate,
                    "vat_code": rule.vat_code or self._get_vat_code(rule.vat_rate),
                    "rule_applied": rule.rule_name if hasattr(rule, 'rule_name') else f"merchant_pattern_{rule.id}",
                    "confidence": "high",
                    "explanation": f"Matched merchant pattern: {rule.merchant_pattern}",
                    "is_recoverable": self._is_recoverable(rule.vat_rate, rule.category)
                }
            
            # Pattern match (simple substring for now, can be enhanced with regex)
            if pattern in merchant_lower or merchant_lower in pattern:
                return {
                    "vat_rate": rule.vat_rate,
                    "vat_code": rule.vat_code or self._get_vat_code(rule.vat_rate),
                    "rule_applied": f"merchant_pattern_{rule.id}",
                    "confidence": "high",
                    "explanation": f"Matched merchant pattern: {rule.merchant_pattern}",
                    "is_recoverable": self._is_recoverable(rule.vat_rate, rule.category)
                }
        
        return None
    
    async def _match_category_rule(
        self,
        category: str,
        expense_date: date
    ) -> Optional[Dict[str, Any]]:
        """Match category against category rules"""
        if not self._rules_cache:
            return None
        
        category_lower = category.lower()
        
        # Find matching category rules
        category_rules = [
            rule for rule in self._rules_cache
            if rule.category and rule.category.lower() == category_lower
            and self._is_rule_effective(rule, expense_date)
        ]
        
        if category_rules:
            # Use first matching rule (can be enhanced with priority)
            rule = category_rules[0]
            return {
                "vat_rate": rule.vat_rate,
                "vat_code": rule.vat_code or self._get_vat_code(rule.vat_rate),
                "rule_applied": f"category_rule_{rule.id}",
                "confidence": "high",
                "explanation": f"Matched category rule: {rule.category}",
                "is_recoverable": self._is_recoverable(rule.vat_rate, rule.category)
            }
        
        return None
    
    async def _get_default_rule(
        self,
        expense_date: date
    ) -> Optional[Dict[str, Any]]:
        """Get default VAT rule"""
        if not self._rules_cache:
            return None
        
        # Find default rule
        default_rules = [
            rule for rule in self._rules_cache
            if rule.is_default and self._is_rule_effective(rule, expense_date)
        ]
        
        if default_rules:
            rule = default_rules[0]
            return {
                "vat_rate": rule.vat_rate,
                "vat_code": rule.vat_code or self._get_vat_code(rule.vat_rate),
                "rule_applied": "default_rule",
                "confidence": "medium",
                "explanation": "Using default VAT rule",
                "is_recoverable": self._is_recoverable(rule.vat_rate, rule.category)
            }
        
        return None
    
    def _get_category_fallback(self, category: Optional[str]) -> Decimal:
        """Get VAT rate from category mapping fallback"""
        if not category:
            return self.CATEGORY_VAT_MAPPING["default"]
        
        category_lower = category.lower()
        
        # Check category mapping
        for cat_key, rate in self.CATEGORY_VAT_MAPPING.items():
            if cat_key in category_lower:
                return rate
        
        return self.CATEGORY_VAT_MAPPING["default"]
    
    def _is_rule_effective(self, rule: VatRule, expense_date: date) -> bool:
        """Check if rule is effective for given date"""
        if rule.effective_from and expense_date < rule.effective_from.date():
            return False
        if rule.effective_to and expense_date > rule.effective_to.date():
            return False
        return True
    
    def _get_vat_code(self, vat_rate: Decimal) -> str:
        """Get French VAT code for rate"""
        rate_float = float(vat_rate)
        
        if rate_float == 20.0:
            return "FR_STD"  # Standard rate
        elif rate_float == 10.0:
            return "FR_INT"  # Intermediate rate
        elif rate_float == 5.5:
            return "FR_RED"  # Reduced rate
        elif rate_float == 2.1:
            return "FR_SUP"  # Super-reduced rate
        elif rate_float == 0.0:
            return "FR_ZERO"  # Zero rate
        else:
            return "FR_OTHER"
    
    def _is_recoverable(
        self,
        vat_rate: Decimal,
        category: Optional[str] = None
    ) -> bool:
        """
        Determine if VAT is recoverable
        Most business expenses have recoverable VAT, except:
        - Entertainment expenses (restaurants, hotels for non-business)
        - Personal expenses
        """
        if vat_rate == 0:
            return False
        
        if category:
            category_lower = category.lower()
            # Entertainment expenses may have restrictions
            if "entertainment" in category_lower and "business" not in category_lower:
                return False
        
        # Default: recoverable
        return True
    
    async def validate_vat_calculation(
        self,
        total_amount: Decimal,
        vat_rate: Decimal,
        vat_amount: Decimal,
        tolerance: Decimal = Decimal("0.01")
    ) -> Dict[str, Any]:
        """
        Validate VAT calculation
        
        Args:
            total_amount: Total amount including VAT
            vat_rate: VAT rate percentage
            vat_amount: VAT amount
        
        Returns:
            {
                "is_valid": bool,
                "expected_vat": Decimal,
                "difference": Decimal,
                "explanation": str
            }
        """
        try:
            # Calculate expected VAT: total_amount * vat_rate / (100 + vat_rate)
            expected_vat = (total_amount * vat_rate) / (Decimal("100") + vat_rate)
            
            difference = abs(vat_amount - expected_vat)
            is_valid = difference <= tolerance
            
            return {
                "is_valid": is_valid,
                "expected_vat": expected_vat,
                "actual_vat": vat_amount,
                "difference": difference,
                "tolerance": tolerance,
                "explanation": f"Expected VAT: €{expected_vat:.2f}, Actual: €{vat_amount:.2f}, Difference: €{difference:.2f}"
            }
            
        except Exception as e:
            logger.error("vat_validation_error", error=str(e))
            return {
                "is_valid": False,
                "expected_vat": Decimal("0.0"),
                "actual_vat": vat_amount,
                "difference": Decimal("0.0"),
                "tolerance": tolerance,
                "explanation": f"Validation error: {str(e)}"
            }
    
    async def handle_mixed_vat_receipt(
        self,
        line_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle receipt with multiple VAT rates
        
        Args:
            line_items: List of line items with amounts and VAT rates
        
        Returns:
            {
                "total_amount": Decimal,
                "total_vat": Decimal,
                "by_rate": Dict[str, Dict],
                "is_valid": bool,
                "explanation": str
            }
        """
        try:
            total_amount = Decimal("0.0")
            total_vat = Decimal("0.0")
            by_rate = {}
            
            for item in line_items:
                item_amount = Decimal(str(item.get("amount", 0)))
                item_vat_rate = Decimal(str(item.get("vat_rate", 0)))
                item_vat_amount = Decimal(str(item.get("vat_amount", 0)))
                
                total_amount += item_amount
                total_vat += item_vat_amount
                
                rate_key = f"{item_vat_rate}%"
                if rate_key not in by_rate:
                    by_rate[rate_key] = {
                        "count": 0,
                        "total_amount": Decimal("0.0"),
                        "total_vat": Decimal("0.0")
                    }
                
                by_rate[rate_key]["count"] += 1
                by_rate[rate_key]["total_amount"] += item_amount
                by_rate[rate_key]["total_vat"] += item_vat_amount
            
            # Validate: sum of line item amounts should equal total
            line_total = sum(Decimal(str(item.get("amount", 0))) for item in line_items)
            is_valid = abs(total_amount - line_total) < Decimal("0.01")
            
            return {
                "total_amount": total_amount,
                "total_vat": total_vat,
                "by_rate": {k: {
                    "count": v["count"],
                    "total_amount": float(v["total_amount"]),
                    "total_vat": float(v["total_vat"])
                } for k, v in by_rate.items()},
                "is_valid": is_valid,
                "explanation": f"Mixed VAT receipt: {len(by_rate)} different rates, Total: €{total_amount:.2f}, VAT: €{total_vat:.2f}"
            }
            
        except Exception as e:
            logger.error("mixed_vat_receipt_error", error=str(e))
            return {
                "total_amount": Decimal("0.0"),
                "total_vat": Decimal("0.0"),
                "by_rate": {},
                "is_valid": False,
                "explanation": f"Error processing mixed VAT receipt: {str(e)}"
            }

