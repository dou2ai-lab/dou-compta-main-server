# -----------------------------------------------------------------------------
# File: merchant_profiler.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Merchant profiling and spend analysis
# -----------------------------------------------------------------------------

"""
Merchant Profiling Service
Analyzes merchant patterns and spending behavior
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct
from common.models import Expense, User
import structlog

logger = structlog.get_logger()

class MerchantProfiler:
    """Profile merchants and analyze spending patterns"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def get_merchant_profile(
        self,
        merchant_name: str,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Get comprehensive profile for a merchant"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get all expenses for this merchant
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.merchant_name == merchant_name,
                        Expense.expense_date >= cutoff_date,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expenses = result.scalars().all()
            
            if not expenses:
                return {
                    "merchant_name": merchant_name,
                    "exists": False,
                    "message": "No expenses found for this merchant"
                }
            
            # Calculate statistics
            amounts = [float(exp.amount) for exp in expenses]
            categories = [exp.category for exp in expenses if exp.category]
            employees = set(str(exp.submitted_by) for exp in expenses)
            
            # Get employee details
            employee_details = []
            for emp_id in list(employees)[:10]:  # Limit to 10 employees
                user_result = await self.db.execute(
                    select(User).where(User.id == emp_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    employee_details.append({
                        "id": str(emp_id),
                        "email": user.email,
                        "name": f"{user.first_name} {user.last_name}"
                    })
            
            # Calculate time patterns
            expense_dates = [exp.expense_date for exp in expenses]
            weekday_counts = {}
            month_counts = {}
            for date in expense_dates:
                weekday = date.weekday()
                weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
                month = date.month
                month_counts[month] = month_counts.get(month, 0) + 1
            
            # Calculate category distribution
            category_counts = {}
            for cat in categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            # Calculate approval rates
            approved = sum(1 for exp in expenses if exp.approval_status == "approved")
            rejected = sum(1 for exp in expenses if exp.approval_status == "rejected")
            pending = sum(1 for exp in expenses if exp.approval_status == "pending")
            total = len(expenses)
            
            return {
                "merchant_name": merchant_name,
                "exists": True,
                "statistics": {
                    "total_expenses": total,
                    "total_amount": sum(amounts),
                    "average_amount": sum(amounts) / len(amounts) if amounts else 0,
                    "min_amount": min(amounts) if amounts else 0,
                    "max_amount": max(amounts) if amounts else 0,
                    "median_amount": sorted(amounts)[len(amounts) // 2] if amounts else 0,
                    "unique_employees": len(employees),
                    "unique_categories": len(set(categories)),
                    "date_range": {
                        "first_expense": min(expense_dates).isoformat() if expense_dates else None,
                        "last_expense": max(expense_dates).isoformat() if expense_dates else None
                    }
                },
                "patterns": {
                    "weekday_distribution": weekday_counts,
                    "month_distribution": month_counts,
                    "category_distribution": category_counts,
                    "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
                },
                "approval_metrics": {
                    "approved": approved,
                    "rejected": rejected,
                    "pending": pending,
                    "approval_rate": (approved / total * 100) if total > 0 else 0,
                    "rejection_rate": (rejected / total * 100) if total > 0 else 0
                },
                "employees": employee_details,
                "risk_indicators": {
                    "high_amount_variance": self._calculate_variance(amounts) > 0.5,
                    "single_employee_usage": len(employees) == 1,
                    "high_rejection_rate": (rejected / total) > 0.2 if total > 0 else False
                }
            }
            
        except Exception as e:
            logger.error("merchant_profile_error", merchant_name=merchant_name, error=str(e))
            return {
                "merchant_name": merchant_name,
                "exists": False,
                "error": str(e)
            }
    
    async def get_top_merchants(
        self,
        limit: int = 20,
        days_back: int = 90,
        sort_by: str = "total_amount"  # total_amount, count, avg_amount
    ) -> List[Dict[str, Any]]:
        """Get top merchants by various metrics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get merchant statistics
            result = await self.db.execute(
                select(
                    Expense.merchant_name,
                    func.count(Expense.id).label('count'),
                    func.sum(Expense.amount).label('total_amount'),
                    func.avg(Expense.amount).label('avg_amount'),
                    func.count(distinct(Expense.submitted_by)).label('unique_employees')
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.merchant_name.isnot(None),
                        Expense.expense_date >= cutoff_date,
                        Expense.deleted_at.is_(None)
                    )
                ).group_by(Expense.merchant_name)
            )
            merchants = result.all()
            
            # Convert to list of dicts
            merchant_list = []
            for merch in merchants:
                merchant_list.append({
                    "merchant_name": merch.merchant_name,
                    "expense_count": merch.count,
                    "total_amount": float(merch.total_amount or 0),
                    "average_amount": float(merch.avg_amount or 0),
                    "unique_employees": merch.unique_employees
                })
            
            # Sort
            if sort_by == "total_amount":
                merchant_list.sort(key=lambda x: x["total_amount"], reverse=True)
            elif sort_by == "count":
                merchant_list.sort(key=lambda x: x["expense_count"], reverse=True)
            elif sort_by == "avg_amount":
                merchant_list.sort(key=lambda x: x["average_amount"], reverse=True)
            
            return merchant_list[:limit]
            
        except Exception as e:
            logger.error("top_merchants_error", error=str(e))
            return []
    
    async def get_merchant_spend_analysis(
        self,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """Get overall merchant spend analysis"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get overall statistics
            result = await self.db.execute(
                select(
                    func.count(Expense.id).label('total_expenses'),
                    func.sum(Expense.amount).label('total_amount'),
                    func.count(distinct(Expense.merchant_name)).label('unique_merchants'),
                    func.count(distinct(Expense.submitted_by)).label('unique_employees')
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= cutoff_date,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            stats = result.one()
            
            # Get top merchants
            top_merchants = await self.get_top_merchants(limit=10, days_back=days_back)
            
            # Calculate concentration metrics
            total_amount = float(stats.total_amount or 0)
            top_10_amount = sum(m["total_amount"] for m in top_merchants[:10])
            concentration_ratio = (top_10_amount / total_amount * 100) if total_amount > 0 else 0
            
            return {
                "period_days": days_back,
                "summary": {
                    "total_expenses": stats.total_expenses,
                    "total_amount": total_amount,
                    "unique_merchants": stats.unique_merchants,
                    "unique_employees": stats.unique_employees,
                    "average_per_merchant": total_amount / stats.unique_merchants if stats.unique_merchants > 0 else 0,
                    "average_per_employee": total_amount / stats.unique_employees if stats.unique_employees > 0 else 0
                },
                "top_merchants": top_merchants,
                "concentration": {
                    "top_10_percentage": concentration_ratio,
                    "is_concentrated": concentration_ratio > 50  # More than 50% from top 10
                }
            }
            
        except Exception as e:
            logger.error("spend_analysis_error", error=str(e))
            return {}
    
    def _calculate_variance(self, amounts: List[float]) -> float:
        """Calculate coefficient of variation"""
        if not amounts or len(amounts) < 2:
            return 0.0
        
        mean = sum(amounts) / len(amounts)
        variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
        std_dev = variance ** 0.5
        
        if mean == 0:
            return 0.0
        
        return std_dev / mean  # Coefficient of variation




