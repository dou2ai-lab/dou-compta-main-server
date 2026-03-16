# -----------------------------------------------------------------------------
# File: anomaly_rules.py
# Description: Deterministic rule-based anomaly reason codes (5.2.2)
# -----------------------------------------------------------------------------

"""
Rule-based anomaly detection: VAT, timing, approval limits, missing docs.
Returns list of reason codes e.g. ["ML_OUTLIER","MISSING_VAT","NEAR_APPROVAL_LIMIT"].
"""
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from common.models import Expense

# Reason codes for anomaly_reasons JSONB
REASON_ML_OUTLIER = "ML_OUTLIER"
REASON_MISSING_VAT = "MISSING_VAT"
REASON_NEAR_APPROVAL_LIMIT = "NEAR_APPROVAL_LIMIT"
REASON_WEEKEND = "WEEKEND"
REASON_LATE_NIGHT = "LATE_NIGHT"  # if we had time; expense_date only has date
REASON_END_OF_MONTH = "END_OF_MONTH_CLUSTER"
REASON_RECURRING_JUST_UNDER_LIMIT = "RECURRING_JUST_UNDER_LIMIT"
REASON_MISSING_RECEIPT = "MISSING_RECEIPT"
REASON_MISSING_MANDATORY_FIELDS = "MISSING_MANDATORY_FIELDS"

# Default approval limit threshold (e.g. 90% of 500 = 450)
APPROVAL_LIMIT_DEFAULT = 500.0
NEAR_LIMIT_RATIO = 0.9


async def get_rule_based_reasons(
    db: AsyncSession,
    expense: Expense,
    is_ml_anomaly: bool,
    has_receipt: Optional[bool] = None,
) -> List[str]:
    """
    Compute deterministic anomaly reason codes for an expense.
    has_receipt: if None, will be queried from receipt_documents.
    """
    reasons: List[str] = []

    if is_ml_anomaly:
        reasons.append(REASON_ML_OUTLIER)

    # VAT: missing where expected (simplified: amount > 0 and no vat_amount)
    if expense.amount and float(expense.amount) > 0:
        if not expense.vat_amount or float(expense.vat_amount or 0) == 0:
            reasons.append(REASON_MISSING_VAT)

    # Weekend
    if expense.expense_date and expense.expense_date.weekday() >= 5:
        reasons.append(REASON_WEEKEND)

    # End of month (last 7 days)
    if expense.expense_date and expense.expense_date.day >= 25:
        reasons.append(REASON_END_OF_MONTH)

    # Near approval limit (amount just below threshold)
    amount_val = float(expense.amount) if expense.amount else 0
    if amount_val >= APPROVAL_LIMIT_DEFAULT * NEAR_LIMIT_RATIO and amount_val < APPROVAL_LIMIT_DEFAULT:
        reasons.append(REASON_NEAR_APPROVAL_LIMIT)

    # Missing receipt: check receipt_documents if not provided
    if has_receipt is None:
        has_receipt = await _expense_has_receipt(db, expense.id)
    if has_receipt is False:
        reasons.append(REASON_MISSING_RECEIPT)

    # Missing mandatory fields (Appvizer: category and merchant or description)
    if not expense.category or (not expense.merchant_name and not expense.description):
        reasons.append(REASON_MISSING_MANDATORY_FIELDS)

    # Recurring just under limit: would need history per merchant/employee - skip for now or add later
    return reasons


async def _expense_has_receipt(db: AsyncSession, expense_id) -> bool:
    """Check if expense has at least one receipt document."""
    try:
        from sqlalchemy import text
        result = await db.execute(
            text(
                "SELECT 1 FROM receipt_documents WHERE expense_id = :eid AND deleted_at IS NULL LIMIT 1"
            ),
            {"eid": str(expense_id)}
        )
        row = result.fetchone()
        return row is not None
    except Exception:
        return False
