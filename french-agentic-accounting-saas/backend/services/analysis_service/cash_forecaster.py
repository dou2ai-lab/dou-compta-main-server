"""
FORECASTA Agent - Cash Flow Forecasting.
Simple linear trend forecasting for cash position.
"""
import structlog
from decimal import Decimal
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from services.accounting_service.models import JournalEntry, JournalEntryLine

logger = structlog.get_logger()


async def forecast_cash(
    db: AsyncSession,
    tenant_id: UUID,
    horizon_days: int = 30,
) -> dict:
    """
    Forecast cash position using simple linear trend.
    Analyzes bank journal (BNQ) entries over past 90 days to predict future.
    """
    today = date.today()
    lookback_start = today - timedelta(days=90)

    # Get daily net cash flow from bank journal entries
    result = await db.execute(
        select(
            JournalEntry.entry_date,
            func.sum(JournalEntryLine.debit).label("total_debit"),
            func.sum(JournalEntryLine.credit).label("total_credit"),
        ).select_from(
            JournalEntryLine.__table__.join(
                JournalEntry.__table__,
                JournalEntryLine.entry_id == JournalEntry.id,
            )
        ).where(
            JournalEntry.tenant_id == tenant_id,
            JournalEntry.entry_date.between(lookback_start, today),
            JournalEntry.status.in_(["validated", "posted"]),
            JournalEntryLine.account_code.like("5%"),  # Class 5 = financial accounts
        ).group_by(JournalEntry.entry_date)
        .order_by(JournalEntry.entry_date)
    )
    daily_data = result.all()

    if len(daily_data) < 5:
        return {
            "type": "cash_position",
            "horizon_days": horizon_days,
            "forecast_date": today.isoformat(),
            "data_points": [],
            "confidence": 0,
            "model_used": "insufficient_data",
        }

    # Compute cumulative cash position
    cumulative = Decimal("0")
    points = []
    for row in daily_data:
        net = (row.total_debit or Decimal("0")) - (row.total_credit or Decimal("0"))
        cumulative += net
        days_from_start = (row.entry_date - lookback_start).days
        points.append((days_from_start, float(cumulative)))

    # Simple linear regression
    n = len(points)
    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_x2 = sum(p[0] ** 2 for p in points)

    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        slope = 0
        intercept = sum_y / n
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

    # Generate forecast points
    base_day = (today - lookback_start).days
    forecast_points = []
    for d in range(1, horizon_days + 1):
        future_day = base_day + d
        predicted = intercept + slope * future_day
        margin = abs(predicted * 0.1)  # 10% confidence band
        forecast_points.append({
            "date": (today + timedelta(days=d)).isoformat(),
            "value": str(round(predicted, 2)),
            "lower_bound": str(round(predicted - margin, 2)),
            "upper_bound": str(round(predicted + margin, 2)),
        })

    # R-squared for confidence
    mean_y = sum_y / n
    ss_tot = sum((p[1] - mean_y) ** 2 for p in points)
    ss_res = sum((p[1] - (intercept + slope * p[0])) ** 2 for p in points)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    confidence = max(0, min(1, r_squared))

    logger.info("cash_forecast_computed", horizon=horizon_days, confidence=round(confidence, 4))

    return {
        "type": "cash_position",
        "horizon_days": horizon_days,
        "forecast_date": today.isoformat(),
        "data_points": forecast_points,
        "confidence": round(confidence, 4),
        "model_used": "linear",
    }
