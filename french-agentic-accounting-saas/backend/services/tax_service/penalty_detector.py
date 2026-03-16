"""
FISCA Enhancement - Penalty Detector.
Predicts late filing penalties and flags missing declarations.
"""
import structlog
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import TaxCalendar, TaxDeclaration

logger = structlog.get_logger()

# French tax penalty rates
PENALTY_RATES = {
    "late_filing": Decimal("0.10"),      # 10% majoration for late filing
    "late_payment": Decimal("0.05"),     # 5% majoration for late payment (first month)
    "interest_per_month": Decimal("0.004"),  # 0.4% interest per month
    "minimum_penalty": Decimal("150"),    # Minimum penalty amount
}


async def detect_overdue_declarations(
    db: AsyncSession, tenant_id: UUID, as_of: date = None
) -> list[dict]:
    """Find declarations that are overdue and estimate penalties."""
    if as_of is None:
        as_of = date.today()

    result = await db.execute(
        select(TaxCalendar).where(
            TaxCalendar.tenant_id == tenant_id,
            TaxCalendar.due_date < as_of,
            TaxCalendar.status.in_(["upcoming", "due", "overdue"]),
        ).order_by(TaxCalendar.due_date)
    )
    overdue_items = list(result.scalars().all())

    warnings = []
    for item in overdue_items:
        days_overdue = (as_of - item.due_date).days

        # Update status if needed
        if item.status != "overdue":
            item.status = "overdue"

        # Estimate penalty
        penalty = estimate_penalty(item.declaration_type, days_overdue)

        warnings.append({
            "calendar_id": str(item.id),
            "declaration_type": item.declaration_type,
            "due_date": item.due_date.isoformat(),
            "days_overdue": days_overdue,
            "estimated_penalty": str(penalty),
            "message": _penalty_message(item.declaration_type, days_overdue, penalty),
        })

    if overdue_items:
        await db.flush()

    logger.info("penalty_detection_complete", overdue=len(warnings))
    return warnings


def estimate_penalty(declaration_type: str, days_overdue: int) -> Decimal:
    """Estimate penalty amount for a late declaration."""
    if days_overdue <= 0:
        return Decimal("0")

    # Base penalty: 10% majoration
    base_penalty = PENALTY_RATES["late_filing"]

    # Monthly interest: 0.4% per month
    months_late = max(1, days_overdue // 30)
    interest = PENALTY_RATES["interest_per_month"] * months_late

    # For CA3, typical amounts
    estimated_base = Decimal("5000")  # Placeholder for average VAT amount
    if declaration_type == "IS":
        estimated_base = Decimal("20000")
    elif declaration_type == "CVAE":
        estimated_base = Decimal("3000")

    penalty = estimated_base * (base_penalty + interest)
    return max(penalty, PENALTY_RATES["minimum_penalty"]).quantize(Decimal("0.01"))


def _penalty_message(declaration_type: str, days_overdue: int, penalty: Decimal) -> str:
    """Generate French penalty warning message."""
    type_labels = {
        "CA3": "Declaration de TVA (CA3)",
        "CA12": "Declaration annuelle de TVA (CA12)",
        "IS": "Declaration d'impot sur les societes",
        "CVAE": "Declaration de CVAE",
        "CFE": "Cotisation fonciere des entreprises",
        "DAS2": "Declaration des honoraires (DAS2)",
    }
    label = type_labels.get(declaration_type, declaration_type)

    if days_overdue <= 30:
        urgency = "Attention"
    elif days_overdue <= 90:
        urgency = "Urgent"
    else:
        urgency = "Critique"

    return (
        f"{urgency}: {label} en retard de {days_overdue} jours. "
        f"Penalite estimee: {penalty} EUR. "
        f"Deposez la declaration au plus vite pour limiter les majorations."
    )


async def check_upcoming_deadlines(
    db: AsyncSession, tenant_id: UUID, days_ahead: int = 30
) -> list[dict]:
    """Find declarations due within the next N days."""
    today = date.today()
    deadline = today + timedelta(days=days_ahead)

    result = await db.execute(
        select(TaxCalendar).where(
            TaxCalendar.tenant_id == tenant_id,
            TaxCalendar.due_date.between(today, deadline),
            TaxCalendar.status.in_(["upcoming", "due"]),
        ).order_by(TaxCalendar.due_date)
    )
    items = list(result.scalars().all())

    upcoming = []
    for item in items:
        days_until = (item.due_date - today).days
        if days_until <= 7 and item.status == "upcoming":
            item.status = "due"

        upcoming.append({
            "calendar_id": str(item.id),
            "declaration_type": item.declaration_type,
            "due_date": item.due_date.isoformat(),
            "days_until": days_until,
            "status": item.status,
        })

    if items:
        await db.flush()

    return upcoming
