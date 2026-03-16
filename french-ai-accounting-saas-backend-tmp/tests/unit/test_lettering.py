# -----------------------------------------------------------------------------
# File: test_lettering.py
# Description: Unit tests for lettering service
# -----------------------------------------------------------------------------

"""Unit tests for lettering service."""
import pytest

from services.accounting_service.lettering_service import generate_lettering_code


class TestGenerateLetteringCode:
    def test_first_code(self):
        assert generate_lettering_code(0) == "AA"

    def test_second_code(self):
        assert generate_lettering_code(1) == "AB"

    def test_26th_code(self):
        assert generate_lettering_code(26) == "BA"

    def test_last_of_first_series(self):
        assert generate_lettering_code(25) == "AZ"
