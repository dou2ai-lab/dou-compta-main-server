# -----------------------------------------------------------------------------
# Document classifier for pipeline: invoice | receipt | bank_statement | payslip | other
# Keyword-based (Phase 1). Optional LLM classification can be added later.
# -----------------------------------------------------------------------------
"""
Document classification for the receipt/invoice pipeline.
Returns one of: invoice, receipt, bank_statement, payslip, other.
"""
from __future__ import annotations

from typing import Tuple

import structlog

logger = structlog.get_logger()

# Categories required by the pipeline
DOCUMENT_CATEGORIES = ("invoice", "receipt", "bank_statement", "payslip", "other")

# Keyword rules: category -> list of keywords (lowercase)
KEYWORDS: dict[str, list[str]] = {
    "invoice": [
        "facture", "invoice", "n° facture", "n facture", "numero facture",
        "total ttc", "tva", "montant ttc", "facture n", "bill",
    ],
    "receipt": [
        "reçu", "receipt", "ticket", "caisse", "merci de votre achat",
        "total", "payé", "carte bancaire", "espèces",
    ],
    "bank_statement": [
        "releve", "relevé", "solde", "debit", "credit", "iban", "bic",
        "compte", "extrait de compte", "bank statement",
    ],
    "payslip": [
        "bulletin", "salaire", "brut", "net a payer", "net à payer",
        "urssaf", "cotisation", "paie", "payslip", "salaire net",
    ],
}


def classify_document(ocr_text: str) -> str:
    """
    Classify document from OCR text into one of:
    invoice, receipt, bank_statement, payslip, other.

    Uses keyword scoring. Returns the category with highest score, or "other" if none.
    """
    if not ocr_text or not ocr_text.strip():
        return "other"

    text_lower = ocr_text.lower().strip()
    scores: dict[str, int] = {}

    for category, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "other"

    best = max(scores.items(), key=lambda x: x[1])
    return best[0]


def classify_document_with_confidence(ocr_text: str) -> Tuple[str, float]:
    """
    Same as classify_document but returns (category, confidence 0.0–1.0).
    """
    if not ocr_text or not ocr_text.strip():
        return "other", 0.0

    text_lower = ocr_text.lower().strip()
    scores: dict[str, int] = {}

    for category, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "other", 0.0

    best_category = max(scores.items(), key=lambda x: x[1])
    max_possible = len(KEYWORDS.get(best_category[0], []))
    confidence = min(best_category[1] / max(max_possible, 1), 1.0)
    return best_category[0], round(confidence, 2)
