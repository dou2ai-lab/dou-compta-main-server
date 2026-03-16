# -----------------------------------------------------------------------------
# File: test_charge_allocator.py
# Description: Unit tests for payroll charge allocator
# -----------------------------------------------------------------------------

"""Unit tests for payroll charge allocator."""
import pytest
from decimal import Decimal

from services.payroll_service.charge_allocator import allocate_charges


class TestAllocateCharges:
    def test_basic_allocation(self):
        data = {
            "gross_salary": "3000",
            "net_salary": "2300",
            "employer_charges": "1200",
            "urssaf": "400",
            "retirement": "200",
        }
        lines = allocate_charges(data)
        assert len(lines) == 6

    def test_debit_credit_balance(self):
        data = {
            "gross_salary": "3000",
            "net_salary": "2300",
            "employer_charges": "1200",
            "urssaf": "400",
            "retirement": "200",
        }
        lines = allocate_charges(data)
        total_debit = sum(Decimal(str(l["debit"])) for l in lines)
        total_credit = sum(Decimal(str(l["credit"])) for l in lines)
        assert total_debit == total_credit

    def test_correct_accounts(self):
        data = {"gross_salary": "3000", "net_salary": "2300", "employer_charges": "1200", "urssaf": "400", "retirement": "200"}
        lines = allocate_charges(data)
        accounts = [l["account_code"] for l in lines]
        assert "641100" in accounts  # Salaries
        assert "421000" in accounts  # Personnel
        assert "431000" in accounts  # Securite sociale

    def test_gross_salary_debit(self):
        data = {"gross_salary": "5000", "net_salary": "3800", "employer_charges": "2000", "urssaf": "600", "retirement": "300"}
        lines = allocate_charges(data)
        salary_line = next(l for l in lines if l["account_code"] == "641100")
        assert salary_line["debit"] == Decimal("5000")
        assert salary_line["credit"] == Decimal("0")
