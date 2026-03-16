# -----------------------------------------------------------------------------
# File: narrative_generator.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Narrative generation for audit reports
# -----------------------------------------------------------------------------

"""
Narrative Generation Service
Generates narrative text for audit reports using LLM
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from datetime import date, datetime, timedelta
from common.models import Expense, PolicyViolation
import structlog
import json

from .config import settings

# Use RAG service settings if available (when rag_service is installed), otherwise keep audit settings
try:
    from services.rag_service.config import settings as rag_settings
    settings.LLM_PROVIDER = rag_settings.LLM_PROVIDER
    settings.GEMINI_API_KEY = rag_settings.GEMINI_API_KEY
    settings.GEMINI_MODEL = getattr(rag_settings, 'GEMINI_MODEL', 'models/gemini-2.0-flash')
    settings.OPENAI_API_KEY = getattr(rag_settings, 'OPENAI_API_KEY', '')
    settings.OPENAI_MODEL = getattr(rag_settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview')
except Exception:
    pass

logger = structlog.get_logger()

class NarrativeGenerator:
    """Generate narrative text for audit reports"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.llm_client = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client"""
        try:
            llm_provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
            if llm_provider == "gemini":
                import google.generativeai as genai
                gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
                if gemini_key:
                    genai.configure(api_key=gemini_key)
                    self.llm_client = genai.GenerativeModel(
                        getattr(settings, 'GEMINI_MODEL', 'models/gemini-2.0-flash')
                    )
            elif llm_provider == "openai":
                import openai
                openai_key = getattr(settings, 'OPENAI_API_KEY', '')
                if openai_key:
                    self.llm_client = openai.AsyncOpenAI(api_key=openai_key)
        except Exception as e:
            logger.error("narrative_llm_init_error", error=str(e))
            self.llm_client = None
    
    async def generate_report_narrative(
        self,
        report_data: Dict[str, Any],
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """Generate complete narrative for audit report"""
        try:
            narratives = {
                "introduction": await self._generate_introduction(period_start, period_end),
                "executive_summary": await self._generate_executive_summary(report_data),
                "detailed_findings": await self._generate_detailed_findings(report_data),
                "trend_analysis": await self._generate_trend_analysis(period_start, period_end),
                "conclusions": await self._generate_conclusions(report_data)
            }
            
            # P0: Fact-check all narratives against database
            verified_narratives = await self._fact_check_narratives(narratives, report_data, period_start, period_end)
            
            return verified_narratives
            
        except Exception as e:
            logger.error("generate_report_narrative_error", error=str(e))
            return self._get_default_narratives()
    
    async def _generate_introduction(
        self,
        period_start: date,
        period_end: date
    ) -> str:
        """Generate introduction section"""
        try:
            prompt = f"""
Generate an introduction section for a French accounting audit report.

Period: {period_start} to {period_end}

The introduction should:
- Explain the purpose of the audit
- Define the scope and period covered
- Describe the methodology used
- Be professional and suitable for French accounting standards

Return only the narrative text, no JSON or markdown.
"""
            
            if self.llm_client:
                llm_provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
                if llm_provider == "gemini":
                    response = await self.llm_client.generate_content_async(prompt)
                    return response.text.strip()
                elif llm_provider == "openai":
                    response = await self.llm_client.chat.completions.create(
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3
                    )
                    return response.choices[0].message.content.strip()
            
            return f"""
This audit report covers the period from {period_start} to {period_end}. 
The purpose of this audit is to review expense management practices, ensure compliance 
with French accounting regulations, and identify areas for improvement.
"""
            
        except Exception as e:
            logger.error("generate_introduction_error", error=str(e))
            return "Introduction section could not be generated."
    
    async def _generate_executive_summary(
        self,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary"""
        try:
            spend_summary = report_data.get("spend_summary", {})
            violations = report_data.get("policy_violations", {})
            vat_summary = report_data.get("vat_summary", {})
            
            prompt = f"""
Generate an executive summary for a French accounting audit report.

Key Findings:
- Total Expenses: {spend_summary.get('total_count', 0)} expenses, €{spend_summary.get('total_amount', 0):.2f}
- Policy Violations: {violations.get('total_violations', 0)} violations
- VAT Compliance: {vat_summary.get('vat_compliance', {}).get('compliance_rate', 0):.1f}% compliance rate

The executive summary should:
- Provide a high-level overview
- Highlight key findings
- Mention risk assessment
- Include recommendations summary
- Be concise (2-3 paragraphs)

Return JSON:
{{
    "overview": "High-level overview paragraph",
    "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
    "risk_assessment": "Risk assessment paragraph",
    "recommendations_summary": "Summary of recommendations"
}}
"""
            
            if self.llm_client:
                llm_provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
                if llm_provider == "gemini":
                    response = await self.llm_client.generate_content_async(prompt)
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    return json.loads(text)
                elif llm_provider == "openai":
                    response = await self.llm_client.chat.completions.create(
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    return json.loads(response.choices[0].message.content)
            
            return {
                "overview": f"This audit reviewed {spend_summary.get('total_count', 0)} expenses totaling €{spend_summary.get('total_amount', 0):.2f}.",
                "key_findings": [
                    f"{violations.get('total_violations', 0)} policy violations detected",
                    f"VAT compliance rate: {vat_summary.get('vat_compliance', {}).get('compliance_rate', 0):.1f}%"
                ],
                "risk_assessment": "Overall risk level is moderate.",
                "recommendations_summary": "Recommendations focus on improving compliance and reducing violations."
            }
            
        except Exception as e:
            logger.error("generate_executive_summary_error", error=str(e))
            return {
                "overview": "Executive summary could not be generated.",
                "key_findings": [],
                "risk_assessment": "",
                "recommendations_summary": ""
            }
    
    async def _generate_detailed_findings(
        self,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed findings section"""
        try:
            violations = report_data.get("policy_violations", {})
            vat_summary = report_data.get("vat_summary", {})
            
            prompt = f"""
Generate detailed findings section for a French accounting audit report.

Policy Violations:
- Total: {violations.get('total_violations', 0)}
- By Severity: {json.dumps(violations.get('by_severity', {}))}
- By Type: {json.dumps(violations.get('by_type', {}))}

VAT Summary:
- Total VAT: €{vat_summary.get('total_vat_amount', 0):.2f}
- Compliance Rate: {vat_summary.get('vat_compliance', {}).get('compliance_rate', 0):.1f}%

Return JSON:
{{
    "anomalies": "Description of anomalies found",
    "policy_compliance": "Policy compliance assessment",
    "process_observations": ["Observation 1", "Observation 2"],
    "control_effectiveness": "Assessment of control effectiveness"
}}
"""
            
            if self.llm_client:
                llm_provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
                if llm_provider == "gemini":
                    response = await self.llm_client.generate_content_async(prompt)
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    return json.loads(text)
                elif llm_provider == "openai":
                    response = await self.llm_client.chat.completions.create(
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    return json.loads(response.choices[0].message.content)
            
            return {
                "anomalies": "Various anomalies were detected in the expense data.",
                "policy_compliance": f"Policy compliance analysis identified {violations.get('total_violations', 0)} violations.",
                "process_observations": [
                    "Expense submission process appears functional",
                    "Approval workflow is in place"
                ],
                "control_effectiveness": "Controls are generally effective but improvements are recommended."
            }
            
        except Exception as e:
            logger.error("generate_detailed_findings_error", error=str(e))
            return {
                "anomalies": "",
                "policy_compliance": "",
                "process_observations": [],
                "control_effectiveness": ""
            }
    
    async def _generate_trend_analysis(
        self,
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """Generate trend analysis narratives"""
        try:
            # Get historical data for comparison
            previous_period_start = period_start - timedelta(days=(period_end - period_start).days + 1)
            previous_period_end = period_start - timedelta(days=1)
            
            # Current period data
            current_result = await self.db.execute(
                select(
                    func.count(Expense.id).label('count'),
                    func.sum(Expense.amount).label('total'),
                    func.sum(Expense.vat_amount).label('vat_total'),
                    func.count(PolicyViolation.id).label('violations')
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= period_start,
                        Expense.expense_date <= period_end,
                        Expense.deleted_at.is_(None)
                    )
                ).outerjoin(
                    PolicyViolation, PolicyViolation.expense_id == Expense.id
                )
            )
            current = current_result.one()
            
            # Previous period data
            prev_result = await self.db.execute(
                select(
                    func.count(Expense.id).label('count'),
                    func.sum(Expense.amount).label('total'),
                    func.sum(Expense.vat_amount).label('vat_total'),
                    func.count(PolicyViolation.id).label('violations')
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= previous_period_start,
                        Expense.expense_date <= previous_period_end,
                        Expense.deleted_at.is_(None)
                    )
                ).outerjoin(
                    PolicyViolation, PolicyViolation.expense_id == Expense.id
                )
            )
            previous = prev_result.one()
            
            # Calculate trends
            spend_change = 0.0
            if previous.total and previous.total > 0:
                spend_change = ((current.total or 0) - previous.total) / previous.total * 100
            
            vat_change = 0.0
            if previous.vat_total and previous.vat_total > 0:
                vat_change = ((current.vat_total or 0) - previous.vat_total) / previous.vat_total * 100
            
            violations_change = 0.0
            if previous.violations and previous.violations > 0:
                violations_change = ((current.violations or 0) - previous.violations) / previous.violations * 100
            
            prompt = f"""
Generate trend analysis narratives for a French accounting audit report.

Current Period ({period_start} to {period_end}):
- Expenses: {current.count or 0}, Total: €{current.total or 0:.2f}
- VAT: €{current.vat_total or 0:.2f}
- Violations: {current.violations or 0}

Previous Period ({previous_period_start} to {previous_period_end}):
- Expenses: {previous.count or 0}, Total: €{previous.total or 0:.2f}
- VAT: €{previous.vat_total or 0:.2f}
- Violations: {previous.violations or 0}

Trends:
- Spend Change: {spend_change:+.1f}%
- VAT Change: {vat_change:+.1f}%
- Violations Change: {violations_change:+.1f}%

Generate narratives for:
1. Spend increase/decrease analysis
2. VAT recovery changes analysis
3. Policy compliance trends

Return JSON:
{{
    "spend_trend": "Narrative about spend trends",
    "vat_trend": "Narrative about VAT recovery changes",
    "compliance_trend": "Narrative about policy compliance trends"
}}
"""
            
            if self.llm_client:
                llm_provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
                if llm_provider == "gemini":
                    response = await self.llm_client.generate_content_async(prompt)
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    return json.loads(text)
                elif llm_provider == "openai":
                    response = await self.llm_client.chat.completions.create(
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    return json.loads(response.choices[0].message.content)
            
            # Default narratives
            spend_trend = f"Spending {'increased' if spend_change > 0 else 'decreased'} by {abs(spend_change):.1f}% compared to the previous period."
            vat_trend = f"VAT recovery {'increased' if vat_change > 0 else 'decreased'} by {abs(vat_change):.1f}%."
            compliance_trend = f"Policy violations {'increased' if violations_change > 0 else 'decreased'} by {abs(violations_change):.1f}%."
            
            return {
                "spend_trend": spend_trend,
                "vat_trend": vat_trend,
                "compliance_trend": compliance_trend
            }
            
        except Exception as e:
            logger.error("generate_trend_analysis_error", error=str(e))
            return {
                "spend_trend": "Trend analysis could not be generated.",
                "vat_trend": "",
                "compliance_trend": ""
            }
    
    async def _generate_conclusions(
        self,
        report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate conclusions section"""
        try:
            violations = report_data.get("policy_violations", {})
            vat_summary = report_data.get("vat_summary", {})
            
            prompt = f"""
Generate conclusions section for a French accounting audit report.

Summary:
- Total Violations: {violations.get('total_violations', 0)}
- VAT Compliance: {vat_summary.get('vat_compliance', {}).get('compliance_rate', 0):.1f}%

Return JSON:
{{
    "overall_assessment": "Overall assessment paragraph",
    "risk_level": "high|medium|low",
    "compliance_status": "Compliance status assessment"
}}
"""
            
            if self.llm_client:
                llm_provider = getattr(settings, 'LLM_PROVIDER', 'gemini')
                if llm_provider == "gemini":
                    response = await self.llm_client.generate_content_async(prompt)
                    text = response.text.strip()
                    if text.startswith("```"):
                        text = text.split("```")[1]
                        if text.startswith("json"):
                            text = text[4:]
                    return json.loads(text)
                elif llm_provider == "openai":
                    response = await self.llm_client.chat.completions.create(
                        model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    return json.loads(response.choices[0].message.content)
            
            # Determine risk level
            violation_count = violations.get('total_violations', 0)
            compliance_rate = vat_summary.get('vat_compliance', {}).get('compliance_rate', 100)
            
            if violation_count > 20 or compliance_rate < 80:
                risk_level = "high"
            elif violation_count > 10 or compliance_rate < 90:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "overall_assessment": f"The audit identified {violation_count} policy violations and a VAT compliance rate of {compliance_rate:.1f}%.",
                "risk_level": risk_level,
                "compliance_status": f"Compliance status is {'satisfactory' if compliance_rate >= 90 else 'needs improvement'}."
            }
            
        except Exception as e:
            logger.error("generate_conclusions_error", error=str(e))
            return {
                "overall_assessment": "Conclusions could not be generated.",
                "risk_level": "medium",
                "compliance_status": ""
            }
    
    async def _fact_check_narratives(
        self,
        narratives: Dict[str, Any],
        report_data: Dict[str, Any],
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """
        P0: Fact-check narratives against actual database values
        Extracts numbers from narrative text and verifies against database
        """
        try:
            import re
            from sqlalchemy import func, and_
            
            # Get actual database values for verification
            actual_values = await self._get_actual_report_values(period_start, period_end)
            
            # Fact-check each narrative section
            verified = {}
            
            for section_name, section_content in narratives.items():
                if isinstance(section_content, str):
                    # Text narrative - extract and verify numbers
                    verified[section_name] = await self._fact_check_text(section_content, actual_values)
                elif isinstance(section_content, dict):
                    # Structured narrative - verify each field
                    verified[section_name] = {}
                    for key, value in section_content.items():
                        if isinstance(value, str):
                            verified[section_name][key] = await self._fact_check_text(value, actual_values)
                        elif isinstance(value, list):
                            verified[section_name][key] = [
                                await self._fact_check_text(item, actual_values) if isinstance(item, str) else item
                                for item in value
                            ]
                        else:
                            verified[section_name][key] = value
                else:
                    verified[section_name] = section_content
            
            logger.info("narratives_fact_checked", sections_checked=list(narratives.keys()))
            return verified
            
        except Exception as e:
            logger.error("fact_check_narratives_error", error=str(e))
            # Return original narratives if fact-checking fails
            return narratives
    
    async def _get_actual_report_values(
        self,
        period_start: date,
        period_end: date
    ) -> Dict[str, Any]:
        """Get actual values from database for fact-checking"""
        try:
            from sqlalchemy import func, and_
            
            # Get expense statistics
            expense_result = await self.db.execute(
                select(
                    func.count(Expense.id).label('total_count'),
                    func.sum(Expense.amount).label('total_amount'),
                    func.sum(Expense.vat_amount).label('total_vat'),
                    func.avg(Expense.amount).label('avg_amount')
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= period_start,
                        Expense.expense_date <= period_end,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expense_stats = expense_result.one()
            
            # Get violation statistics
            violation_result = await self.db.execute(
                select(
                    func.count(PolicyViolation.id).label('total_violations')
                ).join(
                    Expense, PolicyViolation.expense_id == Expense.id
                ).where(
                    and_(
                        Expense.tenant_id == self.tenant_id,
                        Expense.expense_date >= period_start,
                        Expense.expense_date <= period_end,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            violation_stats = violation_result.one()
            
            return {
                "total_expenses": expense_stats.total_count or 0,
                "total_amount": float(expense_stats.total_amount or 0),
                "total_vat": float(expense_stats.total_vat or 0),
                "avg_amount": float(expense_stats.avg_amount or 0),
                "total_violations": violation_stats.total_violations or 0
            }
            
        except Exception as e:
            logger.error("get_actual_report_values_error", error=str(e))
            return {}
    
    async def _fact_check_text(
        self,
        text: str,
        actual_values: Dict[str, Any]
    ) -> str:
        """Fact-check text by replacing numbers with verified values"""
        try:
            import re
            
            # Pattern to match numbers (including currency amounts)
            number_pattern = r'\b(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\b|\b(\d+\.?\d*)\b'
            
            def replace_number(match):
                number_str = match.group(0).replace(',', '').replace(' ', '')
                try:
                    number = float(number_str)
                    
                    # Check if this number matches any actual value (within tolerance)
                    tolerance = 0.01
                    for key, actual_value in actual_values.items():
                        if isinstance(actual_value, (int, float)):
                            if abs(actual_value - number) < tolerance:
                                # Number matches - keep it
                                return match.group(0)
                            # Check if it's a percentage representation
                            if "rate" in key.lower() or "compliance" in key.lower():
                                if abs(actual_value * 100 - number) < tolerance:
                                    return match.group(0)
                    
                    # Number doesn't match - try to find closest match
                    closest_key = None
                    closest_diff = float('inf')
                    for key, actual_value in actual_values.items():
                        if isinstance(actual_value, (int, float)):
                            diff = abs(actual_value - number)
                            if diff < closest_diff:
                                closest_diff = diff
                                closest_key = key
                    
                    # If close match found, replace with actual value
                    if closest_key and closest_diff < (number * 0.1):  # Within 10%
                        actual = actual_values[closest_key]
                        logger.warning(
                            "narrative_number_corrected",
                            original=number,
                            corrected=actual,
                            key=closest_key
                        )
                        # Format number to match original format
                        if '.' in match.group(0):
                            return f"{actual:.2f}"
                        else:
                            return f"{int(actual)}"
                    
                    # No match found - keep original but log warning
                    logger.warning("narrative_number_unverified", number=number)
                    return match.group(0)
                    
                except ValueError:
                    return match.group(0)
            
            # Replace numbers in text
            verified_text = re.sub(number_pattern, replace_number, text)
            
            return verified_text
            
        except Exception as e:
            logger.error("fact_check_text_error", error=str(e))
            return text
    
    def _get_default_narratives(self) -> Dict[str, Any]:
        """Get default narratives if LLM generation fails"""
        return {
            "introduction": "This audit report covers the specified period.",
            "executive_summary": {
                "overview": "Executive summary",
                "key_findings": [],
                "risk_assessment": "",
                "recommendations_summary": ""
            },
            "detailed_findings": {
                "anomalies": "",
                "policy_compliance": "",
                "process_observations": [],
                "control_effectiveness": ""
            },
            "trend_analysis": {
                "spend_trend": "",
                "vat_trend": "",
                "compliance_trend": ""
            },
            "conclusions": {
                "overall_assessment": "",
                "risk_level": "medium",
                "compliance_status": ""
            }
        }

