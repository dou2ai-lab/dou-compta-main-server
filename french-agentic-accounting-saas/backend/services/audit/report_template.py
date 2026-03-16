# -----------------------------------------------------------------------------
# File: report_template.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Audit report template generator
# -----------------------------------------------------------------------------

"""
Audit Report Template Generator
Creates technical and narrative report structures
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from common.models import Expense, User, PolicyViolation
from .models import AuditReport, AuditScope
import structlog

logger = structlog.get_logger()

class AuditReportTemplate:
    """Generate audit report templates"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
    
    async def create_report_template(
        self,
        title: str,
        period_start: date,
        period_end: date,
        created_by: str,
        period_type: str = "custom",
        report_type: str = "combined"
    ) -> Dict[str, Any]:
        """Create a new audit report template"""
        
        # Generate report number
        report_number = await self._generate_report_number(period_start, period_end)
        
        # Get scope statistics
        scope_stats = await self._calculate_scope_statistics(period_start, period_end)
        
        # Build template structure
        template = {
            "report_number": report_number,
            "title": title,
            "description": f"Audit report for period {period_start} to {period_end}",
            "audit_period_start": period_start.isoformat(),
            "audit_period_end": period_end.isoformat(),
            "period_type": period_type,
            "report_type": report_type,
            "template_version": "1.0",
            "status": "draft",
            "scope_statistics": scope_stats,
            "technical_data": self._get_technical_template(),
            "narrative_sections": self._get_narrative_template(),
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "created_by": created_by
            }
        }
        
        return template
    
    def _get_technical_template(self) -> Dict[str, Any]:
        """Get technical report structure template"""
        return {
            "executive_summary": {
                "total_expenses": 0,
                "total_amount": 0.0,
                "sample_size": 0,
                "anomalies_detected": 0,
                "policy_violations": 0,
                "high_risk_items": 0
            },
            "scope": {
                "period": {},
                "criteria": [],
                "exclusions": []
            },
            "methodology": {
                "sampling_method": "",
                "risk_assessment_approach": "",
                "evidence_collection_method": ""
            },
            "findings": {
                "anomalies": [],
                "policy_violations": [],
                "compliance_issues": [],
                "risk_items": []
            },
            "statistics": {
                "by_category": {},
                "by_merchant": {},
                "by_employee": {},
                "by_status": {}
            },
            "recommendations": []
        }
    
    def _get_narrative_template(self) -> Dict[str, Any]:
        """Get narrative report structure template"""
        return {
            "introduction": {
                "purpose": "",
                "scope": "",
                "methodology": "",
                "period_covered": ""
            },
            "executive_summary": {
                "overview": "",
                "key_findings": [],
                "risk_assessment": "",
                "recommendations_summary": ""
            },
            "detailed_findings": {
                "anomalies": [],
                "policy_compliance": "",
                "process_observations": [],
                "control_effectiveness": ""
            },
            "conclusions": {
                "overall_assessment": "",
                "risk_level": "",
                "compliance_status": ""
            },
            "appendices": {
                "sample_details": [],
                "evidence_references": [],
                "supporting_documents": []
            }
        }
    
    async def _generate_report_number(self, period_start: date, period_end: date) -> str:
        """Generate unique report number"""
        year = period_start.year
        month = period_start.month
        
        # Format: AUD-YYYY-MM-XXX
        base_number = f"AUD-{year}-{month:02d}"
        
        # Check for existing reports with same base
        result = await self.db.execute(
            select(func.count(AuditReport.id)).where(
                and_(
                    AuditReport.tenant_id == self.tenant_id,
                    AuditReport.report_number.like(f"{base_number}%"),
                    AuditReport.deleted_at.is_(None)
                )
            )
        )
        count = result.scalar() or 0
        
        return f"{base_number}-{count + 1:03d}"
    
    async def _calculate_scope_statistics(
        self,
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """Calculate statistics for the audit scope"""
        try:
            result = await self.db.execute(
                select(
                    func.count(Expense.id).label('count'),
                    func.sum(Expense.amount).label('total_amount'),
                    func.count(func.distinct(Expense.submitted_by)).label('unique_employees'),
                    func.count(func.distinct(Expense.merchant_name)).label('unique_merchants')
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= period_start,
                        Expense.expense_date <= period_end,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            stats = result.one()
            
            return {
                "total_expenses": stats.count or 0,
                "total_amount": float(stats.total_amount or 0),
                "unique_employees": stats.unique_employees or 0,
                "unique_merchants": stats.unique_merchants or 0,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat()
            }
        except Exception as e:
            logger.error("scope_statistics_error", error=str(e))
            return {
                "total_expenses": 0,
                "total_amount": 0.0,
                "unique_employees": 0,
                "unique_merchants": 0
            }
    
    async def populate_technical_data(
        self,
        audit_report_id: str,
        sample_expense_ids: List[str]
    ) -> Dict[str, Any]:
        """Populate technical data from sample expenses"""
        try:
            # Get expenses
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.id.in_(sample_expense_ids),
                        Expense.tenant_id == self.tenant_id,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expenses = result.scalars().all()
            
            # Get policy violations
            violation_result = await self.db.execute(
                select(PolicyViolation).join(
                    Expense, PolicyViolation.expense_id == Expense.id
                ).where(
                    Expense.id.in_(sample_expense_ids)
                )
            )
            violations = violation_result.scalars().all()
            
            # Calculate statistics
            amounts = [float(exp.amount) for exp in expenses]
            categories = {}
            merchants = {}
            employees = {}
            statuses = {}
            
            for exp in expenses:
                # Categories
                cat = exp.category or "Uncategorized"
                categories[cat] = categories.get(cat, 0) + 1
                
                # Merchants
                merch = exp.merchant_name or "Unknown"
                merchants[merch] = merchants.get(merch, 0) + 1
                
                # Employees
                emp_id = str(exp.submitted_by)
                employees[emp_id] = employees.get(emp_id, 0) + 1
                
                # Statuses
                status = exp.approval_status or exp.status
                statuses[status] = statuses.get(status, 0) + 1
            
            technical_data = {
                "executive_summary": {
                    "total_expenses": len(expenses),
                    "total_amount": sum(amounts),
                    "sample_size": len(sample_expense_ids),
                    "anomalies_detected": 0,  # Will be populated by anomaly service
                    "policy_violations": len(violations),
                    "high_risk_items": 0  # Will be populated by risk service
                },
                "findings": {
                    "policy_violations": [
                        {
                            "expense_id": str(viol.expense_id),
                            "violation_type": viol.violation_type,
                            "severity": viol.violation_severity,
                            "message": viol.violation_message
                        }
                        for viol in violations
                    ]
                },
                "statistics": {
                    "by_category": categories,
                    "by_merchant": merchants,
                    "by_employee": employees,
                    "by_status": statuses
                }
            }
            
            return technical_data
            
        except Exception as e:
            logger.error("populate_technical_data_error", error=str(e))
            return self._get_technical_template()




