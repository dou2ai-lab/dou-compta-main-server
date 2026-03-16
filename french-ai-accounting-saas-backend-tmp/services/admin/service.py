# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: Business logic for admin module including category suggestion
# -----------------------------------------------------------------------------

"""
Business logic for Admin Service
"""
import structlog
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from .models import ExpenseCategory, GLAccount, ExpensePolicy
from .schemas import CategorySuggestionRequest, CategorySuggestionResponse, CategoryResponse

logger = structlog.get_logger()

class CategorySuggestionService:
    """Category suggestion service using rule-based and semantic matching"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def suggest_category(
        self,
        request: CategorySuggestionRequest,
        tenant_id: str
    ) -> CategorySuggestionResponse:
        """
        Suggest expense category based on merchant name, description, and amount
        
        Uses:
        1. Rule-based matching (merchant name keywords)
        2. Semantic matching (description similarity)
        3. Amount-based rules
        """
        # Get all active categories for tenant
        result = await self.db.execute(
            select(ExpenseCategory).where(
                ExpenseCategory.tenant_id == tenant_id,
                ExpenseCategory.is_active == True,
                ExpenseCategory.deleted_at.is_(None)
            )
        )
        categories = result.scalars().all()
        
        if not categories:
            return CategorySuggestionResponse(
                suggested_category=None,
                confidence=0.0,
                reasoning="No categories available",
                alternatives=[]
            )
        
        best_match = None
        best_score = 0.0
        alternatives = []
        
        merchant_name = (request.merchant_name or "").lower()
        description = (request.description or "").lower()
        
        # Rule-based matching
        for category in categories:
            score = 0.0
            reasons = []
            
            # Match merchant name keywords
            category_name_lower = category.name.lower()
            category_code_lower = category.code.lower()
            
            # Check if merchant name contains category keywords
            if merchant_name:
                if category_name_lower in merchant_name or merchant_name in category_name_lower:
                    score += 0.6
                    reasons.append(f"Merchant name matches category '{category.name}'")
                elif category_code_lower in merchant_name:
                    score += 0.4
                    reasons.append(f"Merchant name matches category code '{category.code}'")
            
            # Check description keywords
            if description:
                # Common keywords mapping
                keyword_map = {
                    "restaurant": ["restaurant", "cafe", "bistro", "food", "meal", "dining"],
                    "travel": ["hotel", "flight", "train", "taxi", "uber", "transport"],
                    "office": ["office", "supplies", "stationery", "equipment"],
                    "fuel": ["fuel", "gas", "petrol", "diesel", "station"],
                    "parking": ["parking", "park", "garage"],
                    "telecom": ["phone", "internet", "telecom", "mobile", "communication"]
                }
                
                for cat_key, keywords in keyword_map.items():
                    if cat_key in category_name_lower or cat_key in category_code_lower:
                        for keyword in keywords:
                            if keyword in description:
                                score += 0.3
                                reasons.append(f"Description contains '{keyword}'")
                                break
            
            # Amount-based rules (if amount is very high, might be travel/equipment)
            if request.amount:
                if request.amount > 1000 and "travel" in category_name_lower:
                    score += 0.2
                    reasons.append("High amount suggests travel expense")
                elif request.amount < 50 and "meal" in category_name_lower:
                    score += 0.1
                    reasons.append("Low amount suggests meal expense")
            
            if score > best_score:
                if best_match:
                    alternatives.append(CategoryResponse.model_validate(best_match))
                best_match = category
                best_score = score
            elif score > 0.3:
                alternatives.append(CategoryResponse.model_validate(category))
        
        # Sort alternatives by score (descending)
        alternatives = sorted(alternatives, key=lambda x: x.name, reverse=True)[:3]
        
        if best_match and best_score > 0.3:
            return CategorySuggestionResponse(
                suggested_category=CategoryResponse.model_validate(best_match),
                confidence=min(best_score, 1.0),
                reasoning=f"Matched based on: {', '.join(reasons) if 'reasons' in locals() else 'rule-based matching'}",
                alternatives=alternatives
            )
        else:
            # Return first category as default if no good match
            default_category = categories[0] if categories else None
            return CategorySuggestionResponse(
                suggested_category=CategoryResponse.model_validate(default_category) if default_category else None,
                confidence=0.2,
                reasoning="No strong match found, using default category",
                alternatives=alternatives
            )




























