# -----------------------------------------------------------------------------
# File: test_vat_calculation.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: Unit tests for VAT calculation validation
# -----------------------------------------------------------------------------

"""
Unit Tests for VAT Calculation Validation
"""
import pytest
from decimal import Decimal
from services.vat_service.engine import VATRulesEngine
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_vat_calculation_validation_correct():
    """Test VAT calculation validation with correct values"""
    # Mock database session
    db = None  # Will be mocked in actual test setup
    engine = VATRulesEngine(db, "test-tenant-id")
    
    # Test case: €100 total, 20% VAT, €16.67 VAT (correct)
    result = await engine.validate_vat_calculation(
        total_amount=Decimal("100.00"),
        vat_rate=Decimal("20.0"),
        vat_amount=Decimal("16.67")
    )
    
    assert result["is_valid"] is True
    assert abs(float(result["expected_vat"]) - 16.67) < 0.01


@pytest.mark.asyncio
async def test_vat_calculation_validation_incorrect():
    """Test VAT calculation validation with incorrect values"""
    db = None
    engine = VATRulesEngine(db, "test-tenant-id")
    
    # Test case: €100 total, 20% VAT, €20 VAT (incorrect - should be €16.67)
    result = await engine.validate_vat_calculation(
        total_amount=Decimal("100.00"),
        vat_rate=Decimal("20.0"),
        vat_amount=Decimal("20.00")
    )
    
    assert result["is_valid"] is False
    assert float(result["difference"]) > 3.0  # Significant difference


@pytest.mark.asyncio
async def test_vat_calculation_standard_rates():
    """Test VAT calculation for standard French rates"""
    db = None
    engine = VATRulesEngine(db, "test-tenant-id")
    
    test_cases = [
        (Decimal("100.00"), Decimal("20.0"), Decimal("16.67")),  # 20%
        (Decimal("100.00"), Decimal("10.0"), Decimal("9.09")),   # 10%
        (Decimal("100.00"), Decimal("5.5"), Decimal("5.21")),    # 5.5%
        (Decimal("100.00"), Decimal("2.1"), Decimal("2.06")),     # 2.1%
    ]
    
    for total, rate, expected_vat in test_cases:
        result = await engine.validate_vat_calculation(
            total_amount=total,
            vat_rate=rate,
            vat_amount=expected_vat
        )
        assert result["is_valid"] is True, f"Failed for {rate}% rate"


@pytest.mark.asyncio
async def test_mixed_vat_receipt():
    """Test mixed VAT receipt handling"""
    db = None
    engine = VATRulesEngine(db, "test-tenant-id")
    
    line_items = [
        {"amount": 50.00, "vat_rate": 20.0, "vat_amount": 8.33},
        {"amount": 30.00, "vat_rate": 10.0, "vat_amount": 2.73},
        {"amount": 20.00, "vat_rate": 5.5, "vat_amount": 1.04}
    ]
    
    result = await engine.handle_mixed_vat_receipt(line_items)
    
    assert result["is_valid"] is True
    assert abs(float(result["total_amount"]) - 100.00) < 0.01
    assert len(result["by_rate"]) == 3  # Three different rates


@pytest.mark.asyncio
async def test_vat_rate_determination_category():
    """Test VAT rate determination by category"""
    db = None
    engine = VATRulesEngine(db, "test-tenant-id")
    
    # Test restaurant category (should be 10%)
    result = await engine.determine_vat_rate(category="restaurant")
    assert float(result["vat_rate"]) == 10.0
    
    # Test food category (should be 5.5%)
    result = await engine.determine_vat_rate(category="food")
    assert float(result["vat_rate"]) == 5.5
    
    # Test default category (should be 20%)
    result = await engine.determine_vat_rate(category="office_supplies")
    assert float(result["vat_rate"]) == 20.0

