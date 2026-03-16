# -----------------------------------------------------------------------------
# File: test_notification_engine.py
# Description: Unit tests for notification engine
# -----------------------------------------------------------------------------

"""Unit tests for notification engine."""
import pytest

from services.notification_service.engine import (
    render_template,
    _evaluate_condition,
    TEMPLATES,
)


class TestRenderTemplate:
    def test_expense_approved(self):
        title, body, priority = render_template("expense.approved", {"amount": "150"})
        assert "approuvee" in title.lower() or "approuv\u00e9e" in title.lower() or "Depense" in title
        assert "150" in body

    def test_declaration_due(self):
        title, body, priority = render_template("declaration.due", {"declaration_type": "CA3", "due_date": "2025-03-15"})
        assert "fiscale" in title.lower() or "Echeance" in title
        assert priority == "high"

    def test_unknown_event(self):
        title, body, priority = render_template("unknown.event", {"foo": "bar"})
        assert title  # should have a fallback title


class TestEvaluateCondition:
    def test_empty_condition(self):
        assert _evaluate_condition({}, {"anything": "value"}) is True

    def test_simple_match(self):
        assert _evaluate_condition({"status": "approved"}, {"status": "approved"}) is True

    def test_simple_no_match(self):
        assert _evaluate_condition({"status": "approved"}, {"status": "rejected"}) is False

    def test_gt_operator(self):
        assert _evaluate_condition(
            {"amount": {"op": "gt", "value": 100}},
            {"amount": 150}
        ) is True

    def test_lt_operator(self):
        assert _evaluate_condition(
            {"amount": {"op": "lt", "value": 100}},
            {"amount": 50}
        ) is True
