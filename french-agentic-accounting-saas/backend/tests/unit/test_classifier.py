# -----------------------------------------------------------------------------
# File: test_classifier.py
# Description: Unit tests for document classifier (CLASSA agent)
# -----------------------------------------------------------------------------

"""Unit tests for document classifier (CLASSA agent)."""
import pytest

from services.collection_service.classifier import classify_document


class TestClassifyDocument:
    def test_classify_invoice(self):
        text = "FACTURE N\u00b0 F-2025-001 Total TTC: 1200.00 EUR TVA 20%"
        result = classify_document(text, "facture_2025.pdf")
        assert result["document_type"] == "facture"
        assert result["confidence"] > 0.3

    def test_classify_bank_statement(self):
        text = "Releve de compte IBAN FR76 1234 Solde debiteur Credit Debit"
        result = classify_document(text)
        assert result["document_type"] == "releve_bancaire"

    def test_classify_payslip(self):
        text = "Bulletin de salaire Brut Net URSSAF Cotisation retraite"
        result = classify_document(text)
        assert result["document_type"] == "bulletin_paie"

    def test_classify_expense_note(self):
        text = "Note de frais deplacement repas remboursement"
        result = classify_document(text)
        assert result["document_type"] == "note_frais"

    def test_classify_unknown(self):
        text = "Lorem ipsum dolor sit amet"
        result = classify_document(text)
        assert result["document_type"] == "autre"
        assert result["confidence"] == 0.0

    def test_has_route(self):
        result = classify_document("facture total ttc tva n\u00b0 facture")
        assert result["route"] is not None

    def test_alternatives_provided(self):
        text = "facture releve bancaire"
        result = classify_document(text)
        assert isinstance(result["alternatives"], list)
