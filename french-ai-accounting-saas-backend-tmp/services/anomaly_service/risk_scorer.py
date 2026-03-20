# -----------------------------------------------------------------------------
# File: risk_scorer.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Risk score calculation for expenses
# -----------------------------------------------------------------------------

"""
Risk Score Calculator
Calculates comprehensive risk scores for expenses based on multiple factors
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from common.models import Expense, PolicyViolation
import structlog

logger = structlog.get_logger()

class RiskScorer:
    """Calculate risk scores for expenses"""
    
    def __init__(
        self,
        db: AsyncSession,
        tenant_id: str,
        high_threshold: float = 0.7,
        medium_threshold: float = 0.4
    ):
        self.db = db
        self.tenant_id = tenant_id
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
    
    async def calculate_risk_score(
        self,
        expense: Expense,
        anomaly_score: float,
        is_anomaly: bool
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for an expense
        Returns risk score (0-1) and risk level (low/medium/high)
        """
        risk_factors = {}
        
        # Anomaly score (0-1, higher = more risky)
        risk_factors['anomaly_risk'] = anomaly_score if is_anomaly else 0.0
        
        # Amount risk (large amounts are riskier)
        amount_risk = await self._calculate_amount_risk(expense)
        risk_factors['amount_risk'] = amount_risk
        
        # Employee risk (employees with history of violations)
        employee_risk = await self._calculate_employee_risk(expense.submitted_by)
        risk_factors['employee_risk'] = employee_risk
        
        # Merchant risk (unusual merchants)
        merchant_risk = await self._calculate_merchant_risk(expense.merchant_name)
        risk_factors['merchant_risk'] = merchant_risk
        
        # Category risk (unusual categories for employee)
        category_risk = await self._calculate_category_risk(
            expense.submitted_by,
            expense.category
        )
        risk_factors['category_risk'] = category_risk
        
        # Policy violation risk
        violation_risk = await self._calculate_violation_risk(expense.id)
        risk_factors['violation_risk'] = violation_risk
        
        # Time-based risk (off-hours, weekends, month-end)
        time_risk = self._calculate_time_risk(expense.expense_date)
        risk_factors['time_risk'] = time_risk
        
        # Frequency risk (too many expenses in short time)
        frequency_risk = await self._calculate_frequency_risk(expense)
        risk_factors['frequency_risk'] = frequency_risk
        
        # Calculate weighted total risk score
        weights = {
            'anomaly_risk': 0.25,
            'amount_risk': 0.15,
            'employee_risk': 0.15,
            'merchant_risk': 0.10,
            'category_risk': 0.10,
            'violation_risk': 0.15,
            'time_risk': 0.05,
            'frequency_risk': 0.05
        }
        
        total_risk = sum(risk_factors[key] * weights[key] for key in weights.keys())
        total_risk = min(1.0, max(0.0, total_risk))  # Clamp to 0-1
        
        # Determine risk level
        if total_risk >= self.high_threshold:
            risk_level = 'high'
        elif total_risk >= self.medium_threshold:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_score': float(total_risk),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'weights': weights
        }
    
    async def _calculate_amount_risk(self, expense: Expense) -> float:
        """Calculate risk based on amount (large amounts = higher risk)"""
        amount = float(expense.amount)
        
        # Get average amount for this employee
        result = await self.db.execute(
            select(func.avg(Expense.amount)).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.submitted_by == expense.submitted_by,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        avg_amount = result.scalar() or 0
        
        if avg_amount == 0:
            # No history, moderate risk for any amount
            return 0.3 if amount > 1000 else 0.1
        
        # Risk increases if amount is significantly above average
        ratio = amount / float(avg_amount)
        if ratio > 3.0:
            return 0.9
        elif ratio > 2.0:
            return 0.6
        elif ratio > 1.5:
            return 0.3
        else:
            return 0.1
    
    async def _calculate_employee_risk(self, user_id: str) -> float:
        """Calculate risk based on employee's violation history"""
        # Count policy violations in last 90 days for this employee's expenses
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        result = await self.db.execute(
            select(func.count(PolicyViolation.id)).join(
                Expense, PolicyViolation.expense_id == Expense.id
            ).where(
                and_(
                    Expense.submitted_by == user_id,
                    Expense.tenant_id == self.tenant_id,
                    PolicyViolation.created_at >= cutoff_date
                )
            )
        )
        violation_count = result.scalar() or 0
        
        if violation_count >= 5:
            return 0.9
        elif violation_count >= 3:
            return 0.6
        elif violation_count >= 1:
            return 0.3
        else:
            return 0.0
    
    async def _calculate_merchant_risk(self, merchant_name: Optional[str]) -> float:
        """Calculate risk based on merchant frequency"""
        if not merchant_name:
            return 0.2  # Missing merchant name is slightly risky
        
        # Count how many employees use this merchant
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        result = await self.db.execute(
            select(func.count(func.distinct(Expense.submitted_by))).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.merchant_name == merchant_name,
                    Expense.expense_date >= cutoff_date,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        employee_count = result.scalar() or 0
        
        # Rare merchants (used by < 2 employees) are riskier
        if employee_count == 0:
            return 0.8
        elif employee_count == 1:
            return 0.5
        else:
            return 0.1
    
    async def _calculate_category_risk(self, user_id: str, category: Optional[str]) -> float:
        """Calculate risk if category is unusual for this employee"""
        if not category:
            return 0.1
        
        # Get employee's most common categories
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        result = await self.db.execute(
            select(Expense.category, func.count(Expense.id).label('count')).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.submitted_by == user_id,
                    Expense.category.isnot(None),
                    Expense.expense_date >= cutoff_date,
                    Expense.deleted_at.is_(None)
                )
            ).group_by(Expense.category).order_by(func.count(Expense.id).desc())
        )
        categories = result.all()
        
        if not categories:
            return 0.2  # No history
        
        # Check if this category is in top 3
        top_categories = [cat[0] for cat in categories[:3]]
        if category in top_categories:
            return 0.0
        else:
            return 0.4  # Unusual category
    
    async def _calculate_violation_risk(self, expense_id: str) -> float:
        """Calculate risk based on policy violations"""
        result = await self.db.execute(
            select(func.count(PolicyViolation.id)).where(
                PolicyViolation.expense_id == expense_id
            )
        )
        violation_count = result.scalar() or 0
        
        if violation_count >= 3:
            return 0.9
        elif violation_count >= 2:
            return 0.6
        elif violation_count >= 1:
            return 0.3
        else:
            return 0.0
    
    def _calculate_time_risk(self, expense_date: datetime) -> float:
        """Calculate risk based on timing patterns"""
        risk = 0.0
        
        # Weekend expenses
        if expense_date.weekday() >= 5:
            risk += 0.2
        
        # Month-end expenses (potential budget padding)
        if expense_date.day >= 25:
            risk += 0.2
        
        # Late night/early morning (if we had time data)
        # For now, just use date-based patterns
        
        return min(1.0, risk)
    
    async def _calculate_frequency_risk(self, expense: Expense) -> float:
        """Calculate risk if too many expenses in short time"""
        # Count expenses in last 7 days
        cutoff_date = expense.expense_date - timedelta(days=7)
        
        result = await self.db.execute(
            select(func.count(Expense.id)).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.submitted_by == expense.submitted_by,
                    Expense.expense_date >= cutoff_date,
                    Expense.expense_date <= expense.expense_date,
                    Expense.id != expense.id,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        recent_count = result.scalar() or 0
        
        if recent_count >= 10:
            return 0.8
        elif recent_count >= 5:
            return 0.4
        else:
            return 0.0

