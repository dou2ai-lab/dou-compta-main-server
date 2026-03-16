"""CLASSA Agent - Document classification using LLM."""
import structlog
from typing import Optional

logger = structlog.get_logger()

# Document type classification rules
DOCUMENT_TYPES = {
    "facture": {"keywords": ["facture", "invoice", "n° facture", "total ttc", "tva"], "route": "einvoice_service"},
    "releve_bancaire": {"keywords": ["releve", "solde", "debit", "credit", "iban", "bic"], "route": "banking_service"},
    "bulletin_paie": {"keywords": ["bulletin", "salaire", "brut", "net", "urssaf", "cotisation"], "route": "payroll_service"},
    "note_frais": {"keywords": ["note de frais", "remboursement", "deplacement", "repas"], "route": "expense"},
    "contrat": {"keywords": ["contrat", "convention", "parties", "signataire"], "route": "dossier_service"},
    "declaration": {"keywords": ["declaration", "cerfa", "dgfip", "impot", "tva ca3"], "route": "tax_service"},
    "kbis": {"keywords": ["kbis", "extrait", "rcs", "greffe"], "route": "dossier_service"},
    "rib": {"keywords": ["rib", "releve d'identite", "iban", "domiciliation"], "route": "banking_service"},
}


def classify_document(text_content: str, filename: Optional[str] = None) -> dict:
    """Classify a document based on its text content and filename.
    Returns document type and suggested routing."""
    text_lower = (text_content or "").lower()
    filename_lower = (filename or "").lower()
    combined = f"{text_lower} {filename_lower}"

    scores = {}
    for doc_type, config in DOCUMENT_TYPES.items():
        score = sum(1 for kw in config["keywords"] if kw in combined)
        if score > 0:
            scores[doc_type] = score

    if not scores:
        return {
            "document_type": "autre",
            "confidence": 0.0,
            "route": None,
            "alternatives": [],
        }

    sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_type = sorted_types[0][0]
    best_score = sorted_types[0][1]
    max_possible = len(DOCUMENT_TYPES[best_type]["keywords"])
    confidence = min(best_score / max(max_possible, 1), 1.0)

    return {
        "document_type": best_type,
        "confidence": round(confidence, 2),
        "route": DOCUMENT_TYPES[best_type]["route"],
        "alternatives": [{"type": t, "score": s} for t, s in sorted_types[1:3]],
    }
