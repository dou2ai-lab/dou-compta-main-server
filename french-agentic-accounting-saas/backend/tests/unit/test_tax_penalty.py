# -----------------------------------------------------------------------------
# File: test_tax_penalty.py
# Description: Unit tests for tax penalty detection
# -----------------------------------------------------------------------------

"""Unit tests for tax penalty detection."""
import pytest
from decimal import Decimal

from services.tax_service.penalty_detector import estimate_penalty, _penalty_message


class TestEstimatePenalty:
    def test_no_penalty_if_not_overdue(self):
        assert estimate_penalty("CA3", 0) == Decimal("0")

    def test_penalty_for_overdue_ca3(self):
        penalty = estimate_penalty("CA3", 30)
        assert penalty >= Decimal("150")  # minimum penalty

    def test_penalty_increases_with_days(self):
        p30 = estimate_penalty("CA3", 30)
        p90 = estimate_penalty("CA3", 90)
        assert p90 > p30

    def test_is_penalty_higher_than_ca3(self):
        p_is = estimate_penalty("IS", 30)
        p_ca3 = estimate_penalty("CA3", 30)
        assert p_is > p_ca3  # IS has higher base


class TestPenaltyMessage:
    def test_message_french(self):
        msg = _penalty_message("CA3", 15, Decimal("500"))
        assert "CA3" in msg or "TVA" in msg
        assert "15 jours" in msg
        assert "500" in msg

    def test_urgency_levels(self):
        msg_short = _penalty_message("CA3", 10, Decimal("100"))
        msg_long = _penalty_message("CA3", 100, Decimal("100"))
        assert "Attention" in msg_short
        assert "Critique" in msg_long
