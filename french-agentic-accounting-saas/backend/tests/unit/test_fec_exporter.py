# -----------------------------------------------------------------------------
# File: test_fec_exporter.py
# Description: Unit tests for FEC exporter
# -----------------------------------------------------------------------------

"""Unit tests for FEC exporter."""
import pytest
from datetime import date

from services.accounting_service.fec_exporter import (
    format_fec_date,
    format_fec_amount,
    get_fec_filename,
)


class TestFormatFecDate:
    def test_standard_date(self):
        assert format_fec_date(date(2025, 1, 15)) == "20250115"

    def test_year_end(self):
        assert format_fec_date(date(2025, 12, 31)) == "20251231"

    def test_first_day(self):
        assert format_fec_date(date(2025, 1, 1)) == "20250101"


class TestFormatFecAmount:
    def test_positive_amount(self):
        assert format_fec_amount(100.50) == "100,50"

    def test_zero(self):
        assert format_fec_amount(0) == "0,00"

    def test_none(self):
        assert format_fec_amount(None) == "0,00"

    def test_large_amount(self):
        assert format_fec_amount(1234567.89) == "1234567,89"

    def test_negative(self):
        result = format_fec_amount(-50.00)
        assert "50,00" in result


class TestGetFecFilename:
    def test_standard(self):
        assert get_fec_filename("123456789", 2025) == "123456789FEC20251231.txt"

    def test_different_year(self):
        assert get_fec_filename("987654321", 2024) == "987654321FEC20241231.txt"
