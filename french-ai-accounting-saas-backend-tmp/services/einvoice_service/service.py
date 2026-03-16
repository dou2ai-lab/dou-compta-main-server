"""E-Invoice Service - Business logic."""
import structlog
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID, uuid4
from datetime import date, datetime
from .models import Invoice, InvoiceLine
from .facturx_generator import generate_facturx_xml

logger = structlog.get_logger()

class EInvoiceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_invoices(self, tenant_id: UUID, page: int = 1, page_size: int = 20,
                            type_filter: Optional[str] = None, status: Optional[str] = None) -> tuple[list[Invoice], int]:
        query = select(Invoice).where(Invoice.tenant_id == tenant_id)
        count_query = select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
        if type_filter:
            query = query.where(Invoice.type == type_filter)
            count_query = count_query.where(Invoice.type == type_filter)
        if status:
            query = query.where(Invoice.status == status)
            count_query = count_query.where(Invoice.status == status)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        query = query.order_by(Invoice.issue_date.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        invoices = list(result.scalars().all())
        for inv in invoices:
            lines_result = await self.db.execute(
                select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id).order_by(InvoiceLine.line_number))
            from sqlalchemy.orm.attributes import set_committed_value; set_committed_value(inv, 'lines', list(lines_result.scalars().all()))
        return invoices, total

    async def get_invoice(self, tenant_id: UUID, invoice_id: UUID) -> Optional[Invoice]:
        result = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id))
        inv = result.scalar_one_or_none()
        if inv:
            lines_result = await self.db.execute(
                select(InvoiceLine).where(InvoiceLine.invoice_id == inv.id).order_by(InvoiceLine.line_number))
            from sqlalchemy.orm.attributes import set_committed_value; set_committed_value(inv, 'lines', list(lines_result.scalars().all()))
        return inv

    async def create_invoice(self, tenant_id: UUID, user_id: UUID, data: dict, lines_data: list[dict]) -> Invoice:
        # Generate invoice number
        count_result = await self.db.execute(
            select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id))
        count = count_result.scalar() or 0
        invoice_number = data.get("invoice_number") or f"FAC-{count + 1:06d}"

        # Calculate totals
        total_ht = Decimal("0")
        total_vat = Decimal("0")
        lines = []
        for i, ld in enumerate(lines_data):
            qty = Decimal(str(ld.get("quantity", 1)))
            price = Decimal(str(ld["unit_price"]))
            rate = Decimal(str(ld.get("vat_rate", 20)))
            line_ht = (qty * price).quantize(Decimal("0.01"))
            line_vat = (line_ht * rate / 100).quantize(Decimal("0.01"))
            total_ht += line_ht
            total_vat += line_vat
            lines.append(InvoiceLine(
                id=uuid4(), line_number=i + 1, description=ld["description"],
                quantity=qty, unit_price=price, vat_rate=rate,
                line_total_ht=line_ht, line_total_vat=line_vat,
                account_code=ld.get("account_code"),
            ))

        invoice = Invoice(
            tenant_id=tenant_id, invoice_number=invoice_number,
            type=data.get("type", "sent"), issue_date=data["issue_date"],
            due_date=data.get("due_date"), recipient_name=data.get("recipient_name", ""),
            recipient_siren=data.get("recipient_siren"),
            recipient_vat_number=data.get("recipient_vat_number"),
            total_ht=total_ht, total_vat=total_vat, total_ttc=total_ht + total_vat,
            notes=data.get("notes"),
        )
        invoice.lines = lines

        # Generate Factur-X XML
        xml = generate_facturx_xml({
            "invoice_number": invoice_number,
            "issue_date": str(data["issue_date"]),
            "issuer_name": "", "issuer_vat_number": "",
            "recipient_name": data.get("recipient_name", ""),
            "recipient_vat_number": data.get("recipient_vat_number", ""),
            "currency": "EUR",
            "total_ht": str(total_ht), "total_vat": str(total_vat), "total_ttc": str(total_ht + total_vat),
        }, [])
        invoice.xml_payload = xml
        invoice.format = "facturx"

        self.db.add(invoice)
        await self.db.flush()
        return invoice
