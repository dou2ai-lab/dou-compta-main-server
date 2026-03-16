# -----------------------------------------------------------------------------
# File: test_accounting_entry_generator.py
# Description: Unit tests for the accounting entry generator (COMPTAA Agent)
# -----------------------------------------------------------------------------

"""Unit tests for the accounting entry generator (COMPTAA Agent)."""
import pytest
from decimal import Decimal
from datetime import date

from services.accounting_service.entry_generator import (
    resolve_expense_account,
    compute_vat_decomposition,
    CATEGORY_ACCOUNT_MAP,
)


class TestResolveExpenseAccount:
    def test_gl_account_code_takes_priority(self):
        assert resolve_expense_account("repas", "606400") == "606400"

    def test_category_mapping_repas(self):
        assert resolve_expense_account("Repas client", None) == "625700"

    def test_category_mapping_transport(self):
        assert resolve_expense_account("Transport taxi", None) == "625100"

    def test_category_mapping_hotel(self):
        assert resolve_expense_account("Hotel Paris", None) == "625600"

    def test_category_mapping_fournitures(self):
        assert resolve_expense_account("Fournitures bureau", None) == "606400"

    def test_category_mapping_telecom(self):
        assert resolve_expense_account("Telephone mobile", None) == "626000"

    def test_category_mapping_honoraires(self):
        assert resolve_expense_account("Honoraires consulting", None) == "622600"

    def test_unknown_category_returns_default(self):
        assert resolve_expense_account("xyz_unknown_category", None) == "628000"

    def test_empty_category_returns_default(self):
        assert resolve_expense_account("", None) == "628000"

    def test_none_category_returns_default(self):
        assert resolve_expense_account(None, None) == "628000"

    def test_case_insensitive(self):
        assert resolve_expense_account("RESTAURANT", None) == "625700"


class TestComputeVatDecomposition:
    def test_standard_20_percent(self):
        ht, vat = compute_vat_decomposition(Decimal("120.00"), Decimal("20"))
        assert ht == Decimal("100.00")
        assert vat == Decimal("20.00")

    def test_intermediate_10_percent(self):
        ht, vat = compute_vat_decomposition(Decimal("110.00"), Decimal("10"))
        assert ht == Decimal("100.00")
        assert vat == Decimal("10.00")

    def test_reduced_5_5_percent(self):
        ht, vat = compute_vat_decomposition(Decimal("105.50"), Decimal("5.5"))
        assert ht == Decimal("100.00")
        assert vat == Decimal("5.50")

    def test_super_reduced_2_1_percent(self):
        ht, vat = compute_vat_decomposition(Decimal("102.10"), Decimal("2.1"))
        assert ht == Decimal("100.00")
        assert vat == Decimal("2.10")

    def test_zero_vat_rate(self):
        ht, vat = compute_vat_decomposition(Decimal("100.00"), Decimal("0"))
        assert ht == Decimal("100.00")
        assert vat == Decimal("0")

    def test_none_vat_rate(self):
        ht, vat = compute_vat_decomposition(Decimal("100.00"), None)
        assert ht == Decimal("100.00")
        assert vat == Decimal("0")

    def test_real_receipt_amount(self):
        # Real-world: restaurant bill 45.50 EUR TTC at 10%
        ht, vat = compute_vat_decomposition(Decimal("45.50"), Decimal("10"))
        assert ht + vat == Decimal("45.50")
        assert ht == Decimal("41.36")
        assert vat == Decimal("4.14")

    def test_rounding_consistency(self):
        ht, vat = compute_vat_decomposition(Decimal("99.99"), Decimal("20"))
        assert ht + vat == Decimal("99.99")
