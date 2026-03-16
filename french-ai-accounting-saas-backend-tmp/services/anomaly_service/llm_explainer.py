# -----------------------------------------------------------------------------
# File: llm_explainer.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: LLM-based anomaly explanations
# -----------------------------------------------------------------------------

"""
LLM-based Anomaly Explanation Service
Provides explanations for anomalies using LLM
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from common.models import Expense, PolicyViolation, User
import structlog
import os

logger = structlog.get_logger()

class LLMAnomalyExplainer:
    """Generate LLM-based explanations for anomalies"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini")
        self.llm_api_key = os.getenv("GEMINI_API_KEY", "")
    
    async def explain_anomaly(
        self,
        expense_id: str,
        anomaly_score: float,
        risk_factors: Dict[str, float],
        is_anomaly: bool
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for an anomaly
        Returns explanations for behavioural patterns, VAT errors, and policy inconsistencies
        """
        try:
            # Get expense details
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.id == expense_id,
                        Expense.tenant_id == self.tenant_id
                    )
                )
            )
            expense = result.scalar_one_or_none()
            
            if not expense:
                raise ValueError(f"Expense {expense_id} not found")
            
            # Get user info
            user_result = await self.db.execute(
                select(User).where(User.id == expense.submitted_by)
            )
            user = user_result.scalar_one_or_none()
            
            # Get policy violations
            violation_result = await self.db.execute(
                select(PolicyViolation).where(
                    PolicyViolation.expense_id == expense_id
                )
            )
            violations = violation_result.scalars().all()
            
            # Generate explanations
            explanations = {
                "behavioural_patterns": await self._explain_behavioural_patterns(
                    expense, user, risk_factors
                ),
                "vat_errors": await self._explain_vat_errors(expense, risk_factors),
                "policy_inconsistencies": await self._explain_policy_inconsistencies(
                    expense, violations, risk_factors
                ),
                "summary": self._generate_summary(
                    expense, anomaly_score, risk_factors, is_anomaly
                )
            }
            
            return explanations
            
        except Exception as e:
            logger.error("anomaly_explanation_error", expense_id=expense_id, error=str(e))
            return {
                "error": str(e),
                "behavioural_patterns": {},
                "vat_errors": {},
                "policy_inconsistencies": {},
                "summary": "Failed to generate explanation"
            }
    
    async def _explain_behavioural_patterns(
        self,
        expense: Expense,
        user: Optional[User],
        risk_factors: Dict[str, float]
    ) -> Dict[str, Any]:
        """Explain behavioural pattern anomalies"""
        patterns = []
        severity = "low"
        
        # Check employee risk
        if risk_factors.get("employee_risk", 0) > 0.5:
            patterns.append({
                "type": "high_employee_risk",
                "description": f"Employee {user.email if user else 'Unknown'} has a history of policy violations or high-risk expenses",
                "severity": "high",
                "risk_score": risk_factors.get("employee_risk", 0)
            })
            severity = "high"
        
        # Check frequency risk
        if risk_factors.get("frequency_risk", 0) > 0.5:
            patterns.append({
                "type": "unusual_frequency",
                "description": "Unusually high number of expenses in a short time period",
                "severity": "medium",
                "risk_score": risk_factors.get("frequency_risk", 0)
            })
            if severity == "low":
                severity = "medium"
        
        # Check category risk
        if risk_factors.get("category_risk", 0) > 0.4:
            patterns.append({
                "type": "unusual_category",
                "description": f"Expense category '{expense.category}' is unusual for this employee",
                "severity": "medium",
                "risk_score": risk_factors.get("category_risk", 0)
            })
            if severity == "low":
                severity = "medium"
        
        # Check merchant risk
        if risk_factors.get("merchant_risk", 0) > 0.5:
            patterns.append({
                "type": "unusual_merchant",
                "description": f"Merchant '{expense.merchant_name}' is rarely used by other employees",
                "severity": "medium",
                "risk_score": risk_factors.get("merchant_risk", 0)
            })
            if severity == "low":
                severity = "medium"
        
        # Check time-based patterns
        if risk_factors.get("time_risk", 0) > 0.3:
            expense_date = expense.expense_date
            time_issues = []
            if expense_date.weekday() >= 5:
                time_issues.append("weekend")
            if expense_date.day >= 25:
                time_issues.append("month-end")
            
            if time_issues:
                patterns.append({
                    "type": "unusual_timing",
                    "description": f"Expense occurred during unusual time: {', '.join(time_issues)}",
                    "severity": "low",
                    "risk_score": risk_factors.get("time_risk", 0)
                })
        
        return {
            "patterns": patterns,
            "severity": severity,
            "count": len(patterns)
        }
    
    async def _explain_vat_errors(
        self,
        expense: Expense,
        risk_factors: Dict[str, float]
    ) -> Dict[str, Any]:
        """Explain VAT-related errors"""
        errors = []
        severity = "low"
        
        # Check if VAT is missing when it should be present
        if expense.merchant_name and not expense.vat_amount:
            # Check if merchant typically has VAT
            # This is simplified - in production, check merchant database
            errors.append({
                "type": "missing_vat",
                "description": "VAT amount is missing but may be required for this merchant type",
                "severity": "medium",
                "suggestion": "Verify if VAT should be included for this expense"
            })
            severity = "medium"
        
        # Check VAT rate consistency
        if expense.vat_rate and expense.vat_amount:
            expected_vat = float(expense.amount) * (float(expense.vat_rate) / 100)
            actual_vat = float(expense.vat_amount)
            difference = abs(expected_vat - actual_vat)
            
            if difference > 0.01:  # More than 1 cent difference
                errors.append({
                    "type": "vat_calculation_error",
                    "description": f"VAT amount ({actual_vat:.2f}) doesn't match expected calculation ({expected_vat:.2f}) based on VAT rate ({expense.vat_rate}%)",
                    "severity": "high",
                    "difference": difference,
                    "suggestion": "Recalculate VAT amount or verify VAT rate"
                })
                severity = "high"
        
        # Check for unusual VAT rates
        if expense.vat_rate:
            vat_rate = float(expense.vat_rate)
            # Standard French VAT rates: 20%, 10%, 5.5%, 2.1%
            standard_rates = [20.0, 10.0, 5.5, 2.1]
            if vat_rate not in standard_rates and vat_rate > 0:
                errors.append({
                    "type": "unusual_vat_rate",
                    "description": f"VAT rate ({vat_rate}%) is not a standard French VAT rate",
                    "severity": "medium",
                    "suggestion": "Verify if this VAT rate is correct for this expense type"
                })
                if severity == "low":
                    severity = "medium"
        
        return {
            "errors": errors,
            "severity": severity,
            "count": len(errors)
        }
    
    async def _explain_policy_inconsistencies(
        self,
        expense: Expense,
        violations: List[PolicyViolation],
        risk_factors: Dict[str, float]
    ) -> Dict[str, Any]:
        """Explain policy inconsistencies"""
        inconsistencies = []
        severity = "low"
        
        # Check violation risk
        violation_risk = risk_factors.get("violation_risk", 0)
        if violation_risk > 0:
            inconsistencies.append({
                "type": "policy_violations",
                "description": f"Expense has {len(violations)} policy violation(s)",
                "severity": "high" if violation_risk > 0.6 else "medium",
                "violations": [
                    {
                        "type": viol.violation_type,
                        "severity": viol.violation_severity,
                        "message": viol.violation_message
                    }
                    for viol in violations
                ],
                "count": len(violations)
            })
            severity = "high" if violation_risk > 0.6 else "medium"
        
        # Check amount against policy limits
        if risk_factors.get("amount_risk", 0) > 0.5:
            inconsistencies.append({
                "type": "amount_exceeds_pattern",
                "description": f"Expense amount ({expense.amount} {expense.currency}) is significantly higher than employee's average",
                "severity": "medium",
                "risk_score": risk_factors.get("amount_risk", 0),
                "suggestion": "Verify if this amount is within policy limits"
            })
            if severity == "low":
                severity = "medium"
        
        return {
            "inconsistencies": inconsistencies,
            "severity": severity,
            "count": len(inconsistencies)
        }
    
    def _generate_summary(
        self,
        expense: Expense,
        anomaly_score: float,
        risk_factors: Dict[str, float],
        is_anomaly: bool
    ) -> str:
        """Generate summary explanation"""
        if not is_anomaly and max(risk_factors.values()) < 0.4:
            return "This expense appears normal with no significant anomalies detected."
        
        top_risks = sorted(
            risk_factors.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        risk_descriptions = []
        for factor, score in top_risks:
            if score > 0.3:
                factor_name = factor.replace("_", " ").title()
                risk_descriptions.append(f"{factor_name} ({(score * 100):.1f}%)")
        
        if is_anomaly:
            return f"This expense has been flagged as an anomaly (score: {(anomaly_score * 100):.1f}%). " \
                   f"Primary risk factors: {', '.join(risk_descriptions)}. " \
                   f"Please review the detailed explanations below."
        else:
            return f"This expense shows elevated risk indicators. " \
                   f"Primary concerns: {', '.join(risk_descriptions)}. " \
                   f"Review recommended."




