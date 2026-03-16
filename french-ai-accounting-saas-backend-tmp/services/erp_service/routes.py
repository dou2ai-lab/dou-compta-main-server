# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: ERP service routes
# -----------------------------------------------------------------------------

"""
ERP Service Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user, get_user_permissions
from .accounting_poster import AccountingPoster
from .sepa_builder import SEPABuilder
from .reconciliation import ReconciliationService
from .schemas import (
    ERPConnectionCreate,
    ERPConnectionResponse,
    PostExpenseRequest,
    PostExpenseResponse,
    SEPACreateRequest,
    SEPACreateResponse,
    CardPaymentImportRequest,
    CardPaymentImportResponse,
    ManualReconcileRequest
)

logger = structlog.get_logger()
router = APIRouter()

async def require_erp_permission(current_user: User, db: AsyncSession):
    """Check if user has ERP permissions"""
    permissions = await get_user_permissions(current_user, db)
    if "erp:write" not in permissions and "admin:write" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERP access required"
        )

# Phase 25 Routes

@router.post("/connections", response_model=ERPConnectionResponse)
async def create_erp_connection(
    request: ERPConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create ERP connection"""
    await require_erp_permission(current_user, db)
    
    try:
        from .models import ERPConnection
        
        connection = ERPConnection(
            tenant_id=current_user.tenant_id,
            provider=request.provider,
            connection_type=request.connection_type,
            configuration=request.configuration,
            created_by=current_user.id
        )
        
        db.add(connection)
        await db.flush()
        
        return ERPConnectionResponse(
            id=str(connection.id),
            provider=connection.provider,
            connection_type=connection.connection_type,
            is_active=connection.is_active,
            last_sync_at=connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            last_sync_status=connection.last_sync_status,
            created_at=connection.created_at.isoformat()
        )
    except Exception as e:
        await db.rollback()
        logger.error("create_erp_connection_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create ERP connection")

@router.post("/post-expense", response_model=PostExpenseResponse)
async def post_expense(
    request: PostExpenseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Post expense to ERP with VAT segmentation"""
    await require_erp_permission(current_user, db)
    
    try:
        poster = AccountingPoster(db, str(current_user.tenant_id))
        
        result = await poster.post_expense(
            expense_id=request.expense_id,
            erp_connection_id=request.erp_connection_id,
            posting_date=request.posting_date
        )
        
        await db.commit()
        
        return PostExpenseResponse(**result)
    except Exception as e:
        await db.rollback()
        logger.error("post_expense_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to post expense to ERP")

# Phase 26 Routes

@router.post("/sepa/create", response_model=SEPACreateResponse)
async def create_sepa_file(
    request: SEPACreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create SEPA file for reimbursement"""
    await require_erp_permission(current_user, db)
    
    try:
        builder = SEPABuilder(db, str(current_user.tenant_id))
        
        result = await builder.create_sepa_file(
            expense_ids=request.expense_ids,
            creditor_iban=request.creditor_iban,
            creditor_bic=request.creditor_bic,
            creditor_name=request.creditor_name,
            execution_date=request.execution_date,
            created_by=str(current_user.id)
        )
        
        return SEPACreateResponse(**result)
    except Exception as e:
        logger.error("create_sepa_file_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create SEPA file")

@router.post("/reconciliation/import", response_model=CardPaymentImportResponse)
async def import_card_payment(
    request: CardPaymentImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Import card payment and attempt reconciliation"""
    await require_erp_permission(current_user, db)
    
    try:
        service = ReconciliationService(db, str(current_user.tenant_id))
        
        result = await service.import_card_payment(
            card_transaction_id=request.card_transaction_id,
            card_last_four=request.card_last_four,
            merchant_name=request.merchant_name,
            transaction_date=request.transaction_date,
            amount=request.amount,
            currency=request.currency,
            metadata=request.metadata
        )
        
        await db.commit()
        
        return CardPaymentImportResponse(**result)
    except Exception as e:
        await db.rollback()
        logger.error("import_card_payment_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to import card payment")

@router.post("/reconciliation/manual", response_model=Dict[str, Any])
async def manual_reconcile(
    request: ManualReconcileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually reconcile card payment"""
    await require_erp_permission(current_user, db)
    
    try:
        service = ReconciliationService(db, str(current_user.tenant_id))
        
        result = await service.manual_reconcile(
            reconciliation_id=request.reconciliation_id,
            expense_id=request.expense_id,
            reviewed_by=str(current_user.id)
        )
        
        await db.commit()
        
        return result
    except Exception as e:
        await db.rollback()
        logger.error("manual_reconcile_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reconcile")

@router.get("/reconciliation/unmatched", response_model=List[Dict[str, Any]])
async def list_unmatched_payments(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List unmatched card payments"""
    await require_erp_permission(current_user, db)
    
    try:
        service = ReconciliationService(db, str(current_user.tenant_id))
        
        result = await service.list_unmatched_payments(limit=limit)
        
        return result
    except Exception as e:
        logger.error("list_unmatched_payments_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list unmatched payments")




