# -----------------------------------------------------------------------------
# File: report_generator.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Basic Audit Report Generator
# -----------------------------------------------------------------------------

"""
Basic Audit Report Generator
Generates reports with spend summary, policy violations, and VAT summary
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from common.models import Expense, PolicyViolation, User
from decimal import Decimal
import structlog

logger = structlog.get_logger()

class AuditReportGenerator:
    """Generate basic audit reports"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def generate_report(
        self,
        period_start: date,
        period_end: date,
        expense_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        try:
            # Build query
            query = select(Expense).where(
                and_(
                    Expense.tenant_id == self.tenant_id,
                    Expense.expense_date >= period_start,
                    Expense.expense_date <= period_end,
                    Expense.deleted_at.is_(None)
                )
            )
            
            if expense_ids:
                query = query.where(Expense.id.in_(expense_ids))
            
            result = await self.db.execute(query)
            expenses = result.scalars().all()
            
            # Generate sections
            spend_summary = await self._generate_spend_summary(expenses)
            policy_violations = await self._generate_policy_violations(expenses)
            vat_summary = await self._generate_vat_summary(expenses)
            top_risks = await self._generate_top_risks(expenses)
            executive_summary = self._build_executive_summary(
                spend_summary, policy_violations, vat_summary, top_risks
            )
            
            return {
                "report_period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "generated_at": datetime.utcnow().isoformat(),
                "total_expenses": len(expenses),
                "executive_summary": executive_summary,
                "spend_summary": spend_summary,
                "policy_violations": policy_violations,
                "vat_summary": vat_summary,
                "top_risk_employees": top_risks.get("employees", []),
                "top_risk_merchants": top_risks.get("merchants", []),
            }
            
        except Exception as e:
            logger.error("generate_report_error", error=str(e))
            raise
    
    async def _generate_spend_summary(
        self,
        expenses: List[Expense]
    ) -> Dict[str, Any]:
        """Generate spend summary section"""
        try:
            if not expenses:
                return {
                    "total_amount": 0.0,
                    "total_count": 0,
                    "by_category": {},
                    "by_merchant": {},
                    "by_employee": {},
                    "by_status": {},
                    "by_month": {},
                    "average_amount": 0.0,
                    "min_amount": 0.0,
                    "max_amount": 0.0
                }
            
            amounts = [float(exp.amount) for exp in expenses]
            total_amount = sum(amounts)
            
            # Group by category
            by_category = {}
            for exp in expenses:
                category = exp.category or "Uncategorized"
                if category not in by_category:
                    by_category[category] = {"count": 0, "total": 0.0}
                by_category[category]["count"] += 1
                by_category[category]["total"] += float(exp.amount)
            
            # Group by merchant
            by_merchant = {}
            for exp in expenses:
                merchant = exp.merchant_name or "Unknown"
                if merchant not in by_merchant:
                    by_merchant[merchant] = {"count": 0, "total": 0.0}
                by_merchant[merchant]["count"] += 1
                by_merchant[merchant]["total"] += float(exp.amount)
            
            # Group by employee
            by_employee = {}
            employee_ids = set(str(exp.submitted_by) for exp in expenses)
            
            for emp_id in employee_ids:
                emp_expenses = [exp for exp in expenses if str(exp.submitted_by) == emp_id]
                if emp_expenses:
                    # Get employee info
                    emp_result = await self.db.execute(
                        select(User).where(User.id == emp_id)
                    )
                    emp = emp_result.scalar_one_or_none()
                    
                    by_employee[emp_id] = {
                        "count": len(emp_expenses),
                        "total": sum(float(exp.amount) for exp in emp_expenses),
                        "email": emp.email if emp else "Unknown",
                        "name": f"{emp.first_name} {emp.last_name}".strip() if emp else "Unknown"
                    }
            
            # Group by status
            by_status = {}
            for exp in expenses:
                status = exp.approval_status or exp.status
                if status not in by_status:
                    by_status[status] = {"count": 0, "total": 0.0}
                by_status[status]["count"] += 1
                by_status[status]["total"] += float(exp.amount)
            
            # Group by month
            by_month = {}
            for exp in expenses:
                if exp.expense_date:
                    month_key = exp.expense_date.strftime("%Y-%m")
                    if month_key not in by_month:
                        by_month[month_key] = {"count": 0, "total": 0.0}
                    by_month[month_key]["count"] += 1
                    by_month[month_key]["total"] += float(exp.amount)
            
            return {
                "total_amount": total_amount,
                "total_count": len(expenses),
                "by_category": by_category,
                "by_merchant": by_merchant,
                "by_employee": by_employee,
                "by_status": by_status,
                "by_month": by_month,
                "average_amount": total_amount / len(expenses) if expenses else 0.0,
                "min_amount": min(amounts) if amounts else 0.0,
                "max_amount": max(amounts) if amounts else 0.0
            }
            
        except Exception as e:
            logger.error("generate_spend_summary_error", error=str(e))
            return {}
    
    async def _generate_policy_violations(
        self,
        expenses: List[Expense]
    ) -> Dict[str, Any]:
        """Generate policy violations summary"""
        try:
            expense_ids = [exp.id for exp in expenses]
            
            if not expense_ids:
                return {
                    "total_violations": 0,
                    "by_severity": {},
                    "by_type": {},
                    "by_employee": {},
                    "violations": []
                }
            
            # Get violations
            result = await self.db.execute(
                select(PolicyViolation).join(
                    Expense, PolicyViolation.expense_id == Expense.id
                ).where(
                    Expense.id.in_(expense_ids)
                )
            )
            violations = result.scalars().all()
            
            # Group by severity
            by_severity = {}
            for viol in violations:
                severity = viol.violation_severity
                if severity not in by_severity:
                    by_severity[severity] = 0
                by_severity[severity] += 1
            
            # Group by type
            by_type = {}
            for viol in violations:
                v_type = viol.violation_type
                if v_type not in by_type:
                    by_type[v_type] = 0
                by_type[v_type] += 1
            
            # Group by employee
            by_employee = {}
            for viol in violations:
                # Get expense to find employee
                exp_result = await self.db.execute(
                    select(Expense).where(Expense.id == viol.expense_id)
                )
                exp = exp_result.scalar_one_or_none()
                
                if exp:
                    emp_id = str(exp.submitted_by)
                    if emp_id not in by_employee:
                        emp_result = await self.db.execute(
                            select(User).where(User.id == emp_id)
                        )
                        emp = emp_result.scalar_one_or_none()
                        by_employee[emp_id] = {
                            "count": 0,
                            "email": emp.email if emp else "Unknown",
                            "name": f"{emp.first_name} {emp.last_name}".strip() if emp else "Unknown"
                        }
                    by_employee[emp_id]["count"] += 1
            
            # Detailed violations list
            violations_list = []
            for viol in violations[:100]:  # Limit to 100 for report
                exp_result = await self.db.execute(
                    select(Expense).where(Expense.id == viol.expense_id)
                )
                exp = exp_result.scalar_one_or_none()
                
                violations_list.append({
                    "id": str(viol.id),
                    "expense_id": str(viol.expense_id),
                    "violation_type": viol.violation_type,
                    "severity": viol.violation_severity,
                    "message": viol.violation_message,
                    "is_resolved": viol.is_resolved,
                    "expense_amount": float(exp.amount) if exp else None,
                    "expense_date": exp.expense_date.isoformat() if exp and exp.expense_date else None
                })
            
            return {
                "total_violations": len(violations),
                "by_severity": by_severity,
                "by_type": by_type,
                "by_employee": by_employee,
                "violations": violations_list
            }
            
        except Exception as e:
            logger.error("generate_policy_violations_error", error=str(e))
            return {}
    
    async def _generate_vat_summary(
        self,
        expenses: List[Expense]
    ) -> Dict[str, Any]:
        """Generate VAT summary"""
        try:
            if not expenses:
                return {
                    "total_vat_amount": 0.0,
                    "total_vatable_amount": 0.0,
                    "by_rate": {},
                    "by_category": {},
                    "vat_compliance": {
                        "expenses_with_vat": 0,
                        "expenses_without_vat": 0,
                        "missing_vat_count": 0
                    }
                }
            
            total_vat = 0.0
            total_vatable = 0.0
            expenses_with_vat = 0
            expenses_without_vat = 0
            missing_vat_count = 0
            
            # Group by VAT rate
            by_rate = {}
            by_category = {}
            
            for exp in expenses:
                amount = float(exp.amount)
                vat_rate = float(exp.vat_rate) if exp.vat_rate else None
                vat_amount = float(exp.vat_amount) if exp.vat_amount else None
                
                if vat_rate and vat_rate > 0:
                    expenses_with_vat += 1
                    total_vat += vat_amount or 0.0
                    total_vatable += amount
                    
                    rate_key = f"{vat_rate}%"
                    if rate_key not in by_rate:
                        by_rate[rate_key] = {
                            "count": 0,
                            "total_amount": 0.0,
                            "total_vat": 0.0
                        }
                    by_rate[rate_key]["count"] += 1
                    by_rate[rate_key]["total_amount"] += amount
                    by_rate[rate_key]["total_vat"] += (vat_amount or 0.0)
                else:
                    expenses_without_vat += 1
                    # Check if VAT should have been present (French VAT rules)
                    if amount > 0:  # Simplified check
                        missing_vat_count += 1
                
                # Group by category
                category = exp.category or "Uncategorized"
                if category not in by_category:
                    by_category[category] = {
                        "count": 0,
                        "total_amount": 0.0,
                        "total_vat": 0.0
                    }
                by_category[category]["count"] += 1
                by_category[category]["total_amount"] += amount
                by_category[category]["total_vat"] += (vat_amount or 0.0)
            
            return {
                "total_vat_amount": total_vat,
                "total_vatable_amount": total_vatable,
                "by_rate": by_rate,
                "by_category": by_category,
                "vat_compliance": {
                    "expenses_with_vat": expenses_with_vat,
                    "expenses_without_vat": expenses_without_vat,
                    "missing_vat_count": missing_vat_count,
                    "compliance_rate": (expenses_with_vat / len(expenses) * 100) if expenses else 0.0
                }
            }
            
        except Exception as e:
            logger.error("generate_vat_summary_error", error=str(e))
            return {}

    async def _generate_top_risks(
        self,
        expenses: List[Expense],
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Top risk employees and merchants from expense risk_score_line (5.2.3)."""
        try:
            from common.models import User
            emp_risk: Dict[str, Dict[str, Any]] = {}
            merch_risk: Dict[str, Dict[str, Any]] = {}
            for exp in expenses:
                rs = float(exp.risk_score_line) if getattr(exp, "risk_score_line", None) is not None else 0.0
                emp_id = str(exp.submitted_by)
                if emp_id not in emp_risk:
                    emp_risk[emp_id] = {"user_id": emp_id, "total_risk": 0.0, "count": 0, "total_amount": 0.0}
                emp_risk[emp_id]["total_risk"] += rs
                emp_risk[emp_id]["count"] += 1
                emp_risk[emp_id]["total_amount"] += float(exp.amount)
                merchant = (exp.merchant_name or "").strip() or "_unknown_"
                if merchant not in merch_risk:
                    merch_risk[merchant] = {"merchant_name": merchant, "total_risk": 0.0, "count": 0, "total_amount": 0.0}
                merch_risk[merchant]["total_risk"] += rs
                merch_risk[merchant]["count"] += 1
                merch_risk[merchant]["total_amount"] += float(exp.amount)
            employees = []
            for emp_id, d in emp_risk.items():
                avg = d["total_risk"] / d["count"] if d["count"] else 0
                emp_result = await self.db.execute(select(User).where(User.id == emp_id))
                u = emp_result.scalar_one_or_none()
                employees.append({
                    "user_id": emp_id,
                    "email": u.email if u else "Unknown",
                    "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or "Unknown",
                    "avg_risk_score": round(avg, 4),
                    "expense_count": d["count"],
                    "total_amount": d["total_amount"],
                })
            employees.sort(key=lambda x: x["avg_risk_score"], reverse=True)
            merchants = []
            for name, d in merch_risk.items():
                if name == "_unknown_":
                    continue
                avg = d["total_risk"] / d["count"] if d["count"] else 0
                merchants.append({
                    "merchant_name": name,
                    "avg_risk_score": round(avg, 4),
                    "expense_count": d["count"],
                    "total_amount": d["total_amount"],
                })
            merchants.sort(key=lambda x: x["avg_risk_score"], reverse=True)
            return {"employees": employees[:limit], "merchants": merchants[:limit]}
        except Exception as e:
            logger.error("generate_top_risks_error", error=str(e))
            return {"employees": [], "merchants": []}

    def _build_executive_summary(
        self,
        spend_summary: Dict[str, Any],
        policy_violations: Dict[str, Any],
        vat_summary: Dict[str, Any],
        top_risks: Dict[str, Any],
    ) -> str:
        """Build a short executive summary (5.2.3)."""
        total = spend_summary.get("total_amount", 0) or 0
        count = spend_summary.get("total_count", 0) or 0
        viol = policy_violations.get("total_violations", 0) or 0
        vat = vat_summary.get("vat_compliance", {})
        missing_vat = vat.get("missing_vat_count", 0) or 0
        top_emp = len(top_risks.get("employees", []))
        top_merch = len(top_risks.get("merchants", []))
        return (
            f"Total spend: {total:.2f} EUR across {count} expenses. "
            f"Policy violations: {viol}. VAT exceptions (missing where expected): {missing_vat}. "
            f"Top risk employees: {top_emp}, top risk merchants: {top_merch}."
        )