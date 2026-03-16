# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Expense report service business logic
# -----------------------------------------------------------------------------

"""
Expense report service business logic
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
import structlog

from common.models import ExpenseReport, Expense, ExpenseReportItem, User
from .models import ExpenseReportCreate, ExpenseReportUpdate

logger = structlog.get_logger()

class ExpenseReportService:
    """Service for managing expense reports"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_report_number(self, tenant_id: UUID) -> str:
        """Generate unique report number"""
        # Format: REP-YYYYMMDD-XXXX
        today = datetime.utcnow().date()
        date_str = today.strftime("%Y%m%d")
        
        # Get count of reports for today
        result = await self.db.execute(
            select(func.count(ExpenseReport.id)).where(
                ExpenseReport.tenant_id == tenant_id,
                ExpenseReport.report_number.like(f"REP-{date_str}-%")
            )
        )
        count = result.scalar() or 0
        
        report_number = f"REP-{date_str}-{count + 1:04d}"
        return report_number
    
    async def create_report(
        self,
        report_data: ExpenseReportCreate,
        user: User
    ) -> ExpenseReport:
        """Create a new expense report"""
        try:
            # Generate report number
            report_number = await self.generate_report_number(user.tenant_id)
            
            # Calculate totals from expenses
            total_amount = Decimal("0.00")
            currency = "EUR"
            expense_count = 0
            
            if report_data.expense_ids:
                result = await self.db.execute(
                    select(Expense).where(
                        Expense.id.in_(report_data.expense_ids),
                        Expense.tenant_id == user.tenant_id,
                        Expense.submitted_by == user.id,
                        Expense.deleted_at.is_(None)
                    )
                )
                expenses = result.scalars().all()
                expense_count = len(expenses)
                
                if expenses:
                    currency = expenses[0].currency
                    total_amount = sum(exp.amount for exp in expenses)
            
            # Create report
            report = ExpenseReport(
                tenant_id=user.tenant_id,
                submitted_by=user.id,
                report_number=report_number,
                report_type=report_data.report_type,
                title=report_data.title,
                description=report_data.description,
                period_start_date=report_data.period_start_date,
                period_end_date=report_data.period_end_date,
                period_type=report_data.period_type,
                trip_name=report_data.trip_name,
                trip_start_date=report_data.trip_start_date,
                trip_end_date=report_data.trip_end_date,
                trip_destination=report_data.trip_destination,
                total_amount=total_amount,
                currency=currency,
                expense_count=expense_count,
                status="draft"
            )
            
            self.db.add(report)
            await self.db.flush()
            
            # Link expenses
            if report_data.expense_ids:
                for expense_id in report_data.expense_ids:
                    # Check if expense exists and belongs to user
                    expense_result = await self.db.execute(
                        select(Expense).where(
                            Expense.id == expense_id,
                            Expense.tenant_id == user.tenant_id,
                            Expense.submitted_by == user.id
                        )
                    )
                    expense = expense_result.scalar_one_or_none()
                    
                    if expense:
                        # Create report item
                        report_item = ExpenseReportItem(
                            expense_report_id=report.id,
                            expense_id=expense.id,
                            added_by=user.id
                        )
                        self.db.add(report_item)
                        
                        # Update expense
                        expense.expense_report_id = report.id
            
            await self.db.flush()
            
            logger.info("expense_report_created", report_id=str(report.id), user_id=str(user.id))
            
            return report
            
        except Exception as e:
            logger.error("expense_report_creation_failed", error=str(e), exc_info=True)
            raise
    
    async def update_report(
        self,
        report_id: UUID,
        report_data: ExpenseReportUpdate,
        user: User
    ) -> ExpenseReport:
        """Update an expense report"""
        result = await self.db.execute(
            select(ExpenseReport).where(
                ExpenseReport.id == report_id,
                ExpenseReport.tenant_id == user.tenant_id,
                ExpenseReport.deleted_at.is_(None)
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise ValueError("Report not found")
        
        if report.submitted_by != user.id:
            raise ValueError("Access denied")
        
        if report.status != "draft":
            raise ValueError("Cannot update report in current status")
        
        # Update fields
        if report_data.title is not None:
            report.title = report_data.title
        if report_data.description is not None:
            report.description = report_data.description
        
        # Update expenses if provided
        if report_data.expense_ids is not None:
            # Remove existing items
            existing_items_result = await self.db.execute(
                select(ExpenseReportItem).where(
                    ExpenseReportItem.expense_report_id == report_id
                )
            )
            existing_items = existing_items_result.scalars().all()
            for item in existing_items:
                await self.db.delete(item)
            
            # Add new items
            total_amount = Decimal("0.00")
            currency = "EUR"
            
            for expense_id in report_data.expense_ids:
                expense_result = await self.db.execute(
                    select(Expense).where(
                        Expense.id == expense_id,
                        Expense.tenant_id == user.tenant_id,
                        Expense.submitted_by == user.id
                    )
                )
                expense = expense_result.scalar_one_or_none()
                
                if expense:
                    report_item = ExpenseReportItem(
                        expense_report_id=report.id,
                        expense_id=expense.id,
                        added_by=user.id
                    )
                    self.db.add(report_item)
                    expense.expense_report_id = report.id
                    
                    total_amount += expense.amount
                    currency = expense.currency
            
            report.total_amount = total_amount
            report.currency = currency
            report.expense_count = len(report_data.expense_ids)
        
        await self.db.flush()
        
        logger.info("expense_report_updated", report_id=str(report_id))
        
        return report
    
    async def submit_report(
        self,
        report_id: UUID,
        user: User,
        notes: Optional[str] = None
    ) -> ExpenseReport:
        """Submit expense report for approval"""
        result = await self.db.execute(
            select(ExpenseReport).where(
                ExpenseReport.id == report_id,
                ExpenseReport.tenant_id == user.tenant_id,
                ExpenseReport.deleted_at.is_(None)
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise ValueError("Report not found")
        
        if report.submitted_by != user.id:
            raise ValueError("Access denied")
        
        if report.status != "draft":
            raise ValueError("Report already submitted")
        
        if report.expense_count == 0:
            raise ValueError("Cannot submit report with no expenses")
        
        # Get user's manager for approval
        user_result = await self.db.execute(
            select(User).where(User.id == user.id)
        )
        user_obj = user_result.scalar_one()
        manager_id = user_obj.manager_id if hasattr(user_obj, 'manager_id') else None
        
        if not manager_id:
            # If no manager, auto-approve or set to pending for admin
            logger.warning("no_manager_for_approval", report_id=str(report_id), user_id=str(user.id))
            # For now, set status to submitted and approval_status to pending
            # In production, this would trigger admin approval workflow
        
        report.status = "submitted"
        report.approval_status = "pending"
        report.submitted_at = datetime.utcnow()
        report.approver_id = manager_id
        
        if notes:
            report.approval_notes = notes
        
        await self.db.flush()
        
        logger.info("expense_report_submitted", report_id=str(report_id), approver_id=str(manager_id) if manager_id else None)
        
        return report
    
    async def get_user_reports(
        self,
        user: User,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[ExpenseReport], int]:
        """Get expense reports for user"""
        query = select(ExpenseReport).where(
            ExpenseReport.tenant_id == user.tenant_id,
            ExpenseReport.submitted_by == user.id,
            ExpenseReport.deleted_at.is_(None)
        )
        
        if status_filter:
            query = query.where(ExpenseReport.status == status_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.order_by(ExpenseReport.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        reports = list(result.scalars().all())
        
        return reports, total

