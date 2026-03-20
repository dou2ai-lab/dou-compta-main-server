# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Expense service routes
# -----------------------------------------------------------------------------

"""
Expense routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Optional, List, Dict, Any
from datetime import date
from uuid import UUID
import structlog

from common.database import get_db
from common.models import Expense, User, UserRole, Role
from common.roles import has_admin_role, can_approve_expense
from services.auth.dependencies import get_current_user
from services.security.rbac import require_approval_access
from services.policy_service.service import PolicyService
from .models import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    ExpenseListResponse, ExpenseDetailResponse,
    ExpenseApproveRequest, ExpenseRejectRequest
)

logger = structlog.get_logger()
router = APIRouter()

async def get_expense_receipt_ids(db: AsyncSession, expense_id: str, tenant_id: str) -> List[str]:
    """Helper function to get receipt IDs for an expense"""
    from services.file_service.models import ReceiptDocument
    receipt_result = await db.execute(
        select(ReceiptDocument.id).where(
            and_(
                ReceiptDocument.expense_id == expense_id,
                ReceiptDocument.tenant_id == tenant_id,
                ReceiptDocument.deleted_at.is_(None)
            )
        )
    )
    return [str(row[0]) for row in receipt_result.all()]

async def get_expenses_receipt_ids_map(db: AsyncSession, expense_ids: List[str], tenant_id: str) -> Dict[str, List[str]]:
    """Helper function to get receipt IDs for multiple expenses"""
    from services.file_service.models import ReceiptDocument
    receipt_map = {}
    if not expense_ids:
        return receipt_map
    
    receipt_result = await db.execute(
        select(ReceiptDocument.expense_id, ReceiptDocument.id).where(
            and_(
                ReceiptDocument.expense_id.in_(expense_ids),
                ReceiptDocument.tenant_id == tenant_id,
                ReceiptDocument.deleted_at.is_(None)
            )
        )
    )
    for row in receipt_result.all():
        expense_id_str = str(row[0])
        if expense_id_str not in receipt_map:
            receipt_map[expense_id_str] = []
        receipt_map[expense_id_str].append(str(row[1]))
    return receipt_map

@router.post("", response_model=ExpenseDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new expense"""
    try:
        # Create expense
        expense = Expense(
            tenant_id=current_user.tenant_id,
            submitted_by=current_user.id,
            amount=expense_data.amount,
            currency=expense_data.currency,
            expense_date=expense_data.expense_date,
            category=expense_data.category,
            description=expense_data.description,
            merchant_name=expense_data.merchant_name,
            vat_amount=expense_data.vat_amount,
            vat_rate=expense_data.vat_rate,
            status="draft"
        )
        
        db.add(expense)
        await db.flush()
        
        # Link receipts if receipt_ids provided
        receipt_ids_list = []
        if expense_data.receipt_ids:
            from services.file_service.models import ReceiptDocument
            from sqlalchemy import and_
            
            for receipt_id in expense_data.receipt_ids:
                # Verify receipt exists and belongs to tenant
                receipt_result = await db.execute(
                    select(ReceiptDocument).where(
                        and_(
                            ReceiptDocument.id == receipt_id,
                            ReceiptDocument.tenant_id == current_user.tenant_id,
                            ReceiptDocument.deleted_at.is_(None)
                        )
                    )
                )
                receipt = receipt_result.scalar_one_or_none()
                
                if receipt:
                    # Link receipt to expense
                    receipt.expense_id = expense.id
                    receipt_ids_list.append(str(receipt.id))
                    logger.info("receipt_linked_to_expense", receipt_id=str(receipt.id), expense_id=str(expense.id))
                else:
                    logger.warning("receipt_not_found_for_linking", receipt_id=str(receipt_id), expense_id=str(expense.id))
        
        # Set policy violation defaults
        expense.policy_violation_count = 0
        expense.has_policy_violations = False
        
        # Store the expense ID immediately after flush (before any other operations)
        expense_id = expense.id
        
        # Evaluate policies (don't fail expense creation if policy evaluation fails)
        try:
            user_roles_result = await db.execute(
                select(Role.name).select_from(UserRole).join(Role, UserRole.role_id == Role.id).where(
                    UserRole.user_id == current_user.id
                )
            )
            user_roles = [row[0] for row in user_roles_result.all()]
            
            policy_service = PolicyService(db)
            await policy_service.evaluate_and_save_violations(expense, user_roles)
        except Exception as e:
            logger.warning("policy_evaluation_failed_on_create", error=str(e), expense_id=str(expense_id), exc_info=True)
            expense.policy_violation_count = 0
            expense.has_policy_violations = False
        
        # Capture ALL expense data into local variables BEFORE commit/refresh
        # This prevents MissingGreenlet errors from accessing detached objects
        expense_data_dict = {
            'id': expense_id,
            'tenant_id': expense.tenant_id,
            'submitted_by': expense.submitted_by,
            'amount': expense.amount,
            'currency': expense.currency,
            'expense_date': expense.expense_date,
            'category': expense.category,
            'description': expense.description,
            'merchant_name': expense.merchant_name,
            'status': expense.status,
            'approval_status': expense.approval_status,
            'approved_by': expense.approved_by,
            'approved_at': expense.approved_at,
            'rejection_reason': expense.rejection_reason,
            'vat_amount': expense.vat_amount,
            'vat_rate': expense.vat_rate,
            'created_at': expense.created_at,
            'updated_at': expense.updated_at,
        }
        
        # Commit the transaction
        try:
            await db.commit()
        except Exception as commit_error:
            # If commit fails, rollback and re-raise
            await db.rollback()
            logger.error("expense_commit_failed", error=str(commit_error), expense_id=str(expense_id), exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save expense"
            )
        
        # Try to refresh to get database-generated values (like timestamps), but don't fail if it doesn't work
        try:
            await db.refresh(expense)
            # Update captured data with any database-generated values (e.g., created_at, updated_at)
            expense_data_dict['created_at'] = expense.created_at
            expense_data_dict['updated_at'] = expense.updated_at
        except Exception as refresh_error:
            # Log but don't fail - we already have the expense data
            logger.warning("expense_refresh_failed", error=str(refresh_error), expense_id=str(expense_id))
            # The expense object already has all the data we need, so we can continue
        
        logger.info("expense_created", expense_id=str(expense_id), user_id=str(current_user.id))
        
        return ExpenseDetailResponse(
            success=True,
            data=ExpenseResponse(
                id=expense_data_dict['id'],
                tenant_id=expense_data_dict['tenant_id'],
                submitted_by=expense_data_dict['submitted_by'],
                amount=expense_data_dict['amount'],
                currency=expense_data_dict['currency'],
                expense_date=expense_data_dict['expense_date'],
                category=expense_data_dict['category'],
                description=expense_data_dict['description'],
                merchant_name=expense_data_dict['merchant_name'],
                status=expense_data_dict['status'],
                approval_status=expense_data_dict['approval_status'],
                approved_by=expense_data_dict['approved_by'],
                approved_at=expense_data_dict['approved_at'],
                rejection_reason=expense_data_dict['rejection_reason'],
                vat_amount=expense_data_dict['vat_amount'],
                vat_rate=expense_data_dict['vat_rate'],
                created_at=expense_data_dict['created_at'],
                updated_at=expense_data_dict['updated_at'],
                receipt_ids=receipt_ids_list
            )
        )
        
    except HTTPException:
        try:
            await db.rollback()
        except Exception:
            pass
        raise
    except Exception as e:
        await db.rollback()
        logger.error("expense_creation_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create expense"
        )

@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List expenses for current user"""
    try:
        # Parse date strings if provided
        start_date_parsed = None
        end_date_parsed = None
        if start_date:
            try:
                start_date_parsed = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid start_date format. Expected YYYY-MM-DD, got: {start_date}"
                )
        if end_date:
            try:
                end_date_parsed = date.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid end_date format. Expected YYYY-MM-DD, got: {end_date}"
                )
        
        # Validate date range
        if start_date_parsed and end_date_parsed and start_date_parsed > end_date_parsed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date must be before or equal to end_date"
            )
        # Build base query (tenant + not deleted)
        query = select(Expense).where(
            Expense.tenant_id == current_user.tenant_id,
            Expense.deleted_at.is_(None)
        )

        # Filter by user unless they are admin (finance dashboards etc. need tenant-wide view)
        user_roles_result = await db.execute(
            select(Role.name).join(UserRole).where(UserRole.user_id == current_user.id)
        )
        user_roles = list(user_roles_result.scalars().all())
        is_admin = has_admin_role(user_roles)
        if not is_admin:
            query = query.where(Expense.submitted_by == current_user.id)
        
        # Apply filters
        if status_filter:
            query = query.where(Expense.status == status_filter)
        
        if start_date_parsed:
            query = query.where(Expense.expense_date >= start_date_parsed)
        
        if end_date_parsed:
            query = query.where(Expense.expense_date <= end_date_parsed)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.order_by(Expense.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        expenses = result.scalars().all()
        
        # Get receipt IDs for all expenses (best-effort; empty if receipt_documents unavailable)
        expense_ids_list = [str(exp.id) for exp in expenses]
        receipt_map: Dict[str, List[str]] = {}
        try:
            receipt_map = await get_expenses_receipt_ids_map(db, expense_ids_list, current_user.tenant_id)
        except Exception as rec_err:
            logger.warning("expense_list_receipt_map_failed", error=str(rec_err))
        
        def _to_uuid_list(rids: List[str]) -> List[UUID]:
            out = []
            for r in rids:
                try:
                    out.append(UUID(r) if isinstance(r, str) else r)
                except (ValueError, TypeError):
                    pass
            return out

        expense_responses = [
            ExpenseResponse(
                id=exp.id,
                tenant_id=exp.tenant_id,
                submitted_by=exp.submitted_by,
                amount=exp.amount,
                currency=exp.currency,
                expense_date=exp.expense_date,
                category=exp.category,
                description=exp.description,
                merchant_name=exp.merchant_name,
                status=exp.status,
                approval_status=exp.approval_status,
                approved_by=exp.approved_by,
                approved_at=exp.approved_at,
                rejection_reason=exp.rejection_reason,
                vat_amount=exp.vat_amount,
                vat_rate=exp.vat_rate,
                created_at=exp.created_at,
                updated_at=exp.updated_at,
                receipt_ids=_to_uuid_list(receipt_map.get(str(exp.id), []))
            )
            for exp in expenses
        ]
        
        return ExpenseListResponse(
            success=True,
            data=expense_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except (OperationalError, ProgrammingError) as e:
        logger.error("expense_list_failed", error=str(e), exc_info=True)
        msg = str(e).lower()
        if "column" in msg and "does not exist" in msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database schema is outdated. Run migrations: cd backend && alembic upgrade head (or apply migration SQL files)."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while listing expenses"
        )
    except Exception as e:
        logger.error("expense_list_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list expenses"
        )

@router.get("/pending-approvals", response_model=ExpenseListResponse)
async def list_pending_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List expenses pending approval by current user (as manager)"""
    try:
        user_roles_result = await db.execute(
            select(Role.name).join(UserRole).where(UserRole.user_id == current_user.id)
        )
        user_roles = list(user_roles_result.scalars().all())

        # Approvers (admin/approver/finance) can view all pending approvals.
        can_view_all_pending = can_approve_expense(user_roles)

        if can_view_all_pending:
            query = select(Expense).where(
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None),
                Expense.status == "submitted",
                Expense.approval_status == "pending",
            )
        else:
            # Managers can view pending approvals for direct reports only.
            manager_submitter_ids = (
                select(User.id).where(
                    User.tenant_id == current_user.tenant_id,
                    User.deleted_at.is_(None),
                    User.manager_id == current_user.id,
                )
            )
            query = select(Expense).where(
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None),
                Expense.status == "submitted",
                Expense.approval_status == "pending",
                Expense.submitted_by.in_(manager_submitter_ids),
            )
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.order_by(Expense.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        # Execute query
        result = await db.execute(query)
        expenses = result.scalars().all()
        
        # Preload submitter details so we can display "Submitted by" in the UI
        submitter_ids = {exp.submitted_by for exp in expenses}
        submitter_map: Dict[Any, Dict[str, Optional[str]]] = {}
        if submitter_ids:
            submitter_result = await db.execute(
                select(User.id, User.first_name, User.last_name, User.email).where(
                    User.id.in_(submitter_ids)
                )
            )
            for user_id, first_name, last_name, email in submitter_result.all():
                full_name_parts = [part for part in [first_name, last_name] if part]
                full_name = " ".join(full_name_parts) if full_name_parts else None
                submitter_map[user_id] = {
                    "name": full_name,
                    "email": email,
                }
        
        # Get receipt IDs for all expenses
        expense_ids_list = [str(exp.id) for exp in expenses]
        receipt_map = await get_expenses_receipt_ids_map(db, expense_ids_list, current_user.tenant_id)
        
        # Batch load submitter display names
        submitter_ids = list({exp.submitted_by for exp in expenses})
        submitter_result = await db.execute(
            select(User.id, User.first_name, User.last_name, User.email).where(
                User.id.in_(submitter_ids)
            )
        )
        submitter_rows = submitter_result.all()
        submitter_names = {}
        for row in submitter_rows:
            uid, fn, ln, em = row[0], row[1], row[2], row[3]
            parts = [p for p in (fn, ln) if p]
            submitter_names[str(uid)] = " ".join(parts) if parts else (em or str(uid))
        
        expense_responses = [
            ExpenseResponse(
                id=exp.id,
                tenant_id=exp.tenant_id,
                submitted_by=exp.submitted_by,
                submitted_by_name=submitter_map.get(exp.submitted_by, {}).get("name"),
                submitted_by_email=submitter_map.get(exp.submitted_by, {}).get("email"),
                amount=exp.amount,
                currency=exp.currency,
                expense_date=exp.expense_date,
                category=exp.category,
                description=exp.description,
                merchant_name=exp.merchant_name,
                status=exp.status,
                approval_status=exp.approval_status,
                approved_by=exp.approved_by,
                approved_at=exp.approved_at,
                rejection_reason=exp.rejection_reason,
                vat_amount=exp.vat_amount,
                vat_rate=exp.vat_rate,
                created_at=exp.created_at,
                updated_at=exp.updated_at,
                receipt_ids=receipt_map.get(str(exp.id), []),
                submitter_display_name=submitter_names.get(str(exp.submitted_by))
            )
            for exp in expenses
        ]
        
        return ExpenseListResponse(
            success=True,
            data=expense_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error("pending_approvals_list_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pending approvals"
        )

@router.get("/{expense_id}", response_model=ExpenseDetailResponse)
async def get_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get expense by ID"""
    try:
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Check access: submitter, or manager of submitter, or admin
        is_submitter = expense.submitted_by == current_user.id
        if not is_submitter:
            submitter_result = await db.execute(
                select(User).where(User.id == expense.submitted_by)
            )
            submitter = submitter_result.scalar_one_or_none()
            is_manager = submitter and submitter.manager_id == current_user.id
            user_roles_result = await db.execute(
                select(Role.name).join(UserRole).where(
                    UserRole.user_id == current_user.id
                )
            )
            user_roles = list(user_roles_result.scalars().all())
            is_admin = has_admin_role(user_roles)
            if not is_manager and not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized"
                )
        
        # Get linked receipt IDs
        from services.file_service.models import ReceiptDocument
        receipt_result = await db.execute(
            select(ReceiptDocument.id).where(
                and_(
                    ReceiptDocument.expense_id == expense.id,
                    ReceiptDocument.tenant_id == current_user.tenant_id,
                    ReceiptDocument.deleted_at.is_(None)
                )
            )
        )
        receipt_ids = [str(row[0]) for row in receipt_result.all()]
        
        # Submitter display name for Approvals UI
        submitter_display_name = None
        submitter_result = await db.execute(
            select(User).where(User.id == expense.submitted_by)
        )
        submitter = submitter_result.scalar_one_or_none()
        if submitter:
            parts = [p for p in (submitter.first_name, submitter.last_name) if p]
            submitter_display_name = " ".join(parts) if parts else submitter.email or str(expense.submitted_by)
        
        return ExpenseDetailResponse(
            success=True,
            data=ExpenseResponse(
                id=expense.id,
                tenant_id=expense.tenant_id,
                submitted_by=expense.submitted_by,
                amount=expense.amount,
                currency=expense.currency,
                expense_date=expense.expense_date,
                category=expense.category,
                description=expense.description,
                merchant_name=expense.merchant_name,
                status=expense.status,
                approval_status=expense.approval_status,
                approved_by=expense.approved_by,
                approved_at=expense.approved_at,
                rejection_reason=expense.rejection_reason,
                vat_amount=expense.vat_amount,
                vat_rate=expense.vat_rate,
                created_at=expense.created_at,
                updated_at=expense.updated_at,
                receipt_ids=receipt_ids,
                submitter_display_name=submitter_display_name
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("expense_get_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get expense"
        )


@router.get("/{expense_id}/duplicates")
async def get_expense_duplicates(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Detect potential duplicate expenses (same amount, date, merchant within tenant)."""
    try:
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        if expense.submitted_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        # Find others from same user, same amount, same date; optional same merchant
        from sqlalchemy import and_
        q = select(Expense).where(
            Expense.tenant_id == current_user.tenant_id,
            Expense.submitted_by == current_user.id,
            Expense.deleted_at.is_(None),
            Expense.id != expense.id,
            Expense.amount == expense.amount,
            Expense.expense_date == expense.expense_date,
        )
        if expense.merchant_name:
            q = q.where(Expense.merchant_name == expense.merchant_name)
        q = q.order_by(Expense.created_at.desc()).limit(10)
        dup_result = await db.execute(q)
        duplicates = dup_result.scalars().all()
        receipt_map = await get_expenses_receipt_ids_map(db, [str(e.id) for e in duplicates], current_user.tenant_id)
        return {
            "success": True,
            "expense_id": str(expense.id),
            "duplicates": [
                {
                    "id": str(e.id),
                    "amount": float(e.amount),
                    "currency": e.currency,
                    "expense_date": e.expense_date.isoformat() if e.expense_date else None,
                    "merchant_name": e.merchant_name,
                    "category": e.category,
                    "status": e.status,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                    "receipt_ids": receipt_map.get(str(e.id), []),
                }
                for e in duplicates
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("expense_duplicates_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check duplicates"
        )


@router.post("/{expense_id}/suggest-category")
async def suggest_expense_category(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Suggest category for expense (auto-categorization: LLM or rules)."""
    try:
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        if expense.submitted_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        # Rule-based suggestion from merchant/description
        merchant = (expense.merchant_name or "").lower()
        desc = (expense.description or "").lower()
        text = f"{merchant} {desc}"
        suggested = "other"
        if any(x in text for x in ["train", "sncf", "ouigo", "tgv", "rail"]):
            suggested = "travel"
        elif any(x in text for x in ["restaurant", "cafe", "café", "hotel", "food", "uber eats", "deliveroo"]):
            suggested = "meals"
        elif any(x in text for x in ["hotel", "booking", "airbnb", "logis"]):
            suggested = "accommodation"
        elif any(x in text for x in ["uber", "taxi", "fuel", "essence", "parking"]):
            suggested = "transport"
        elif any(x in text for x in ["amazon", "fnac", "computer", "laptop", "office"]):
            suggested = "office"
        elif any(x in text for x in ["formation", "training", "cours", "certification"]):
            suggested = "training"
        # Optional: call LLM service if available
        try:
            from services.llm_service.extractor import LLMExtractor
            from services.llm_service.schemas import ReceiptExtractionRequest
            extractor = LLMExtractor()
            req = ReceiptExtractionRequest(
                ocr_text=text or "No description",
                receipt_id=expense_id,
                tenant_id=str(current_user.tenant_id),
                language="fr",
            )
            extraction = await extractor.extract(req)
            if extraction and getattr(extraction, "category", None):
                suggested = extraction.category
        except Exception:
            pass
        return {"success": True, "expense_id": str(expense.id), "suggested_category": suggested}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("suggest_category_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suggest category"
        )


@router.put("/{expense_id}", response_model=ExpenseDetailResponse)
async def update_expense(
    expense_id: str,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update expense"""
    try:
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Check access and status
        if expense.submitted_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        if expense.status not in ["draft", "submitted"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update expense in current status"
            )
        
        # Update fields
        if expense_data.amount is not None:
            expense.amount = expense_data.amount
        if expense_data.currency is not None:
            expense.currency = expense_data.currency
        if expense_data.expense_date is not None:
            expense.expense_date = expense_data.expense_date
        if expense_data.category is not None:
            expense.category = expense_data.category
        if expense_data.description is not None:
            expense.description = expense_data.description
        if expense_data.merchant_name is not None:
            expense.merchant_name = expense_data.merchant_name
        if expense_data.vat_amount is not None:
            expense.vat_amount = expense_data.vat_amount
        if expense_data.vat_rate is not None:
            expense.vat_rate = expense_data.vat_rate
        
        # Re-evaluate policies after update
        try:
            user_roles_result = await db.execute(
                select(Role.name).join(UserRole).where(
                    UserRole.user_id == current_user.id
                )
            )
            # Use .scalars().all() for single-column selects in async SQLAlchemy
            user_roles = list(user_roles_result.scalars().all())
            
            policy_service = PolicyService(db)
            await policy_service.evaluate_and_save_violations(expense, user_roles)
        except Exception as e:
            logger.warning("policy_evaluation_failed_on_update", error=str(e), expense_id=str(expense.id))
        
        await db.commit()
        await db.refresh(expense)
        
        # Get receipt IDs
        receipt_ids = await get_expense_receipt_ids(db, str(expense.id), current_user.tenant_id)
        
        logger.info("expense_updated", expense_id=str(expense.id))
        
        return ExpenseDetailResponse(
            success=True,
            data=ExpenseResponse(
                id=expense.id,
                tenant_id=expense.tenant_id,
                submitted_by=expense.submitted_by,
                amount=expense.amount,
                currency=expense.currency,
                expense_date=expense.expense_date,
                category=expense.category,
                description=expense.description,
                merchant_name=expense.merchant_name,
                status=expense.status,
                approval_status=expense.approval_status,
                approved_by=expense.approved_by,
                approved_at=expense.approved_at,
                rejection_reason=expense.rejection_reason,
                vat_amount=expense.vat_amount,
                vat_rate=expense.vat_rate,
                created_at=expense.created_at,
                updated_at=expense.updated_at,
                receipt_ids=receipt_ids
            )
        )
        
    except HTTPException:
        try:
            await db.rollback()
        except Exception:
            pass
        raise
    except Exception as e:
        await db.rollback()
        logger.error("expense_update_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update expense"
        )

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete expense (soft delete)"""
    try:
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        # Check access
        if expense.submitted_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        # Soft delete
        from datetime import datetime
        expense.deleted_at = datetime.utcnow()
        
        await db.commit()
        
        logger.info("expense_deleted", expense_id=str(expense.id))
        
    except HTTPException:
        try:
            await db.rollback()
        except Exception:
            pass
        raise
    except Exception as e:
        await db.rollback()
        logger.error("expense_delete_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete expense"
        )

@router.post("/{expense_id}/submit", response_model=ExpenseDetailResponse)
async def submit_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit expense for approval"""
    try:
        # Capture current_user data IMMEDIATELY to avoid accessing detached object after rollback
        current_user_id = current_user.id
        current_user_tenant_id = current_user.tenant_id
        
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user_tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )
        
        if expense.submitted_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        if expense.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense already submitted"
            )
        
        # Capture expense ID and all data before policy evaluation (in case of rollback)
        captured_expense_id = expense.id
        submitted_by_id = expense.submitted_by
        tenant_id_val = expense.tenant_id
        expense_amount = expense.amount
        expense_currency = expense.currency
        expense_date_val = expense.expense_date
        expense_category = expense.category
        expense_merchant_name = expense.merchant_name
        expense_description = expense.description
        
        # Re-evaluate policies before submission
        try:
            user_roles_result = await db.execute(
                select(Role.name).select_from(UserRole).join(Role, UserRole.role_id == Role.id).where(
                    UserRole.user_id == current_user_id
                )
            )
            user_roles = [row[0] for row in user_roles_result.all()]
            
            policy_service = PolicyService(db)
            evaluation = await policy_service.evaluate_and_save_violations(expense, user_roles)
            
            # Block submission if there are error-level violations
            if not evaluation.can_submit:
                error_violations = [v for v in evaluation.violations if v.violation_severity.value == "error"]
                error_messages = [v.violation_message for v in error_violations]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot submit expense with policy violations: {'; '.join(error_messages)}"
                )
        except HTTPException:
            # HTTPException means policy violations - rollback and re-raise
            try:
                await db.rollback()
            except Exception:
                pass
            raise
        except Exception as e:
            # Database or other error in policy evaluation - rollback transaction
            try:
                await db.rollback()
            except Exception:
                pass
            # Use captured expense_id instead of accessing expense.id
            logger.warning("policy_evaluation_failed_on_submit", error=str(e), expense_id=str(captured_expense_id), exc_info=True)
            # Don't block submission if policy evaluation fails - log and continue
            # But we need to re-fetch the expense since we rolled back
            # Use captured tenant_id to avoid accessing current_user after rollback
            result = await db.execute(
                select(Expense).where(
                    Expense.id == captured_expense_id,
                    Expense.tenant_id == current_user_tenant_id,
                    Expense.deleted_at.is_(None)
                )
            )
            expense = result.scalar_one_or_none()
            if not expense:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Expense not found"
                )
            # Re-capture IDs after re-fetch
            captured_expense_id = expense.id
            submitted_by_id = expense.submitted_by
        
        expense.status = "submitted"
        expense.approval_status = "pending"
        
        # Assign manager as approver if user has a manager
        submitter_result = await db.execute(
            select(User).where(User.id == submitted_by_id)
        )
        submitter = submitter_result.scalar_one_or_none()
        submitter_manager_id = submitter.manager_id if submitter else None
        if submitter and submitter_manager_id:
            # In a full implementation, we'd set approver_id here
            # For now, we'll use the manager_id to route approvals
            logger.info(
                "expense_submitted_with_manager",
                expense_id=str(captured_expense_id),
                manager_id=str(submitter_manager_id)
            )
        
        await db.commit()
        
        # Try to refresh, but don't fail if it doesn't work
        try:
            await db.refresh(expense)
        except Exception as refresh_error:
            logger.warning("expense_refresh_failed_on_submit", error=str(refresh_error), expense_id=str(captured_expense_id))
        
        # Capture expense data before accessing potentially detached object
        expense_data_dict = {
            'id': captured_expense_id,
            'tenant_id': expense.tenant_id,
            'submitted_by': submitted_by_id,
            'amount': expense.amount,
            'currency': expense.currency,
            'expense_date': expense.expense_date,
            'category': expense.category,
            'description': expense.description,
            'merchant_name': expense.merchant_name,
            'status': expense.status,
            'approval_status': expense.approval_status,
            'approved_by': expense.approved_by,
            'approved_at': expense.approved_at,
            'rejection_reason': expense.rejection_reason,
            'vat_amount': expense.vat_amount,
            'vat_rate': expense.vat_rate,
            'created_at': expense.created_at,
            'updated_at': expense.updated_at,
        }
        
        # Update with refreshed values if refresh succeeded
        try:
            expense_data_dict['created_at'] = expense.created_at
            expense_data_dict['updated_at'] = expense.updated_at
        except Exception:
            pass  # Use captured values if refresh failed
        
        # Get receipt IDs
        receipt_ids = await get_expense_receipt_ids(db, str(captured_expense_id), current_user_tenant_id)
        
        # Send notification to manager (optional; skip if notification_service not installed)
        try:
            from services.notification_service.service import EmailNotificationService
            notification_service = EmailNotificationService(db)
            if submitter and submitter_manager_id:
                await notification_service.send_expense_submission_notification(
                    expense_id=captured_expense_id,
                    submitter_id=submitted_by_id,
                    approver_id=submitter_manager_id
                )
        except ModuleNotFoundError:
            pass  # Notification service not installed
        except Exception as e:
            logger.warning("notification_send_failed", error=str(e))
            # Don't fail expense submission if notification fails
        
        logger.info("expense_submitted", expense_id=str(captured_expense_id))
        
        return ExpenseDetailResponse(
            success=True,
            data=ExpenseResponse(
                id=expense_data_dict['id'],
                tenant_id=expense_data_dict['tenant_id'],
                submitted_by=expense_data_dict['submitted_by'],
                amount=expense_data_dict['amount'],
                currency=expense_data_dict['currency'],
                expense_date=expense_data_dict['expense_date'],
                category=expense_data_dict['category'],
                description=expense_data_dict['description'],
                merchant_name=expense_data_dict['merchant_name'],
                status=expense_data_dict['status'],
                approval_status=expense_data_dict['approval_status'],
                approved_by=expense_data_dict['approved_by'],
                approved_at=expense_data_dict['approved_at'],
                rejection_reason=expense_data_dict['rejection_reason'],
                vat_amount=expense_data_dict['vat_amount'],
                vat_rate=expense_data_dict['vat_rate'],
                created_at=expense_data_dict['created_at'],
                updated_at=expense_data_dict['updated_at'],
                receipt_ids=receipt_ids
            )
        )
        
    except HTTPException:
        # Rollback on HTTPException to ensure clean transaction state
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        raise
    except Exception as e:
        # Always rollback on any exception to ensure transaction is clean
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        logger.error("expense_submit_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit expense"
        )

@router.post("/{expense_id}/approve", response_model=ExpenseDetailResponse)
async def approve_expense(
    expense_id: str,
    request: ExpenseApproveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve expense"""
    try:
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )

        await require_approval_access(
            current_user,
            db,
            expense.submitted_by,
            endpoint="approve_expense",
            allow_owner=False,
        )

        if expense.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense is not pending approval"
            )
        
        from datetime import datetime
        expense.approval_status = "approved"
        expense.status = "approved"
        expense.approved_by = current_user.id
        expense.approved_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(expense)
        
        # Get receipt IDs
        receipt_ids = await get_expense_receipt_ids(db, str(expense.id), current_user.tenant_id)
        
        # Send notification to submitter (optional)
        try:
            from services.notification_service.service import EmailNotificationService
            notification_service = EmailNotificationService(db)
            await notification_service.send_expense_approval_notification(
                expense_id=expense.id,
                submitter_id=expense.submitted_by,
                approver_id=current_user.id,
                approved=True
            )
        except ModuleNotFoundError:
            pass
        except Exception as e:
            logger.warning("notification_send_failed", error=str(e))
        
        logger.info("expense_approved", expense_id=str(expense.id), approver_id=str(current_user.id))
        
        return ExpenseDetailResponse(
            success=True,
            data=ExpenseResponse(
                id=expense.id,
                tenant_id=expense.tenant_id,
                submitted_by=expense.submitted_by,
                amount=expense.amount,
                currency=expense.currency,
                expense_date=expense.expense_date,
                category=expense.category,
                description=expense.description,
                merchant_name=expense.merchant_name,
                status=expense.status,
                approval_status=expense.approval_status,
                approved_by=expense.approved_by,
                approved_at=expense.approved_at,
                rejection_reason=expense.rejection_reason,
                vat_amount=expense.vat_amount,
                vat_rate=expense.vat_rate,
                created_at=expense.created_at,
                updated_at=expense.updated_at,
                receipt_ids=receipt_ids
            )
        )
        
    except HTTPException:
        # Rollback on HTTPException to ensure clean transaction state
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        raise
    except Exception as e:
        # Always rollback on any exception to ensure transaction is clean
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        logger.error("expense_approve_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve expense"
        )

@router.post("/{expense_id}/reject", response_model=ExpenseDetailResponse)
async def reject_expense(
    expense_id: str,
    request: ExpenseRejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject expense"""
    try:
        result = await db.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.tenant_id == current_user.tenant_id,
                Expense.deleted_at.is_(None)
            )
        )
        expense = result.scalar_one_or_none()
        
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found"
            )

        await require_approval_access(
            current_user,
            db,
            expense.submitted_by,
            endpoint="reject_expense",
            allow_owner=False,
        )

        if expense.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense is not pending approval"
            )

        expense.approval_status = "rejected"
        expense.status = "rejected"
        expense.rejection_reason = request.reason
        
        await db.commit()
        await db.refresh(expense)
        
        # Get receipt IDs
        receipt_ids = await get_expense_receipt_ids(db, str(expense.id), current_user.tenant_id)
        
        # Send notification to submitter (optional)
        try:
            from services.notification_service.service import EmailNotificationService
            notification_service = EmailNotificationService(db)
            await notification_service.send_expense_approval_notification(
                expense_id=expense.id,
                submitter_id=expense.submitted_by,
                approver_id=current_user.id,
                approved=False
            )
        except ModuleNotFoundError:
            pass
        except Exception as e:
            logger.warning("notification_send_failed", error=str(e))
        
        logger.info("expense_rejected", expense_id=str(expense.id), rejector_id=str(current_user.id))
        
        return ExpenseDetailResponse(
            success=True,
            data=ExpenseResponse(
                id=expense.id,
                tenant_id=expense.tenant_id,
                submitted_by=expense.submitted_by,
                amount=expense.amount,
                currency=expense.currency,
                expense_date=expense.expense_date,
                category=expense.category,
                description=expense.description,
                merchant_name=expense.merchant_name,
                status=expense.status,
                approval_status=expense.approval_status,
                approved_by=expense.approved_by,
                approved_at=expense.approved_at,
                rejection_reason=expense.rejection_reason,
                vat_amount=expense.vat_amount,
                vat_rate=expense.vat_rate,
                created_at=expense.created_at,
                updated_at=expense.updated_at,
                receipt_ids=receipt_ids
            )
        )
        
    except HTTPException:
        # Rollback on HTTPException to ensure clean transaction state
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        raise
    except Exception as e:
        # Always rollback on any exception to ensure transaction is clean
        try:
            await db.rollback()
        except Exception:
            pass  # Ignore rollback errors
        logger.error("expense_reject_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject expense"
        )

# Phase 28 Routes - Offline Support

@router.post("/offline/draft", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_offline_draft(
    draft_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create expense draft (offline support)"""
    try:
        from .offline_service import OfflineExpenseService
        
        service = OfflineExpenseService(db, str(current_user.tenant_id))
        
        result = await service.create_draft(
            draft_data=draft_data,
            user_id=str(current_user.id),
            client_id=draft_data.get("client_id")
        )
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("create_offline_draft_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create draft")

@router.post("/offline/sync", response_model=Dict[str, Any])
async def sync_offline_drafts(
    drafts: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sync offline drafts"""
    try:
        from .offline_service import OfflineExpenseService
        
        service = OfflineExpenseService(db, str(current_user.tenant_id))
        
        result = await service.sync_drafts(
            drafts=drafts,
            user_id=str(current_user.id)
        )
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("sync_offline_drafts_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to sync drafts")

@router.get("/offline/pending", response_model=List[Dict[str, Any]])
async def get_pending_drafts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending drafts for offline sync"""
    try:
        from .offline_service import OfflineExpenseService
        
        service = OfflineExpenseService(db, str(current_user.tenant_id))
        
        result = await service.get_pending_drafts(user_id=str(current_user.id))
        
        return result
    except Exception as e:
        logger.error("get_pending_drafts_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get pending drafts")
