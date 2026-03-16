# -----------------------------------------------------------------------------
# File: test_reconciliation.py
# Description: Unit tests for reconciliation engine
# -----------------------------------------------------------------------------

"""Unit tests for reconciliation engine."""
import pytest

from services.banking_service.reconciliation_engine import label_similarity


class TestLabelSimilarity:
    def test_identical(self):
        assert label_similarity("Paiement facture", "Paiement facture") == 1.0

    def test_partial_overlap(self):
        sim = label_similarity("Paiement facture client", "Paiement facture")
        assert 0.5 < sim < 1.0

    def test_no_overlap(self):
        assert label_similarity("ABC DEF", "XYZ QRS") == 0.0

    def test_empty_strings(self):
        assert label_similarity("", "") == 0.0

    def test_none_strings(self):
        assert label_similarity(None, "test") == 0.0

    def test_case_insensitive(self):
        assert label_similarity("PAIEMENT", "paiement") == 1.0
