# -----------------------------------------------------------------------------
# Document classifier for pipeline: invoice | receipt | bank_statement | payslip | other
# Keyword-based (Phase 1). Optional LLM classification can be added later.
# -----------------------------------------------------------------------------
"""
Document classification for the receipt/invoice pipeline.

Legacy categories (kept for backward compatibility):
- invoice, receipt, bank_statement, payslip, other

PRD categories:
- facture_achat, facture_vente, releve_bancaire, bulletin_paie, autre
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


def classify_document_prd(ocr_text: str) -> str:
    """
    PRD classifier mapping to:
    facture_achat | facture_vente | releve_bancaire | bulletin_paie | autre

    Phase-1 heuristic:
    - bank_statement -> releve_bancaire
    - payslip -> bulletin_paie
    - invoice/receipt -> default facture_achat unless we see strong "vente" signals
    """
    legacy = classify_document(ocr_text)
    text = (ocr_text or "").lower()

    if legacy == "bank_statement":
        return "releve_bancaire"
    if legacy == "payslip":
        return "bulletin_paie"
    if legacy in ("invoice", "receipt"):
        # Heuristic sales invoice cues
        vente_signals = (
            "facture de vente",
            "client",
            "bill to",
            "ship to",
            "customer",
            "acheteur",
            "buyer",
        )
        if any(s in text for s in vente_signals):
            return "facture_vente"
        return "facture_achat"
    return "autre"


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
