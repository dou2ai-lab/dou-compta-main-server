# -----------------------------------------------------------------------------
# File: evaluator.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Policy evaluation engine for expense validation
# -----------------------------------------------------------------------------

"""
Policy Evaluation Engine
Evaluates expenses against configured policies
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import structlog

from common.models import Expense, User
from services.admin.models import ExpensePolicy
from .models import (
    PolicyEvaluationRequest, PolicyEvaluationResponse,
    PolicyViolationResponse, ViolationType, ViolationSeverity
)

logger = structlog.get_logger()

class PolicyEvaluator:
    """Policy evaluation engine"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def evaluate_expense(
        self,
        request: PolicyEvaluationRequest
    ) -> PolicyEvaluationResponse:
        """
        Evaluate an expense against all applicable policies
        
        Args:
            request: Policy evaluation request with expense details
            
        Returns:
            PolicyEvaluationResponse with violations and recommendations
        """
        violations = []
        
        try:
            # Get all active policies for the tenant
            policies = await self._get_applicable_policies(
                tenant_id=request.tenant_id,
                user_roles=request.user_roles
            )
            
            logger.info(
                "policy_evaluation_started",
                expense_id=str(request.expense_id),
                policy_count=len(policies),
                expense_amount=str(request.amount),
                expense_category=request.category or "",
            )
            
            # Evaluate against each policy
            for policy in policies:
                policy_violations = await self._evaluate_policy(
                    policy=policy,
                    request=request
                )
                logger.info(
                    "policy_evaluated",
                    expense_id=str(request.expense_id),
                    policy_id=str(policy.id),
                    policy_type=policy.policy_type,
                    policy_rules=policy.policy_rules,
                    violations_from_policy=len(policy_violations),
                )
                violations.extend(policy_violations)
            
            # Calculate summary
            error_count = sum(1 for v in violations if v.violation_severity == ViolationSeverity.ERROR)
            warning_count = sum(1 for v in violations if v.violation_severity == ViolationSeverity.WARNING)
            requires_comment = any(v.requires_comment for v in violations)
            can_submit = error_count == 0  # Can only submit if no errors
            
            logger.info(
                "policy_evaluation_completed",
                expense_id=str(request.expense_id),
                violation_count=len(violations),
                error_count=error_count,
                warning_count=warning_count
            )
            
            return PolicyEvaluationResponse(
                has_violations=len(violations) > 0,
                violations=violations,
                can_submit=can_submit,
                requires_comment=requires_comment,
                total_violations=len(violations),
                warning_count=warning_count,
                error_count=error_count
            )
            
        except Exception as e:
            logger.error("policy_evaluation_failed", error=str(e), exc_info=True)
            # Return empty response on error - don't block expense creation
            return PolicyEvaluationResponse(
                has_violations=False,
                violations=[],
                can_submit=True,
                requires_comment=False
            )
    
    async def _get_applicable_policies(
        self,
        tenant_id: str,
        user_roles: List[str]
    ) -> List[ExpensePolicy]:
        """Get all active policies applicable to the user"""
        from uuid import UUID
        
        try:
            # Convert tenant_id to UUID if it's a string
            if isinstance(tenant_id, str):
                tenant_uuid = UUID(tenant_id)
            else:
                tenant_uuid = tenant_id
            
            now = datetime.utcnow()
            
            query = select(ExpensePolicy).where(
                ExpensePolicy.tenant_id == tenant_uuid,
                ExpensePolicy.is_active == True,
                ExpensePolicy.deleted_at.is_(None),
                or_(
                    ExpensePolicy.effective_from.is_(None),
                    ExpensePolicy.effective_from <= now
                ),
                or_(
                    ExpensePolicy.effective_until.is_(None),
                    ExpensePolicy.effective_until >= now
                )
            )
            
            result = await self.db.execute(query)
            all_policies = result.scalars().all()
        except Exception as e:
            logger.warning("failed_to_load_policies", error=str(e), tenant_id=str(tenant_id))
            return []
        
        # Filter by role if policy has role restrictions
        applicable_policies = []
        for policy in all_policies:
            applies_to_roles = policy.applies_to_roles or []
            if not applies_to_roles or any(role in user_roles for role in applies_to_roles):
                applicable_policies.append(policy)
        
        return applicable_policies
    
    async def _evaluate_policy(
        self,
        policy: ExpensePolicy,
        request: PolicyEvaluationRequest
    ) -> List[PolicyViolationResponse]:
        """Evaluate expense against a specific policy"""
        violations = []
        rules = policy.policy_rules or {}
        policy_type = policy.policy_type
        
        try:
            if policy_type == "amount_limit":
                violation = self._check_amount_limit(policy, rules, request)
                if violation:
                    violations.append(violation)
            
            elif policy_type == "category_limit":
                violation = self._check_category_limit(policy, rules, request)
                if violation:
                    violations.append(violation)
            
            elif policy_type == "meal_cap":
                violation = self._check_meal_cap(policy, rules, request)
                if violation:
                    violations.append(violation)
            
            elif policy_type == "hotel_cap":
                violation = self._check_hotel_cap(policy, rules, request)
                if violation:
                    violations.append(violation)
            
            elif policy_type == "mileage_rate":
                violation = self._check_mileage_rate(policy, rules, request)
                if violation:
                    violations.append(violation)
            
            elif policy_type == "required_fields":
                violation = self._check_required_fields(policy, rules, request)
                if violation:
                    violations.append(violation)
            
            elif policy_type == "category_restriction":
                violation = self._check_category_restriction(policy, rules, request)
                if violation:
                    violations.append(violation)
            
        except Exception as e:
            logger.error(
                "policy_evaluation_error",
                policy_id=str(policy.id),
                error=str(e),
                exc_info=True
            )
        
        return violations
    
    def _check_amount_limit(
        self,
        policy: ExpensePolicy,
        rules: Dict[str, Any],
        request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolationResponse]:
        """Check if expense amount exceeds policy limit"""
        max_amount = rules.get("max_amount")
        if max_amount is None:
            return None
        
        max_amount_decimal = Decimal(str(max_amount))
        expense_amount = Decimal(str(request.amount))
        if expense_amount > max_amount_decimal:
            severity = ViolationSeverity.ERROR if rules.get("block_on_exceed", True) else ViolationSeverity.WARNING
            return PolicyViolationResponse(
                policy_id=policy.id,
                violation_type=ViolationType.AMOUNT_EXCEEDED,
                violation_severity=severity,
                violation_message=f"Expense amount {expense_amount} {request.currency} exceeds policy limit of {max_amount_decimal} {request.currency}",
                policy_rule=rules,
                requires_comment=rules.get("requires_comment_on_exceed", False)
            )
        return None
    
    def _check_category_limit(
        self,
        policy: ExpensePolicy,
        rules: Dict[str, Any],
        request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolationResponse]:
        """Check if expense exceeds category-specific limit"""
        if not request.category:
            return None
        
        category_limits = rules.get("category_limits", {})
        category_limit = category_limits.get(request.category)
        
        if category_limit:
            max_amount = Decimal(str(category_limit.get("max_amount", 0)))
            if request.amount > max_amount:
                severity = ViolationSeverity.ERROR if category_limit.get("block_on_exceed", True) else ViolationSeverity.WARNING
                return PolicyViolationResponse(
                    policy_id=policy.id,
                    violation_type=ViolationType.AMOUNT_EXCEEDED,
                    violation_severity=severity,
                    violation_message=f"Expense amount {request.amount} {request.currency} exceeds {request.category} category limit of {max_amount} {request.currency}",
                    policy_rule=rules,
                    requires_comment=category_limit.get("requires_comment", False)
                )
        return None
    
    def _check_meal_cap(
        self,
        policy: ExpensePolicy,
        rules: Dict[str, Any],
        request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolationResponse]:
        """Check French meal cap limits"""
        # French meal caps: Breakfast 19 EUR, Lunch 25 EUR, Dinner 25 EUR
        if not request.category or "meal" not in request.category.lower():
            return None
        
        meal_type = rules.get("meal_type", "lunch").lower()
        caps = {
            "breakfast": Decimal("19.00"),
            "lunch": Decimal("25.00"),
            "dinner": Decimal("25.00"),
            "default": Decimal("25.00")
        }
        
        cap = Decimal(str(rules.get("max_amount", caps.get(meal_type, caps["default"]))))
        
        if request.amount > cap:
            severity = ViolationSeverity.WARNING  # Meal caps are typically warnings
            return PolicyViolationResponse(
                policy_id=policy.id,
                violation_type=ViolationType.MEAL_CAP_EXCEEDED,
                violation_severity=severity,
                violation_message=f"Meal expense {request.amount} {request.currency} exceeds French tax-free meal cap of {cap} {request.currency} for {meal_type}. Amount above cap may be taxable.",
                policy_rule=rules,
                requires_comment=True
            )
        return None
    
    def _check_hotel_cap(
        self,
        policy: ExpensePolicy,
        rules: Dict[str, Any],
        request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolationResponse]:
        """Check hotel accommodation caps"""
        if not request.category or "hotel" not in request.category.lower() and "accommodation" not in request.category.lower():
            return None
        
        max_amount = Decimal(str(rules.get("max_amount", "200.00")))  # Default 200 EUR per night
        
        if request.amount > max_amount:
            severity = ViolationSeverity.WARNING if rules.get("allow_with_approval", True) else ViolationSeverity.ERROR
            return PolicyViolationResponse(
                policy_id=policy.id,
                violation_type=ViolationType.HOTEL_CAP_EXCEEDED,
                violation_severity=severity,
                violation_message=f"Hotel expense {request.amount} {request.currency} exceeds policy limit of {max_amount} {request.currency} per night. Approval may be required.",
                policy_rule=rules,
                requires_comment=True
            )
        return None
    
    def _check_mileage_rate(
        self,
        policy: ExpensePolicy,
        rules: Dict[str, Any],
        request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolationResponse]:
        """Check mileage reimbursement rates"""
        if not request.category or "mileage" not in request.category.lower() and "travel" not in request.category.lower():
            return None
        
        # French mileage rates (example: 0.629 EUR/km for cars)
        standard_rate = Decimal(str(rules.get("rate_per_km", "0.629")))
        
        # If description contains distance, validate
        # This is a simplified check - in production, extract distance from description or separate field
        if request.description:
            # Try to extract distance from description (e.g., "150 km")
            import re
            km_match = re.search(r'(\d+)\s*km', request.description.lower())
            if km_match:
                distance = Decimal(km_match.group(1))
                expected_amount = distance * standard_rate
                tolerance = Decimal("0.10")  # 10 cent tolerance
                
                if abs(request.amount - expected_amount) > tolerance:
                    return PolicyViolationResponse(
                        policy_id=policy.id,
                        violation_type=ViolationType.MILEAGE_INVALID,
                        violation_severity=ViolationSeverity.WARNING,
                        violation_message=f"Mileage expense amount {request.amount} {request.currency} does not match expected rate of {standard_rate} {request.currency}/km for {distance} km (expected: {expected_amount} {request.currency})",
                        policy_rule=rules,
                        requires_comment=True
                    )
        return None
    
    def _check_required_fields(
        self,
        policy: ExpensePolicy,
        rules: Dict[str, Any],
        request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolationResponse]:
        """Check if required fields are present"""
        required_fields = rules.get("required_fields", [])
        missing_fields = []
        
        field_map = {
            "description": request.description,
            "merchant_name": request.merchant_name,
            "category": request.category,
            "receipt": None  # Would need to check receipt_ids separately
        }
        
        for field in required_fields:
            if field in field_map and not field_map[field]:
                missing_fields.append(field)
        
        if missing_fields:
            return PolicyViolationResponse(
                policy_id=policy.id,
                violation_type=ViolationType.MISSING_REQUIRED_FIELD,
                violation_severity=ViolationSeverity.ERROR,
                violation_message=f"Required fields are missing: {', '.join(missing_fields)}",
                policy_rule=rules,
                requires_comment=False
            )
        return None
    
    def _check_category_restriction(
        self,
        policy: ExpensePolicy,
        rules: Dict[str, Any],
        request: PolicyEvaluationRequest
    ) -> Optional[PolicyViolationResponse]:
        """Check if category is restricted"""
        if not request.category:
            return None
        
        restricted_categories = rules.get("restricted_categories", [])
        if request.category in restricted_categories:
            return PolicyViolationResponse(
                policy_id=policy.id,
                violation_type=ViolationType.CATEGORY_RESTRICTED,
                violation_severity=ViolationSeverity.ERROR,
                violation_message=f"Category '{request.category}' is restricted by policy. Please use an allowed category.",
                policy_rule=rules,
                requires_comment=False
            )
        return None

