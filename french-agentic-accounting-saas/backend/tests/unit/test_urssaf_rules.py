# -----------------------------------------------------------------------------
# File: test_urssaf_rules.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: Unit tests for URSSAF rules engine
# -----------------------------------------------------------------------------

"""
Unit Tests for URSSAF Rules Engine
"""
import pytest
from decimal import Decimal
from datetime import date
from services.urssaf_service.rules import URSSAFRulesEngine


def test_urssaf_reimbursement_exempt():
    """Test that reimbursements are exempt from URSSAF"""
    engine = URSSAFRulesEngine()
    
    expense_data = {
        "amount": Decimal("100.00"),
        "category": "meal",
        "expense_type": "reimbursement",
        "employee_type": "employee",
        "description": "Meal reimbursement",
        "expense_date": date.today()
    }
    
    result = engine.evaluate_expense(expense_data)
    
    assert result["exemption_applicable"] is True
    assert result["contribution_applicable"] is False
    assert result["compliance_status"] == "compliant"
    assert "reimbursement" in result["exemption_reason"].lower()


def test_urssaf_employee_benefit_contribution():
    """Test that employee benefits require contribution"""
    engine = URSSAFRulesEngine()
    
    expense_data = {
        "amount": Decimal("100.00"),
        "category": "equipment",
        "expense_type": "benefit",
        "employee_type": "employee",
        "description": "Equipment provided to employee",
        "expense_date": date.today()
    }
    
    result = engine.evaluate_expense(expense_data)
    
    assert result["contribution_applicable"] is True
    assert float(result["contribution_rate"]) == 20.0
    assert float(result["contribution_amount"]) == 20.0  # 20% of €100
    assert result["compliance_status"] == "compliant"


def test_urssaf_contractor_exempt():
    """Test that contractor expenses don't require employer contribution"""
    engine = URSSAFRulesEngine()
    
    expense_data = {
        "amount": Decimal("100.00"),
        "category": "service",
        "expense_type": "benefit",
        "employee_type": "contractor",
        "description": "Contractor service",
        "expense_date": date.today()
    }
    
    result = engine.evaluate_expense(expense_data)
    
    assert result["contribution_applicable"] is False
    assert result["compliance_status"] == "compliant"
    assert "contractor" in result["explanation"].lower()


def test_urssaf_meal_exemption_threshold():
    """Test meal exemption threshold (€5.55)"""
    engine = URSSAFRulesEngine()
    
    # Below threshold
    expense_data = {
        "amount": Decimal("5.00"),
        "category": "meal",
        "expense_type": "benefit",
        "employee_type": "employee",
        "description": "Small meal",
        "expense_date": date.today()
    }
    
    result = engine.evaluate_expense(expense_data)
    assert result["exemption_applicable"] is True
    assert "threshold" in result["exemption_reason"].lower()
    
    # Above threshold
    expense_data["amount"] = Decimal("10.00")
    result = engine.evaluate_expense(expense_data)
    assert result["exemption_applicable"] is False
    assert result["contribution_applicable"] is True


def test_urssaf_gift_exemption_threshold():
    """Test gift exemption threshold (€73.00)"""
    engine = URSSAFRulesEngine()
    
    # Below threshold
    expense_data = {
        "amount": Decimal("50.00"),
        "category": "gift",
        "expense_type": "benefit",
        "employee_type": "employee",
        "description": "Employee gift",
        "expense_date": date.today()
    }
    
    result = engine.evaluate_expense(expense_data)
    assert result["exemption_applicable"] is True
    
    # Above threshold
    expense_data["amount"] = Decimal("100.00")
    result = engine.evaluate_expense(expense_data)
    assert result["exemption_applicable"] is False


def test_urssaf_transport_exempt():
    """Test that transport expenses are exempt"""
    engine = URSSAFRulesEngine()
    
    expense_data = {
        "amount": Decimal("50.00"),
        "category": "transport",
        "expense_type": "reimbursement",
        "employee_type": "employee",
        "description": "Transport reimbursement",
        "expense_date": date.today()
    }
    
    result = engine.evaluate_expense(expense_data)
    assert result["exemption_applicable"] is True
    assert "transport" in result["exemption_reason"].lower()

