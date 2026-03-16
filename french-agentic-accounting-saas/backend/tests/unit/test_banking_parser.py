# -----------------------------------------------------------------------------
# File: test_banking_parser.py
# Description: Unit tests for bank statement parser
# -----------------------------------------------------------------------------

"""Unit tests for bank statement parser."""
import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4

from services.banking_service.statement_parser import (
    parse_csv_statement,
    _parse_french_date,
    _parse_french_amount,
)


class TestParseFrenchDate:
    def test_dd_mm_yyyy_slash(self):
        assert _parse_french_date("15/01/2025") == date(2025, 1, 15)

    def test_dd_mm_yyyy_dash(self):
        assert _parse_french_date("15-01-2025") == date(2025, 1, 15)

    def test_iso_format(self):
        assert _parse_french_date("2025-01-15") == date(2025, 1, 15)

    def test_invalid_date(self):
        assert _parse_french_date("not a date") is None

    def test_empty_string(self):
        assert _parse_french_date("") is None


class TestParseFrenchAmount:
    def test_comma_decimal(self):
        assert _parse_french_amount("1234,56") == Decimal("1234.56")

    def test_dot_decimal(self):
        assert _parse_french_amount("1234.56") == Decimal("1234.56")

    def test_space_thousand_separator(self):
        assert _parse_french_amount("1 234,56") == Decimal("1234.56")

    def test_negative(self):
        assert _parse_french_amount("-50,00") == Decimal("-50.00")

    def test_empty(self):
        assert _parse_french_amount("") == Decimal("0")

    def test_none_like(self):
        assert _parse_french_amount("   ") == Decimal("0")


class TestParseCSVStatement:
    def test_basic_csv(self):
        csv_content = "date;libelle;montant\n15/01/2025;Achat CB;-45,50\n16/01/2025;Virement recu;1200,00\n"
        account_id = uuid4()
        txns = parse_csv_statement(csv_content, account_id)
        assert len(txns) == 2
        assert txns[0]["amount"] == Decimal("-45.50")
        assert txns[1]["amount"] == Decimal("1200.00")
        assert txns[0]["label"] == "Achat CB"

    def test_debit_credit_columns(self):
        csv_content = "date;libelle;debit;credit\n15/01/2025;Paiement;45,50;\n16/01/2025;Encaissement;;1200,00\n"
        account_id = uuid4()
        txns = parse_csv_statement(csv_content, account_id)
        assert len(txns) == 2
        assert txns[0]["amount"] < 0  # debit is negative
        assert txns[1]["amount"] > 0  # credit is positive

    def test_empty_csv(self):
        csv_content = "date;libelle;montant\n"
        txns = parse_csv_statement(csv_content, uuid4())
        assert len(txns) == 0
