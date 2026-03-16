"""E-Invoice Service API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import structlog
from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .service import EInvoiceService
from .schemas import InvoiceCreate, InvoiceResponse, InvoiceListResponse, InvoiceLineResponse

logger = structlog.get_logger()
router = APIRouter()

def invoice_to_response(inv) -> InvoiceResponse:
    return InvoiceResponse(
        id=inv.id, invoice_number=inv.invoice_number, type=inv.type,
        format=inv.format, status=inv.status, issuer_name=inv.issuer_name,
        recipient_name=inv.recipient_name, issue_date=inv.issue_date,
        due_date=inv.due_date, total_ht=inv.total_ht, total_vat=inv.total_vat,
        total_ttc=inv.total_ttc, currency=inv.currency, ppf_status=inv.ppf_status,
        lines=[InvoiceLineResponse(
            id=l.id, line_number=l.line_number, description=l.description,
            quantity=l.quantity, unit_price=l.unit_price, vat_rate=l.vat_rate,
            line_total_ht=l.line_total_ht, line_total_vat=l.line_total_vat,
            account_code=l.account_code,
        ) for l in (inv.lines or [])],
        created_at=inv.created_at,
    )

@router.get("", response_model=InvoiceListResponse)
async def list_invoices(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                        type: Optional[str] = None, status: Optional[str] = None,
                        db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import select, func
    from sqlalchemy.orm.attributes import set_committed_value
    from .models import Invoice, InvoiceLine

    query = select(Invoice).where(Invoice.tenant_id == current_user.tenant_id)
    count_query = select(func.count(Invoice.id)).where(Invoice.tenant_id == current_user.tenant_id)
    if type:
        query = query.where(Invoice.type == type)
        count_query = count_query.where(Invoice.type == type)
    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    query = query.order_by(Invoice.issue_date.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    invoices = list(result.scalars().all())
    for inv in invoices:
        lines_result = await db.execute(
            select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id).order_by(InvoiceLine.line_number))
        set_committed_value(inv, 'lines', list(lines_result.scalars().all()))
    return InvoiceListResponse(data=[invoice_to_response(i) for i in invoices], total=total, page=page, page_size=page_size)

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = EInvoiceService(db)
    inv = await svc.get_invoice(current_user.tenant_id, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Facture non trouvee")
    return invoice_to_response(inv)

@router.post("", response_model=InvoiceResponse)
async def create_invoice(payload: InvoiceCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = EInvoiceService(db)
    inv = await svc.create_invoice(
        current_user.tenant_id, current_user.id,
        payload.model_dump(exclude={"lines"}),
        [l.model_dump() for l in payload.lines],
    )
    await db.commit()
    return invoice_to_response(inv)
