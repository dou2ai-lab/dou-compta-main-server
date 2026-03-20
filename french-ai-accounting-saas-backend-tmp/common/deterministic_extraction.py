"""
Deterministic (rules/regex) extraction for critical accounting fields.

Used to:
- Extract totals/VAT/dates deterministically from OCR text (page-aware)
- Cross-check LLM output and flag inconsistencies
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .receipt_extraction import extract_from_ocr_text


@dataclass
class DeterministicCritical:
    total_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    vat_rate: Optional[float] = None
    expense_date: Optional[str] = None
    merchant_name: Optional[str] = None


def extract_invoice_critical_from_pages(pages: List[Dict[str, Any]]) -> DeterministicCritical:
    """
    Invoice heuristic:
    - totals/VAT from the LAST page (often summary page)
    - date/merchant from earliest page where found
    """
    if not pages:
        return DeterministicCritical()

    last_text = (pages[-1].get("text") or pages[-1].get("raw_text") or "").strip()
    last = extract_from_ocr_text(last_text) if last_text else {}

    out = DeterministicCritical(
        total_amount=last.get("total_amount"),
        vat_amount=last.get("vat_amount"),
        vat_rate=last.get("vat_rate"),
    )

    for p in pages:
        t = (p.get("text") or p.get("raw_text") or "").strip()
        if not t:
            continue
        d = extract_from_ocr_text(t)
        if out.expense_date is None and d.get("expense_date"):
            out.expense_date = d.get("expense_date")
        if out.merchant_name is None and d.get("merchant_name"):
            out.merchant_name = d.get("merchant_name")
        if out.expense_date and out.merchant_name:
            break

    return out


def compare_numbers(a: Any, b: Any, *, tolerance: float = 0.02) -> bool:
    """Return True if values match within tolerance (absolute)."""
    try:
        fa = float(a)
        fb = float(b)
    except (TypeError, ValueError):
        return False
    return abs(fa - fb) <= tolerance


def cross_check_invoice_llm(
    *,
    deterministic: DeterministicCritical,
    llm: Dict[str, Any],
) -> Tuple[List[str], Dict[str, str]]:
    """
    Returns (flags, reasoning) for mismatches.
    """
    flags: List[str] = []
    reasoning: Dict[str, str] = {}

    if deterministic.total_amount is not None and llm.get("total_amount") is not None:
        if not compare_numbers(deterministic.total_amount, llm.get("total_amount")):
            flags.append("inconsistent_total_amount")
            reasoning["total_amount"] = f"Deterministic={deterministic.total_amount} vs LLM={llm.get('total_amount')}"

    if deterministic.vat_amount is not None and llm.get("vat_amount") is not None:
        if not compare_numbers(deterministic.vat_amount, llm.get("vat_amount")):
            flags.append("inconsistent_vat_amount")
            reasoning["vat_amount"] = f"Deterministic={deterministic.vat_amount} vs LLM={llm.get('vat_amount')}"

    if deterministic.expense_date and llm.get("expense_date"):
        if str(deterministic.expense_date) != str(llm.get("expense_date")):
            flags.append("inconsistent_expense_date")
            reasoning["expense_date"] = f"Deterministic={deterministic.expense_date} vs LLM={llm.get('expense_date')}"

    return flags, reasoning

