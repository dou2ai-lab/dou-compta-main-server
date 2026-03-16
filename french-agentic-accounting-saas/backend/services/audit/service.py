# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Audit service layer
# -----------------------------------------------------------------------------

"""
Audit Service
Main service layer for audit reports and evidence collection
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from common.models import User
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from .models import AuditReport, AuditMetadata, AuditScope, AuditEvidence
from .report_template import AuditReportTemplate
from .evidence_collector import EvidenceCollector
from .audit_trail import AuditTrailService
from .report_generator import AuditReportGenerator
from .narrative_generator import NarrativeGenerator
import structlog

logger = structlog.get_logger()

class AuditService:
    """Main audit service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str, storage_service=None):
        self.db = db
        self.tenant_id = tenant_id
        self.report_template = AuditReportTemplate(db, tenant_id)
        self.evidence_collector = EvidenceCollector(db, tenant_id, storage_service)
        self.audit_trail = AuditTrailService(db, tenant_id)
        self.report_generator = AuditReportGenerator(db, tenant_id)
        self.narrative_generator = NarrativeGenerator(db, tenant_id)
    
    async def create_audit_report(
        self,
        title: str,
        period_start: date,
        period_end: date,
        period_type: str,
        report_type: str,
        created_by: str,
        description: Optional[str] = None
    ) -> AuditReport:
        """Create a new audit report"""
        try:
            # Generate template
            template = await self.report_template.create_report_template(
                title=title,
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                report_type=report_type,
                created_by=created_by
            )
            
            if description:
                template["description"] = description
            
            # Create report
            report = AuditReport(
                tenant_id=self.tenant_id,
                created_by=created_by,
                report_number=template["report_number"],
                title=template["title"],
                description=template["description"],
                audit_period_start=period_start,
                audit_period_end=period_end,
                period_type=period_type,
                report_type=report_type,
                template_version=template["template_version"],
                status="draft",
                technical_data=template["technical_data"],
                narrative_sections=template["narrative_sections"],
                metadata=template["metadata"],
                sample_size=0,
                total_expenses_in_scope=template["scope_statistics"]["total_expenses"],
                total_amount_in_scope=template["scope_statistics"]["total_amount"]
            )
            
            self.db.add(report)
            await self.db.flush()
            
            logger.info("audit_report_created", report_id=str(report.id), report_number=template["report_number"])
            
            return report
            
        except Exception as e:
            logger.error("create_audit_report_error", error=str(e))
            raise
    
    async def get_audit_report(self, report_id: str) -> Optional[AuditReport]:
        """Get audit report by ID"""
        result = await self.db.execute(
            select(AuditReport).where(
                and_(
                    AuditReport.id == report_id,
                    AuditReport.tenant_id == self.tenant_id,
                    AuditReport.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_audit_reports(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[AuditReport]:
        """List audit reports"""
        query = select(AuditReport).where(
            and_(
                AuditReport.tenant_id == self.tenant_id,
                AuditReport.deleted_at.is_(None)
            )
        )
        
        if status:
            query = query.where(AuditReport.status == status)
        
        query = query.order_by(AuditReport.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_audit_report(
        self,
        report_id: str,
        updates: Dict[str, Any]
    ) -> Optional[AuditReport]:
        """Update audit report"""
        report = await self.get_audit_report(report_id)
        
        if not report:
            return None
        
        # Update fields
        if "title" in updates:
            report.title = updates["title"]
        if "description" in updates:
            report.description = updates["description"]
        if "status" in updates:
            report.status = updates["status"]
        if "technical_data" in updates:
            report.technical_data = updates["technical_data"]
        if "narrative_sections" in updates:
            report.narrative_sections = updates["narrative_sections"]
        if "metadata" in updates:
            report.metadata_ = {**(report.metadata_ or {}), **updates["metadata"]}
        
        if updates.get("status") == "completed":
            report.completed_at = datetime.utcnow()
        if updates.get("status") == "published":
            report.published_at = datetime.utcnow()
        
        await self.db.flush()
        
        return report
    
    async def add_metadata(
        self,
        report_id: str,
        key: str,
        value: Any,
        created_by: str
    ) -> AuditMetadata:
        """Add metadata to audit report"""
        metadata = AuditMetadata(
            audit_report_id=report_id,
            tenant_id=self.tenant_id,
            key=key,
            value=value if isinstance(value, dict) else {"value": value},
            data_type=self._infer_data_type(value),
            created_by=created_by
        )
        
        self.db.add(metadata)
        await self.db.flush()
        
        return metadata
    
    async def get_metadata(self, report_id: str) -> List[AuditMetadata]:
        """Get all metadata for audit report"""
        result = await self.db.execute(
            select(AuditMetadata).where(
                and_(
                    AuditMetadata.audit_report_id == report_id,
                    AuditMetadata.tenant_id == self.tenant_id
                )
            )
        )
        return result.scalars().all()
    
    async def populate_report_from_sample(
        self,
        report_id: str,
        sample_expense_ids: List[str],
        created_by: str
    ) -> Dict[str, Any]:
        """Populate audit report from sample expenses"""
        try:
            report = await self.get_audit_report(report_id)
            if not report:
                return {"success": False, "error": "Report not found"}
            
            # Populate technical data
            technical_data = await self.report_template.populate_technical_data(
                report_id, sample_expense_ids
            )
            
            report.technical_data = technical_data
            report.sample_size = len(sample_expense_ids)
            
            # Collect evidence
            evidence_result = await self.evidence_collector.collect_evidence_for_sample(
                report_id, sample_expense_ids, created_by
            )
            
            await self.db.flush()
            
            return {
                "success": True,
                "report_id": report_id,
                "sample_size": len(sample_expense_ids),
                "evidence_collected": evidence_result.get("evidence_items_collected", 0)
            }
            
        except Exception as e:
            logger.error("populate_report_error", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from value"""
        if isinstance(value, dict):
            return "json"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, datetime):
            return "datetime"
        elif isinstance(value, date):
            return "date"
        else:
            return "string"

