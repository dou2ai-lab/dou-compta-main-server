# -----------------------------------------------------------------------------
# File: test_pcg_seed.py
# Description: Unit tests for PCG seed data
# -----------------------------------------------------------------------------

"""Unit tests for PCG seed data."""
import pytest

from services.accounting_service.pcg_seed import get_pcg_seed_data


class TestPCGSeedData:
    def test_seed_data_not_empty(self):
        data = get_pcg_seed_data()
        assert len(data) > 50

    def test_all_classes_present(self):
        data = get_pcg_seed_data()
        classes = set(d["account_class"] for d in data)
        for c in range(1, 9):
            assert c in classes, f"Class {c} missing from PCG seed data"

    def test_required_fields(self):
        data = get_pcg_seed_data()
        for d in data:
            assert "account_code" in d
            assert "account_name" in d
            assert "account_class" in d
            assert "account_type" in d

    def test_key_accounts_present(self):
        data = get_pcg_seed_data()
        codes = {d["account_code"] for d in data}
        required = ["101000", "401000", "411000", "512000", "607000", "701000", "445660", "445710"]
        for code in required:
            assert code in codes, f"Account {code} missing"

    def test_account_types_valid(self):
        data = get_pcg_seed_data()
        valid_types = {"asset", "liability", "equity", "revenue", "expense"}
        for d in data:
            assert d["account_type"] in valid_types, f"Invalid type {d['account_type']} for {d['account_code']}"

    def test_account_code_format(self):
        data = get_pcg_seed_data()
        for d in data:
            assert len(d["account_code"]) == 6, f"Account code {d['account_code']} not 6 digits"
            assert d["account_code"].isdigit(), f"Account code {d['account_code']} not numeric"
