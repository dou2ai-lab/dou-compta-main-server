# -----------------------------------------------------------------------------
# File: test_accounting_validation.py
# Description: Unit tests for accounting validation service
# -----------------------------------------------------------------------------

"""Unit tests for accounting validation service."""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from services.accounting_service.validation_service import ValidationError


class TestValidationError:
    def test_to_dict(self):
        err = ValidationError("balance", "Desequilibre", "error")
        d = err.to_dict()
        assert d["field"] == "balance"
        assert d["message"] == "Desequilibre"
        assert d["severity"] == "error"

    def test_default_severity(self):
        err = ValidationError("test", "msg")
        assert err.severity == "error"

    def test_warning_severity(self):
        err = ValidationError("test", "msg", "warning")
        assert err.severity == "warning"
