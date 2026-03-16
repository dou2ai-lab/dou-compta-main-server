# -----------------------------------------------------------------------------
# File: test_scoring_engine.py
# Description: Unit tests for financial scoring engine
# -----------------------------------------------------------------------------

"""Unit tests for financial scoring engine."""
import pytest

from services.analysis_service.scoring_engine import compute_score, _to_decimal


class TestComputeScore:
    def test_excellent_score(self):
        sig = {"ebe": "50000", "chiffre_affaires": "200000"}
        ratios = {"marge_nette": "15", "ratio_liquidite": "3", "ratio_endettement": "0.3"}
        result = compute_score(sig, ratios)
        assert result["overall_score"] >= 80
        assert result["category"] == "excellent"

    def test_weak_score(self):
        sig = {"ebe": "1000", "chiffre_affaires": "200000"}
        ratios = {"marge_nette": "-5", "ratio_liquidite": "0.3", "ratio_endettement": "5"}
        result = compute_score(sig, ratios)
        assert result["overall_score"] < 40
        assert result["category"] in ("weak", "critical")

    def test_has_recommendations(self):
        sig = {"ebe": "1000", "chiffre_affaires": "200000"}
        ratios = {"marge_nette": "1", "ratio_liquidite": "0.5", "ratio_endettement": "3"}
        result = compute_score(sig, ratios)
        assert len(result["recommendations"]) > 0

    def test_missing_data_returns_moderate(self):
        result = compute_score({}, {})
        assert 20 <= result["overall_score"] <= 60


class TestToDecimal:
    def test_string(self):
        assert _to_decimal("10.5") == pytest.approx(10.5, abs=0.01)

    def test_none(self):
        assert _to_decimal(None) is None

    def test_invalid(self):
        assert _to_decimal("not_a_number") is None
