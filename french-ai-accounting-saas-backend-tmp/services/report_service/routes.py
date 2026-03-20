# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Expense report service API routes
# -----------------------------------------------------------------------------

"""
Expense report service routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import structlog
import csv
import io

from common.database import get_db
from common.models import ExpenseReport, ExpenseReportItem, Expense, User
from services.auth.dependencies import get_current_user
from services.security.rbac import require_approval_access
from services.report_service.service import ExpenseReportService
from services.report_service.models import (
    ExpenseReportCreate, ExpenseReportUpdate, ExpenseReportResponse,
    ExpenseReportListResponse, ExpenseReportDetailResponse,
    ExpenseReportSubmitRequest, ExpenseReportApproveRequest, ExpenseReportRejectRequest,
    ReportExpenseItemResponse, ReportExpensesListResponse
)

logger = structlog.get_logger()
router = APIRouter()

@router.post("", response_model=ExpenseReportDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_expense_report(
    report_data: ExpenseReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new expense report"""
    try:
        service = ExpenseReportService(db)
        report = await service.create_report(report_data, current_user)
        
        await db.commit()
        await db.refresh(report)
        
        # Get expense IDs
        expense_items_result = await db.execute(
            select(ExpenseReportItem.expense_id).where(
                ExpenseReportItem.expense_report_id == report.id
            )
        )
        expense_ids = [row[0] for row in expense_items_result.all()]
        
        logger.info("expense_report_created", report_id=str(report.id), user_id=str(current_user.id))
        
        return ExpenseReportDetailResponse(
            success=True,
            data=ExpenseReportResponse(
                id=report.id,
                tenant_id=report.tenant_id,
                submitted_by=report.submitted_by,
                report_number=report.report_number,
                report_type=report.report_type,
                title=report.title,
                description=report.description,
                period_start_date=report.period_start_date,
                period_end_date=report.period_end_date,
                period_type=report.period_type,
                trip_name=report.trip_name,
                trip_start_date=report.trip_start_date,
                trip_end_date=report.trip_end_date,
                trip_destination=report.trip_destination,
                total_amount=report.total_amount,
                currency=report.currency,
                expense_count=report.expense_count,
                status=report.status,
                approval_status=report.approval_status,
                submitted_at=report.submitted_at,
                approver_id=report.approver_id,
                approved_at=report.approved_at,
                rejected_at=report.rejected_at,
                rejection_reason=report.rejection_reason,
                approval_notes=report.approval_notes,
                created_at=report.created_at,
                updated_at=report.updated_at,
                expense_ids=expense_ids
            )
        )
        
    except Exception as e:
        await db.rollback()
        logger.error("expense_report_creation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create expense report: {str(e)}"
        )

@router.get("", response_model=ExpenseReportListResponse)
async def list_expense_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List expense reports for current user"""
    try:
        service = ExpenseReportService(db)
        reports, total = await service.get_user_reports(
            current_user,
            status_filter=status_filter,
            page=page,
            page_size=page_size
        )
        
        report_responses = []
        for report in reports:
            # Get expense IDs
            expense_items_result = await db.execute(
                select(ExpenseReportItem.expense_id).where(
                    ExpenseReportItem.expense_report_id == report.id
                )
            )
            expense_ids = [row[0] for row in expense_items_result.all()]
            
            report_responses.append(
                ExpenseReportResponse(
                    id=report.id,
                    tenant_id=report.tenant_id,
                    submitted_by=report.submitted_by,
                    report_number=report.report_number,
                    report_type=report.report_type,
                    title=report.title,
                    description=report.description,
                    period_start_date=report.period_start_date,
                    period_end_date=report.period_end_date,
                    period_type=report.period_type,
                    trip_name=report.trip_name,
                    trip_start_date=report.trip_start_date,
                    trip_end_date=report.trip_end_date,
                    trip_destination=report.trip_destination,
                    total_amount=report.total_amount,
                    currency=report.currency,
                    expense_count=report.expense_count,
                    status=report.status,
                    approval_status=report.approval_status,
                    submitted_at=report.submitted_at,
                    approver_id=report.approver_id,
                    approved_at=report.approved_at,
                    rejected_at=report.rejected_at,
                    rejection_reason=report.rejection_reason,
                    approval_notes=report.approval_notes,
                    created_at=report.created_at,
                    updated_at=report.updated_at,
                    expense_ids=expense_ids
                )
            )
        
        return ExpenseReportListResponse(
            success=True,
            data=report_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error("expense_report_list_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list expense reports"
        )


@router.get("/{report_id}/expenses", response_model=ReportExpensesListResponse)
async def get_report_expenses(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of expenses included in a report"""
    result = await db.execute(
        select(ExpenseReport).where(
            ExpenseReport.id == report_id,
            ExpenseReport.tenant_id == current_user.tenant_id,
            ExpenseReport.deleted_at.is_(None)
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense report not found"
        )
    await require_approval_access(
        current_user,
        db,
        report.submitted_by,
        endpoint="get_report_expenses",
        allow_owner=True,
    )
    items_result = await db.execute(
        select(ExpenseReportItem.expense_id).where(
            ExpenseReportItem.expense_report_id == report.id
        )
    )
    expense_ids = [row[0] for row in items_result.all()]
    if not expense_ids:
        return ReportExpensesListResponse(success=True, data=[])
    expenses_result = await db.execute(
        select(Expense).where(
            Expense.id.in_(expense_ids),
            Expense.tenant_id == current_user.tenant_id,
            Expense.deleted_at.is_(None)
        )
    )
    expenses = expenses_result.scalars().all()
    # Preserve order of expense_ids
    by_id = {e.id: e for e in expenses}
    ordered = [by_id[eid] for eid in expense_ids if eid in by_id]
    return ReportExpensesListResponse(
        success=True,
        data=[ReportExpenseItemResponse(
            id=e.id,
            amount=e.amount,
            currency=e.currency or "EUR",
            expense_date=e.expense_date,
            merchant_name=e.merchant_name,
            category=e.category,
            description=e.description,
            vat_amount=e.vat_amount,
            vat_rate=e.vat_rate,
            status=e.status,
            approval_status=e.approval_status,
        ) for e in ordered]
    )


@router.get("/{report_id}", response_model=ExpenseReportDetailResponse)
async def get_expense_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expense report by ID"""
    try:
        result = await db.execute(
            select(ExpenseReport).where(
                ExpenseReport.id == report_id,
                ExpenseReport.tenant_id == current_user.tenant_id,
                ExpenseReport.deleted_at.is_(None)
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense report not found"
            )
        
        await require_approval_access(
            current_user,
            db,
            report.submitted_by,
            endpoint="get_expense_report",
            allow_owner=True,
        )
        
        # Get expense IDs
        expense_items_result = await db.execute(
            select(ExpenseReportItem.expense_id).where(
                ExpenseReportItem.expense_report_id == report.id
            )
        )
        expense_ids = [row[0] for row in expense_items_result.all()]
        
        return ExpenseReportDetailResponse(
            success=True,
            data=ExpenseReportResponse(
                id=report.id,
                tenant_id=report.tenant_id,
                submitted_by=report.submitted_by,
                report_number=report.report_number,
                report_type=report.report_type,
                title=report.title,
                description=report.description,
                period_start_date=report.period_start_date,
                period_end_date=report.period_end_date,
                period_type=report.period_type,
                trip_name=report.trip_name,
                trip_start_date=report.trip_start_date,
                trip_end_date=report.trip_end_date,
                trip_destination=report.trip_destination,
                total_amount=report.total_amount,
                currency=report.currency,
                expense_count=report.expense_count,
                status=report.status,
                approval_status=report.approval_status,
                submitted_at=report.submitted_at,
                approver_id=report.approver_id,
                approved_at=report.approved_at,
                rejected_at=report.rejected_at,
                rejection_reason=report.rejection_reason,
                approval_notes=report.approval_notes,
                created_at=report.created_at,
                updated_at=report.updated_at,
                expense_ids=expense_ids
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("expense_report_get_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get expense report"
        )

@router.put("/{report_id}", response_model=ExpenseReportDetailResponse)
async def update_expense_report(
    report_id: str,
    report_data: ExpenseReportUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update expense report"""
    try:
        service = ExpenseReportService(db)
        report = await service.update_report(report_id, report_data, current_user)
        
        await db.commit()
        await db.refresh(report)
        
        # Get expense IDs
        expense_items_result = await db.execute(
            select(ExpenseReportItem.expense_id).where(
                ExpenseReportItem.expense_report_id == report.id
            )
        )
        expense_ids = [row[0] for row in expense_items_result.all()]
        
        logger.info("expense_report_updated", report_id=str(report_id))
        
        return ExpenseReportDetailResponse(
            success=True,
            data=ExpenseReportResponse(
                id=report.id,
                tenant_id=report.tenant_id,
                submitted_by=report.submitted_by,
                report_number=report.report_number,
                report_type=report.report_type,
                title=report.title,
                description=report.description,
                period_start_date=report.period_start_date,
                period_end_date=report.period_end_date,
                period_type=report.period_type,
                trip_name=report.trip_name,
                trip_start_date=report.trip_start_date,
                trip_end_date=report.trip_end_date,
                trip_destination=report.trip_destination,
                total_amount=report.total_amount,
                currency=report.currency,
                expense_count=report.expense_count,
                status=report.status,
                approval_status=report.approval_status,
                submitted_at=report.submitted_at,
                approver_id=report.approver_id,
                approved_at=report.approved_at,
                rejected_at=report.rejected_at,
                rejection_reason=report.rejection_reason,
                approval_notes=report.approval_notes,
                created_at=report.created_at,
                updated_at=report.updated_at,
                expense_ids=expense_ids
            )
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        logger.error("expense_report_update_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update expense report"
        )

@router.post("/{report_id}/submit", response_model=ExpenseReportDetailResponse)
async def submit_expense_report(
    report_id: str,
    request: ExpenseReportSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit expense report for approval"""
    try:
        service = ExpenseReportService(db)
        report = await service.submit_report(report_id, current_user, request.notes)
        
        await db.commit()
        await db.refresh(report)
        
        # TODO: Send email notification to approver
        
        # Get expense IDs
        expense_items_result = await db.execute(
            select(ExpenseReportItem.expense_id).where(
                ExpenseReportItem.expense_report_id == report.id
            )
        )
        expense_ids = [row[0] for row in expense_items_result.all()]
        
        logger.info("expense_report_submitted", report_id=str(report_id))
        
        return ExpenseReportDetailResponse(
            success=True,
            data=ExpenseReportResponse(
                id=report.id,
                tenant_id=report.tenant_id,
                submitted_by=report.submitted_by,
                report_number=report.report_number,
                report_type=report.report_type,
                title=report.title,
                description=report.description,
                period_start_date=report.period_start_date,
                period_end_date=report.period_end_date,
                period_type=report.period_type,
                trip_name=report.trip_name,
                trip_start_date=report.trip_start_date,
                trip_end_date=report.trip_end_date,
                trip_destination=report.trip_destination,
                total_amount=report.total_amount,
                currency=report.currency,
                expense_count=report.expense_count,
                status=report.status,
                approval_status=report.approval_status,
                submitted_at=report.submitted_at,
                approver_id=report.approver_id,
                approved_at=report.approved_at,
                rejected_at=report.rejected_at,
                rejection_reason=report.rejection_reason,
                approval_notes=report.approval_notes,
                created_at=report.created_at,
                updated_at=report.updated_at,
                expense_ids=expense_ids
            )
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        logger.error("expense_report_submit_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit expense report"
        )

@router.post("/{report_id}/approve", response_model=ExpenseReportDetailResponse)
async def approve_expense_report(
    report_id: str,
    request: ExpenseReportApproveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve expense report"""
    try:
        result = await db.execute(
            select(ExpenseReport).where(
                ExpenseReport.id == report_id,
                ExpenseReport.tenant_id == current_user.tenant_id,
                ExpenseReport.deleted_at.is_(None)
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense report not found"
            )

        await require_approval_access(
            current_user,
            db,
            report.submitted_by,
            endpoint="approve_expense_report",
            allow_owner=False,
        )

        if report.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report is not pending approval"
            )
        
        from datetime import datetime
        report.approval_status = "approved"
        report.status = "approved"
        report.approver_id = current_user.id
        report.approved_at = datetime.utcnow()
        if request.notes:
            report.approval_notes = request.notes
        
        await db.commit()
        await db.refresh(report)
        
        # TODO: Send email notification to submitter
        
        # Get expense IDs
        expense_items_result = await db.execute(
            select(ExpenseReportItem.expense_id).where(
                ExpenseReportItem.expense_report_id == report.id
            )
        )
        expense_ids = [row[0] for row in expense_items_result.all()]
        
        logger.info("expense_report_approved", report_id=str(report_id), approver_id=str(current_user.id))
        
        return ExpenseReportDetailResponse(
            success=True,
            data=ExpenseReportResponse(
                id=report.id,
                tenant_id=report.tenant_id,
                submitted_by=report.submitted_by,
                report_number=report.report_number,
                report_type=report.report_type,
                title=report.title,
                description=report.description,
                period_start_date=report.period_start_date,
                period_end_date=report.period_end_date,
                period_type=report.period_type,
                trip_name=report.trip_name,
                trip_start_date=report.trip_start_date,
                trip_end_date=report.trip_end_date,
                trip_destination=report.trip_destination,
                total_amount=report.total_amount,
                currency=report.currency,
                expense_count=report.expense_count,
                status=report.status,
                approval_status=report.approval_status,
                submitted_at=report.submitted_at,
                approver_id=report.approver_id,
                approved_at=report.approved_at,
                rejected_at=report.rejected_at,
                rejection_reason=report.rejection_reason,
                approval_notes=report.approval_notes,
                created_at=report.created_at,
                updated_at=report.updated_at,
                expense_ids=expense_ids
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("expense_report_approve_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve expense report"
        )

@router.post("/{report_id}/reject", response_model=ExpenseReportDetailResponse)
async def reject_expense_report(
    report_id: str,
    request: ExpenseReportRejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject expense report"""
    try:
        result = await db.execute(
            select(ExpenseReport).where(
                ExpenseReport.id == report_id,
                ExpenseReport.tenant_id == current_user.tenant_id,
                ExpenseReport.deleted_at.is_(None)
            )
        )
        report = result.scalar_one_or_none()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense report not found"
            )

        await require_approval_access(
            current_user,
            db,
            report.submitted_by,
            endpoint="reject_expense_report",
            allow_owner=False,
        )

        if report.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report is not pending approval"
            )
        
        from datetime import datetime
        report.approval_status = "rejected"
        report.status = "rejected"
        report.rejected_at = datetime.utcnow()
        report.rejection_reason = request.reason
        
        await db.commit()
        await db.refresh(report)
        
        # TODO: Send email notification to submitter
        
        # Get expense IDs
        expense_items_result = await db.execute(
            select(ExpenseReportItem.expense_id).where(
                ExpenseReportItem.expense_report_id == report.id
            )
        )
        expense_ids = [row[0] for row in expense_items_result.all()]
        
        logger.info("expense_report_rejected", report_id=str(report_id), rejector_id=str(current_user.id))
        
        return ExpenseReportDetailResponse(
            success=True,
            data=ExpenseReportResponse(
                id=report.id,
                tenant_id=report.tenant_id,
                submitted_by=report.submitted_by,
                report_number=report.report_number,
                report_type=report.report_type,
                title=report.title,
                description=report.description,
                period_start_date=report.period_start_date,
                period_end_date=report.period_end_date,
                period_type=report.period_type,
                trip_name=report.trip_name,
                trip_start_date=report.trip_start_date,
                trip_end_date=report.trip_end_date,
                trip_destination=report.trip_destination,
                total_amount=report.total_amount,
                currency=report.currency,
                expense_count=report.expense_count,
                status=report.status,
                approval_status=report.approval_status,
                submitted_at=report.submitted_at,
                approver_id=report.approver_id,
                approved_at=report.approved_at,
                rejected_at=report.rejected_at,
                rejection_reason=report.rejection_reason,
                approval_notes=report.approval_notes,
                created_at=report.created_at,
                updated_at=report.updated_at,
                expense_ids=expense_ids
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("expense_report_reject_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject expense report"
        )


@router.get("/{report_id}/export")
async def export_expense_report(
    report_id: str,
    format: str = Query("csv", description="Export format: csv or excel"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export expense report as CSV or Excel (French compliance: amounts in EUR, date format)."""
    result = await db.execute(
        select(ExpenseReport).where(
            ExpenseReport.id == report_id,
            ExpenseReport.tenant_id == current_user.tenant_id,
            ExpenseReport.deleted_at.is_(None)
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense report not found")
    await require_approval_access(
        current_user,
        db,
        report.submitted_by,
        endpoint="export_expense_report",
        allow_owner=True,
    )

    items_result = await db.execute(
        select(ExpenseReportItem.expense_id).where(
            ExpenseReportItem.expense_report_id == report.id
        )
    )
    expense_ids = [row[0] for row in items_result.all()]
    if not expense_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report has no expenses")

    expenses_result = await db.execute(
        select(Expense).where(
            Expense.id.in_(expense_ids),
            Expense.tenant_id == current_user.tenant_id,
            Expense.deleted_at.is_(None),
        )
    )
    expenses = expenses_result.scalars().all()

    fmt = (format or "csv").lower()
    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "Date", "Merchant", "Category", "Description", "Amount", "Currency",
            "VAT Amount", "VAT Rate", "Status", "Approval Status"
        ])
        for e in expenses:
            writer.writerow([
                e.expense_date.isoformat() if e.expense_date else "",
                e.merchant_name or "",
                e.category or "",
                e.description or "",
                str(e.amount or ""),
                e.currency or "EUR",
                str(e.vat_amount or ""),
                str(e.vat_rate or ""),
                e.status or "",
                e.approval_status or "",
            ])
        content = buf.getvalue().encode("utf-8-sig")
        return Response(
            content=content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="report_{report.report_number}.csv"'
            },
        )

    if fmt == "excel" or fmt == "xlsx":
        try:
            import openpyxl
        except ImportError:
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([
                "Date", "Merchant", "Category", "Description", "Amount", "Currency",
                "VAT Amount", "VAT Rate", "Status", "Approval Status"
            ])
            for e in expenses:
                writer.writerow([
                    e.expense_date.isoformat() if e.expense_date else "",
                    e.merchant_name or "",
                    e.category or "",
                    e.description or "",
                    str(e.amount or ""),
                    e.currency or "EUR",
                    str(e.vat_amount or ""),
                    str(e.vat_rate or ""),
                    e.status or "",
                    e.approval_status or "",
                ])
            content = buf.getvalue().encode("utf-8-sig")
            return Response(
                content=content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="report_{report.report_number}.csv"'
                },
            )
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Expenses"
        ws.append([
            "Date", "Merchant", "Category", "Description", "Amount", "Currency",
            "VAT Amount", "VAT Rate", "Status", "Approval Status"
        ])
        for e in expenses:
            ws.append([
                e.expense_date.isoformat() if e.expense_date else "",
                e.merchant_name or "",
                e.category or "",
                e.description or "",
                float(e.amount) if e.amount is not None else "",
                e.currency or "EUR",
                float(e.vat_amount) if e.vat_amount is not None else "",
                float(e.vat_rate) if e.vat_rate is not None else "",
                e.status or "",
                e.approval_status or "",
            ])
        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        return Response(
            content=out.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="report_{report.report_number}.xlsx"'
            },
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Format must be csv or excel"
    )
























