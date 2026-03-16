# -----------------------------------------------------------------------------
# File: rules.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: URSSAF compliance rules engine (deterministic, no LLMs)
# -----------------------------------------------------------------------------

"""
URSSAF Compliance Rules Engine
Deterministic rule-based engine for French URSSAF compliance
NO LLMs - all logic is rule-based for compliance accuracy
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import date
import structlog

logger = structlog.get_logger()


class URSSAFRulesEngine:
    """Deterministic URSSAF rules engine"""
    
    # Standard URSSAF contribution rates (2025)
    STANDARD_CONTRIBUTION_RATES = {
        "employee_benefit": Decimal("20.0"),  # 20% for employee benefits
        "reimbursement": Decimal("0.0"),  # Reimbursements are exempt
        "meal_voucher": Decimal("0.0"),  # Meal vouchers exempt
        "transport": Decimal("0.0"),  # Transport reimbursements exempt
        "training": Decimal("0.0"),  # Training expenses exempt
        "equipment": Decimal("20.0"),  # Equipment provided to employees
    }
    
    # Exemption thresholds (2025)
    EXEMPTION_THRESHOLDS = {
        "meal": Decimal("5.55"),  # Meal expenses below €5.55 are exempt
        "gift": Decimal("73.00"),  # Gifts below €73 are exempt
        "transport": Decimal("0.0"),  # No threshold - always exempt if reimbursement
    }
    
    # Employee vs Contractor classification rules
    CLASSIFICATION_RULES = {
        "employee": {
            "indicators": ["salary", "payroll", "employment_contract", "cdi", "cdd"],
            "contribution_required": True
        },
        "contractor": {
            "indicators": ["freelance", "consultant", "service_contract", "auto_entrepreneur"],
            "contribution_required": False  # Contractor pays own URSSAF
        },
        "intern": {
            "indicators": ["internship", "stage", "apprentice"],
            "contribution_required": False  # Interns exempt
        }
    }
    
    def __init__(self):
        """Initialize rules engine"""
        self.rules = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default URSSAF rules"""
        # Default rules for common scenarios
        self.rules = [
            {
                "name": "meal_reimbursement_exempt",
                "type": "exemption",
                "category": "meal",
                "expense_type": "reimbursement",
                "exemption_applicable": True,
                "contribution_rate": Decimal("0.0")
            },
            {
                "name": "transport_reimbursement_exempt",
                "type": "exemption",
                "category": "transport",
                "expense_type": "reimbursement",
                "exemption_applicable": True,
                "contribution_rate": Decimal("0.0")
            },
            {
                "name": "employee_benefit_standard",
                "type": "contribution",
                "expense_type": "benefit",
                "employee_type": "employee",
                "contribution_rate": Decimal("20.0"),
                "exemption_applicable": False
            },
            {
                "name": "small_meal_exemption",
                "type": "exemption_threshold",
                "category": "meal",
                "amount_threshold": Decimal("5.55"),
                "exemption_applicable": True,
                "contribution_rate": Decimal("0.0")
            },
            {
                "name": "gift_exemption_threshold",
                "type": "exemption_threshold",
                "category": "gift",
                "amount_threshold": Decimal("73.00"),
                "exemption_applicable": True,
                "contribution_rate": Decimal("0.0")
            }
        ]
    
    def evaluate_expense(
        self,
        expense_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate expense against URSSAF rules
        
        Args:
            expense_data: {
                "amount": Decimal,
                "category": str,
                "expense_type": str,  # benefit, reimbursement
                "employee_type": str,  # employee, contractor, intern
                "description": str,
                "expense_date": date
            }
        
        Returns:
            {
                "is_compliant": bool,
                "compliance_status": str,
                "risk_level": str,
                "expense_classification": str,
                "contribution_applicable": bool,
                "contribution_rate": Decimal,
                "contribution_amount": Decimal,
                "exemption_applicable": bool,
                "exemption_reason": str,
                "rule_applied": str,
                "explanation": str,
                "recommendations": List[str]
            }
        """
        try:
            amount = Decimal(str(expense_data.get("amount", 0)))
            category = expense_data.get("category", "").lower()
            expense_type = expense_data.get("expense_type", "").lower()
            employee_type = expense_data.get("employee_type", "employee").lower()
            description = expense_data.get("description", "").lower()
            
            # Step 1: Classify expense
            classification = self._classify_expense(category, expense_type, description)
            
            # Step 2: Check exemptions
            exemption_result = self._check_exemptions(amount, category, expense_type, classification)
            
            # Step 3: Calculate contribution if applicable
            contribution_result = self._calculate_contribution(
                amount, category, expense_type, employee_type, exemption_result
            )
            
            # Step 4: Determine compliance status
            compliance_status = self._determine_compliance_status(
                exemption_result, contribution_result, employee_type
            )
            
            # Step 5: Assess risk level
            risk_level = self._assess_risk_level(amount, compliance_status, contribution_result)
            
            # Step 6: Generate explanation and recommendations
            explanation = self._generate_explanation(
                classification, exemption_result, contribution_result, compliance_status
            )
            recommendations = self._generate_recommendations(
                compliance_status, exemption_result, contribution_result
            )
            
            return {
                "is_compliant": compliance_status == "compliant",
                "compliance_status": compliance_status,
                "risk_level": risk_level,
                "expense_classification": classification,
                "employee_classification": employee_type,
                "contribution_applicable": contribution_result["applicable"],
                "contribution_rate": contribution_result["rate"],
                "contribution_amount": contribution_result["amount"],
                "exemption_applicable": exemption_result["applicable"],
                "exemption_reason": exemption_result["reason"],
                "exemption_threshold_met": exemption_result["threshold_met"],
                "rule_applied": exemption_result.get("rule_name") or contribution_result.get("rule_name"),
                "explanation": explanation,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error("urssaf_evaluation_error", error=str(e), expense_data=expense_data)
            return {
                "is_compliant": False,
                "compliance_status": "requires_review",
                "risk_level": "high",
                "expense_classification": "unknown",
                "contribution_applicable": False,
                "contribution_rate": Decimal("0.0"),
                "contribution_amount": Decimal("0.0"),
                "exemption_applicable": False,
                "exemption_reason": f"Evaluation error: {str(e)}",
                "explanation": "Unable to evaluate URSSAF compliance due to error",
                "recommendations": ["Manual review required"]
            }
    
    def _classify_expense(
        self,
        category: str,
        expense_type: str,
        description: str
    ) -> str:
        """Classify expense type"""
        # Reimbursements are always exempt
        if expense_type == "reimbursement" or "reimbursement" in description:
            return "reimbursement"
        
        # Check category-based classification
        if "meal" in category or "restaurant" in category or "food" in category:
            return "meal"
        elif "transport" in category or "travel" in category:
            return "transport"
        elif "gift" in category or "present" in category:
            return "gift"
        elif "training" in category or "education" in category:
            return "training"
        elif "equipment" in category or "tool" in category:
            return "equipment"
        
        # Default to benefit if not specified
        return "benefit"
    
    def _check_exemptions(
        self,
        amount: Decimal,
        category: str,
        expense_type: str,
        classification: str
    ) -> Dict[str, Any]:
        """Check if expense is exempt from URSSAF contributions"""
        
        # Reimbursements are always exempt
        if expense_type == "reimbursement" or classification == "reimbursement":
            return {
                "applicable": True,
                "reason": "Reimbursement expenses are exempt from URSSAF contributions",
                "threshold_met": True,
                "rule_name": "reimbursement_exempt"
            }
        
        # Check threshold-based exemptions
        if classification == "meal":
            threshold = self.EXEMPTION_THRESHOLDS.get("meal", Decimal("5.55"))
            if amount <= threshold:
                return {
                    "applicable": True,
                    "reason": f"Meal expense below exemption threshold (€{threshold})",
                    "threshold_met": True,
                    "rule_name": "small_meal_exemption"
                }
        
        if classification == "gift":
            threshold = self.EXEMPTION_THRESHOLDS.get("gift", Decimal("73.00"))
            if amount <= threshold:
                return {
                    "applicable": True,
                    "reason": f"Gift expense below exemption threshold (€{threshold})",
                    "threshold_met": True,
                    "rule_name": "gift_exemption_threshold"
                }
        
        # Transport reimbursements are exempt
        if classification == "transport":
            return {
                "applicable": True,
                "reason": "Transport expenses are exempt from URSSAF contributions",
                "threshold_met": True,
                "rule_name": "transport_exempt"
            }
        
        # Training expenses are exempt
        if classification == "training":
            return {
                "applicable": True,
                "reason": "Training expenses are exempt from URSSAF contributions",
                "threshold_met": True,
                "rule_name": "training_exempt"
            }
        
        # Not exempt
        return {
            "applicable": False,
            "reason": "Expense does not qualify for exemption",
            "threshold_met": False,
            "rule_name": None
        }
    
    def _calculate_contribution(
        self,
        amount: Decimal,
        category: str,
        expense_type: str,
        employee_type: str,
        exemption_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate URSSAF contribution if applicable"""
        
        # If exempt, no contribution
        if exemption_result["applicable"]:
            return {
                "applicable": False,
                "rate": Decimal("0.0"),
                "amount": Decimal("0.0"),
                "rule_name": exemption_result.get("rule_name")
            }
        
        # Contractors and interns don't require employer contribution
        if employee_type in ["contractor", "intern"]:
            return {
                "applicable": False,
                "rate": Decimal("0.0"),
                "amount": Decimal("0.0"),
                "rule_name": f"{employee_type}_exempt",
                "reason": f"{employee_type.title()} expenses do not require employer URSSAF contribution"
            }
        
        # Get contribution rate based on expense type
        if expense_type == "benefit":
            rate = self.STANDARD_CONTRIBUTION_RATES.get("employee_benefit", Decimal("20.0"))
        elif category in ["equipment", "tool"]:
            rate = self.STANDARD_CONTRIBUTION_RATES.get("equipment", Decimal("20.0"))
        else:
            # Default rate for other benefits
            rate = Decimal("20.0")
        
        contribution_amount = (amount * rate) / Decimal("100.0")
        
        return {
            "applicable": True,
            "rate": rate,
            "amount": contribution_amount,
            "rule_name": "standard_contribution_rate"
        }
    
    def _determine_compliance_status(
        self,
        exemption_result: Dict[str, Any],
        contribution_result: Dict[str, Any],
        employee_type: str
    ) -> str:
        """Determine overall compliance status"""
        
        # If exempt, compliant
        if exemption_result["applicable"]:
            return "compliant"
        
        # If contribution calculated correctly, compliant
        if contribution_result["applicable"]:
            return "compliant"
        
        # If contractor/intern, compliant (no employer contribution)
        if employee_type in ["contractor", "intern"]:
            return "compliant"
        
        # Otherwise requires review
        return "requires_review"
    
    def _assess_risk_level(
        self,
        amount: Decimal,
        compliance_status: str,
        contribution_result: Dict[str, Any]
    ) -> str:
        """Assess risk level"""
        
        if compliance_status == "compliant":
            # High amounts with contributions are medium risk
            if contribution_result["applicable"] and amount > Decimal("1000.0"):
                return "medium"
            return "low"
        
        if compliance_status == "requires_review":
            # High amounts requiring review are high risk
            if amount > Decimal("500.0"):
                return "high"
            return "medium"
        
        return "medium"
    
    def _generate_explanation(
        self,
        classification: str,
        exemption_result: Dict[str, Any],
        contribution_result: Dict[str, Any],
        compliance_status: str
    ) -> str:
        """Generate human-readable explanation"""
        
        explanation_parts = []
        
        explanation_parts.append(f"Expense classified as: {classification}")
        
        if exemption_result["applicable"]:
            explanation_parts.append(f"Exemption: {exemption_result['reason']}")
        elif contribution_result["applicable"]:
            explanation_parts.append(
                f"URSSAF contribution applicable: {contribution_result['rate']}% "
                f"(€{contribution_result['amount']:.2f})"
            )
        else:
            explanation_parts.append("No URSSAF contribution required")
        
        explanation_parts.append(f"Compliance status: {compliance_status}")
        
        return ". ".join(explanation_parts) + "."
    
    def _generate_recommendations(
        self,
        compliance_status: str,
        exemption_result: Dict[str, Any],
        contribution_result: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations"""
        
        recommendations = []
        
        if compliance_status == "requires_review":
            recommendations.append("Manual review recommended for URSSAF compliance")
        
        if contribution_result["applicable"]:
            recommendations.append(
                f"Ensure URSSAF contribution of {contribution_result['rate']}% "
                f"(€{contribution_result['amount']:.2f}) is declared"
            )
        
        if not exemption_result["applicable"] and not contribution_result["applicable"]:
            recommendations.append("Verify expense classification is correct")
        
        return recommendations

