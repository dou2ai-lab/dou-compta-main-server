# -----------------------------------------------------------------------------
# File: feature_engineering.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Feature engineering pipeline for expense anomaly detection
# -----------------------------------------------------------------------------

"""
Feature Engineering Pipeline
Extracts features from expenses for anomaly detection
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from common.models import Expense, User
import structlog

logger = structlog.get_logger()

class FeatureEngineeringPipeline:
    """Feature engineering pipeline for expense data"""
    
    def __init__(self, db: AsyncSession, tenant_id: str, lookback_days: int = 90):
        self.db = db
        self.tenant_id = tenant_id
        self.lookback_days = lookback_days
    
    async def extract_expense_features(self, expense: Expense) -> Dict[str, Any]:
        """Extract features from a single expense"""
        features = {}
        
        # Basic amount features
        features['amount'] = float(expense.amount)
        features['amount_log'] = np.log1p(float(expense.amount))
        
        # Time features
        expense_date = expense.expense_date
        features['day_of_week'] = expense_date.weekday()
        features['day_of_month'] = expense_date.day
        features['month'] = expense_date.month
        features['is_weekend'] = 1 if expense_date.weekday() >= 5 else 0
        features['is_month_end'] = 1 if expense_date.day >= 25 else 0
        
        # Employee features
        user_id = str(expense.submitted_by)
        employee_features = await self._get_employee_features(user_id, expense_date)
        features.update(employee_features)
        
        # Merchant features
        if expense.merchant_name:
            merchant_features = await self._get_merchant_features(
                expense.merchant_name, 
                expense_date
            )
            features.update(merchant_features)
        else:
            features['merchant_frequency'] = 0
            features['merchant_avg_amount'] = 0
            features['merchant_std_amount'] = 0
        
        # Category features
        if expense.category:
            category_features = await self._get_category_features(
                expense.category,
                expense_date
            )
            features.update(category_features)
        else:
            features['category_frequency'] = 0
            features['category_avg_amount'] = 0
        
        # VAT features
        features['has_vat'] = 1 if expense.vat_amount and float(expense.vat_amount) > 0 else 0
        features['vat_rate'] = float(expense.vat_rate) if expense.vat_rate else 0
        
        # Status features
        features['is_submitted'] = 1 if expense.status == 'submitted' else 0
        features['is_approved'] = 1 if expense.approval_status == 'approved' else 0
        features['is_rejected'] = 1 if expense.approval_status == 'rejected' else 0
        
        return features
    
    async def _get_employee_features(self, user_id: str, expense_date: datetime) -> Dict[str, Any]:
        """Get employee spending patterns"""
        cutoff_date = expense_date - timedelta(days=self.lookback_days)
        
        # Get employee's historical expenses
        result = await self.db.execute(
            select(Expense).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.submitted_by == user_id,
                    Expense.expense_date >= cutoff_date,
                    Expense.expense_date < expense_date,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        historical_expenses = result.scalars().all()
        
        if not historical_expenses:
            return {
                'employee_expense_count': 0,
                'employee_avg_amount': 0,
                'employee_std_amount': 0,
                'employee_total_amount': 0,
                'employee_avg_daily_spend': 0,
                'employee_unique_merchants': 0,
                'employee_unique_categories': 0
            }
        
        amounts = [float(exp.amount) for exp in historical_expenses]
        merchants = set(exp.merchant_name for exp in historical_expenses if exp.merchant_name)
        categories = set(exp.category for exp in historical_expenses if exp.category)
        
        # Calculate days with expenses
        expense_dates = set(exp.expense_date for exp in historical_expenses)
        days_with_expenses = len(expense_dates)
        
        return {
            'employee_expense_count': len(historical_expenses),
            'employee_avg_amount': np.mean(amounts) if amounts else 0,
            'employee_std_amount': np.std(amounts) if len(amounts) > 1 else 0,
            'employee_total_amount': sum(amounts),
            'employee_avg_daily_spend': sum(amounts) / days_with_expenses if days_with_expenses > 0 else 0,
            'employee_unique_merchants': len(merchants),
            'employee_unique_categories': len(categories)
        }
    
    async def _get_merchant_features(self, merchant_name: str, expense_date: datetime) -> Dict[str, Any]:
        """Get merchant spending patterns"""
        cutoff_date = expense_date - timedelta(days=self.lookback_days)
        
        # Get all expenses for this merchant
        result = await self.db.execute(
            select(Expense).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.merchant_name == merchant_name,
                    Expense.expense_date >= cutoff_date,
                    Expense.expense_date < expense_date,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        merchant_expenses = result.scalars().all()
        
        if not merchant_expenses:
            return {
                'merchant_frequency': 0,
                'merchant_avg_amount': 0,
                'merchant_std_amount': 0,
                'merchant_unique_employees': 0
            }
        
        amounts = [float(exp.amount) for exp in merchant_expenses]
        employees = set(str(exp.submitted_by) for exp in merchant_expenses)
        
        return {
            'merchant_frequency': len(merchant_expenses),
            'merchant_avg_amount': np.mean(amounts) if amounts else 0,
            'merchant_std_amount': np.std(amounts) if len(amounts) > 1 else 0,
            'merchant_unique_employees': len(employees)
        }
    
    async def _get_category_features(self, category: str, expense_date: datetime) -> Dict[str, Any]:
        """Get category spending patterns"""
        cutoff_date = expense_date - timedelta(days=self.lookback_days)
        
        # Get all expenses for this category
        result = await self.db.execute(
            select(Expense).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.category == category,
                    Expense.expense_date >= cutoff_date,
                    Expense.expense_date < expense_date,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        category_expenses = result.scalars().all()
        
        if not category_expenses:
            return {
                'category_frequency': 0,
                'category_avg_amount': 0
            }
        
        amounts = [float(exp.amount) for exp in category_expenses]
        
        return {
            'category_frequency': len(category_expenses),
            'category_avg_amount': np.mean(amounts) if amounts else 0
        }
    
    async def build_training_dataset(self) -> pd.DataFrame:
        """Build training dataset from historical expenses"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)
        
        result = await self.db.execute(
            select(Expense).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.expense_date >= cutoff_date,
                    Expense.deleted_at.is_(None)
                )
            )
        )
        expenses = result.scalars().all()
        
        if not expenses:
            logger.warning("no_expenses_for_training", tenant_id=self.tenant_id)
            return pd.DataFrame()
        
        # Extract features for all expenses
        features_list = []
        for expense in expenses:
            try:
                features = await self.extract_expense_features(expense)
                features['expense_id'] = str(expense.id)
                features_list.append(features)
            except Exception as e:
                logger.error("feature_extraction_error", expense_id=str(expense.id), error=str(e))
                continue
        
        if not features_list:
            return pd.DataFrame()
        
        df = pd.DataFrame(features_list)
        return df




