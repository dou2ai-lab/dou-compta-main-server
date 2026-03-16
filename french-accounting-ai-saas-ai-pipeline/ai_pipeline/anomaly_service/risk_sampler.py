# -----------------------------------------------------------------------------
# File: risk_sampler.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Risk-based sampling logic for audit module
# -----------------------------------------------------------------------------

"""
Risk-Based Sampling Service
Implements sampling logic for audit based on risk scores
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from common.models import Expense
import random
import structlog

logger = structlog.get_logger()

class RiskBasedSampler:
    """Risk-based sampling for audit selection"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def select_audit_sample(
        self,
        sample_size: int = 50,
        min_risk_score: float = 0.4,
        strategy: str = "risk_weighted"  # risk_weighted, stratified, random
    ) -> Dict[str, Any]:
        """
        Select expenses for audit based on risk scores
        Returns selected expenses with sampling rationale
        """
        try:
            # Get candidate expenses
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= cutoff_date,
                        Expense.deleted_at.is_(None),
                        Expense.approval_status != "rejected"  # Don't sample already rejected
                    )
                )
            )
            all_expenses = result.scalars().all()
            
            if not all_expenses:
                return {
                    "success": False,
                    "message": "No expenses available for sampling",
                    "sample": []
                }
            
            # Calculate risk scores for all expenses (simplified - in production use actual service)
            # For now, we'll use a simplified risk calculation
            expense_risks = []
            for expense in all_expenses:
                risk_score = await self._calculate_simple_risk(expense)
                expense_risks.append({
                    "expense_id": str(expense.id),
                    "expense": expense,
                    "risk_score": risk_score
                })
            
            # Filter by minimum risk
            filtered_risks = [
                er for er in expense_risks
                if er["risk_score"] >= min_risk_score
            ]
            
            # Apply sampling strategy
            if strategy == "risk_weighted":
                selected = self._risk_weighted_sampling(filtered_risks, sample_size)
            elif strategy == "stratified":
                selected = self._stratified_sampling(filtered_risks, sample_size)
            else:  # random
                selected = self._random_sampling(filtered_risks, sample_size)
            
            # Format results
            sample_expenses = []
            for item in selected:
                expense = item["expense"]
                sample_expenses.append({
                    "expense_id": str(expense.id),
                    "amount": float(expense.amount),
                    "currency": expense.currency,
                    "merchant_name": expense.merchant_name,
                    "category": expense.category,
                    "expense_date": expense.expense_date.isoformat(),
                    "submitted_by": str(expense.submitted_by),
                    "risk_score": item["risk_score"],
                    "selection_reason": item.get("reason", "Risk-based selection")
                })
            
            return {
                "success": True,
                "strategy": strategy,
                "sample_size": len(sample_expenses),
                "total_candidates": len(all_expenses),
                "filtered_candidates": len(filtered_risks),
                "min_risk_score": min_risk_score,
                "sample": sample_expenses,
                "statistics": {
                    "avg_risk_score": sum(item["risk_score"] for item in selected) / len(selected) if selected else 0,
                    "high_risk_count": sum(1 for item in selected if item["risk_score"] >= 0.7),
                    "medium_risk_count": sum(1 for item in selected if 0.4 <= item["risk_score"] < 0.7),
                    "low_risk_count": sum(1 for item in selected if item["risk_score"] < 0.4)
                }
            }
            
        except Exception as e:
            logger.error("audit_sampling_error", error=str(e))
            return {
                "success": False,
                "message": f"Error during sampling: {str(e)}",
                "sample": []
            }
    
    def _risk_weighted_sampling(
        self,
        expense_risks: List[Dict[str, Any]],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Weighted random sampling based on risk scores"""
        if len(expense_risks) <= sample_size:
            return expense_risks
        
        # Calculate weights (higher risk = higher weight)
        weights = [er["risk_score"] ** 2 for er in expense_risks]  # Square to emphasize high risk
        total_weight = sum(weights)
        
        # Normalize weights
        normalized_weights = [w / total_weight for w in weights]
        
        # Sample based on weights
        selected_indices = random.choices(
            range(len(expense_risks)),
            weights=normalized_weights,
            k=sample_size
        )
        
        selected = []
        seen_ids = set()
        for idx in selected_indices:
            item = expense_risks[idx]
            if item["expense_id"] not in seen_ids:
                item["reason"] = f"Risk-weighted selection (score: {item['risk_score']:.2f})"
                selected.append(item)
                seen_ids.add(item["expense_id"])
        
        # If we need more, fill with highest risk
        if len(selected) < sample_size:
            remaining = [er for er in expense_risks if er["expense_id"] not in seen_ids]
            remaining.sort(key=lambda x: x["risk_score"], reverse=True)
            for item in remaining[:sample_size - len(selected)]:
                item["reason"] = f"High risk selection (score: {item['risk_score']:.2f})"
                selected.append(item)
        
        return selected[:sample_size]
    
    def _stratified_sampling(
        self,
        expense_risks: List[Dict[str, Any]],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Stratified sampling across risk levels"""
        # Categorize by risk level
        high_risk = [er for er in expense_risks if er["risk_score"] >= 0.7]
        medium_risk = [er for er in expense_risks if 0.4 <= er["risk_score"] < 0.7]
        low_risk = [er for er in expense_risks if er["risk_score"] < 0.4]
        
        # Allocate sample size (50% high, 30% medium, 20% low)
        high_count = int(sample_size * 0.5)
        medium_count = int(sample_size * 0.3)
        low_count = sample_size - high_count - medium_count
        
        selected = []
        
        # Sample from each stratum
        if high_risk:
            sampled_high = random.sample(
                high_risk,
                min(high_count, len(high_risk))
            )
            for item in sampled_high:
                item["reason"] = "High risk stratum"
                selected.append(item)
        
        if medium_risk and len(selected) < sample_size:
            sampled_medium = random.sample(
                medium_risk,
                min(medium_count, len(medium_risk))
            )
            for item in sampled_medium:
                item["reason"] = "Medium risk stratum"
                selected.append(item)
        
        if low_risk and len(selected) < sample_size:
            sampled_low = random.sample(
                low_risk,
                min(low_count, len(low_risk))
            )
            for item in sampled_low:
                item["reason"] = "Low risk stratum"
                selected.append(item)
        
        return selected[:sample_size]
    
    def _random_sampling(
        self,
        expense_risks: List[Dict[str, Any]],
        sample_size: int
    ) -> List[Dict[str, Any]]:
        """Simple random sampling"""
        if len(expense_risks) <= sample_size:
            return expense_risks
        
        selected_items = random.sample(expense_risks, sample_size)
        for item in selected_items:
            item["reason"] = "Random selection"
        
        return selected_items
    
    async def _calculate_simple_risk(self, expense: Expense) -> float:
        """Calculate simplified risk score for sampling"""
        risk = 0.0
        
        # Amount-based risk
        amount = float(expense.amount)
        if amount > 1000:
            risk += 0.3
        elif amount > 500:
            risk += 0.2
        
        # Status-based risk
        if expense.approval_status == "pending":
            risk += 0.2
        elif expense.approval_status == "rejected":
            risk += 0.4
        
        # Missing information risk
        if not expense.merchant_name:
            risk += 0.1
        if not expense.category:
            risk += 0.1
        if not expense.description:
            risk += 0.1
        
        # VAT risk
        if expense.vat_rate and float(expense.vat_rate) not in [20.0, 10.0, 5.5, 2.1]:
            risk += 0.2
        
        return min(1.0, risk)




