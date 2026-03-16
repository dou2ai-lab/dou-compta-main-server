# -----------------------------------------------------------------------------
# File: slo_manager.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: SLO and error budget management
# -----------------------------------------------------------------------------

"""
SLO Manager
Manages Service Level Objectives (SLOs) and error budgets
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
import structlog

from .models import SLOMetric, ServiceMetric

logger = structlog.get_logger()

class SLOManager:
    """Manages SLOs and error budgets"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def define_slo(
        self,
        service_name: str,
        metric_name: str,
        target_value: float,
        window_days: int = 30,
        description: Optional[str] = None
    ) -> SLOMetric:
        """Define a new SLO"""
        try:
            slo = SLOMetric(
                service_name=service_name,
                metric_name=metric_name,
                target_value=target_value,
                window_days=window_days,
                description=description or f"SLO for {service_name}.{metric_name}",
                created_at=datetime.utcnow()
            )
            self.db.add(slo)
            await self.db.flush()
            logger.info("slo_defined", service=service_name, metric=metric_name, target=target_value)
            return slo
        except Exception as e:
            logger.error("slo_definition_failed", error=str(e), exc_info=True)
            raise
    
    async def calculate_slo_compliance(
        self,
        slo_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate SLO compliance"""
        try:
            # Get SLO definition
            result = await self.db.execute(
                select(SLOMetric).where(SLOMetric.id == slo_id)
            )
            slo = result.scalar_one_or_none()
            
            if not slo:
                return {"error": "SLO not found"}
            
            # Calculate time window
            if not end_time:
                end_time = datetime.utcnow()
            if not start_time:
                start_time = end_time - timedelta(days=slo.window_days)
            
            # Get metrics for the period
            query = select(ServiceMetric).where(
                and_(
                    ServiceMetric.service_name == slo.service_name,
                    ServiceMetric.metric_name == slo.metric_name,
                    ServiceMetric.timestamp >= start_time,
                    ServiceMetric.timestamp <= end_time
                )
            )
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "slo_id": str(slo.id),
                    "compliance": None,
                    "error": "No metrics found for period"
                }
            
            # Calculate actual value based on metric type
            values = [m.value for m in metrics]
            
            # For availability/uptime metrics, calculate percentage
            if "availability" in slo.metric_name.lower() or "uptime" in slo.metric_name.lower():
                actual_value = (sum(1 for v in values if v >= 1) / len(values)) * 100
            # For latency metrics, calculate percentile
            elif "latency" in slo.metric_name.lower() or "duration" in slo.metric_name.lower():
                sorted_values = sorted(values)
                p95_index = int(len(sorted_values) * 0.95)
                actual_value = sorted_values[p95_index] if p95_index < len(sorted_values) else sorted_values[-1]
            # For error rate metrics
            elif "error" in slo.metric_name.lower() or "failure" in slo.metric_name.lower():
                actual_value = (sum(1 for v in values if v > 0) / len(values)) * 100
            else:
                # Default: average
                actual_value = sum(values) / len(values)
            
            # Calculate compliance
            compliance = actual_value >= slo.target_value if slo.target_type == "minimum" else actual_value <= slo.target_value
            
            # Calculate error budget
            error_budget = abs(actual_value - slo.target_value)
            error_budget_percentage = (error_budget / slo.target_value) * 100 if slo.target_value > 0 else 0
            
            return {
                "slo_id": str(slo.id),
                "service_name": slo.service_name,
                "metric_name": slo.metric_name,
                "target_value": slo.target_value,
                "actual_value": actual_value,
                "compliance": compliance,
                "error_budget": error_budget,
                "error_budget_percentage": error_budget_percentage,
                "metrics_count": len(metrics),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }
        except Exception as e:
            logger.error("slo_compliance_calculation_failed", error=str(e), exc_info=True)
            return {"error": str(e)}
    
    async def get_all_slos(self) -> List[Dict[str, Any]]:
        """Get all SLO definitions"""
        try:
            result = await self.db.execute(select(SLOMetric))
            slos = result.scalars().all()
            
            return [
                {
                    "id": str(slo.id),
                    "service_name": slo.service_name,
                    "metric_name": slo.metric_name,
                    "target_value": slo.target_value,
                    "target_type": slo.target_type,
                    "window_days": slo.window_days,
                    "description": slo.description,
                    "created_at": slo.created_at.isoformat()
                }
                for slo in slos
            ]
        except Exception as e:
            logger.error("get_all_slos_failed", error=str(e), exc_info=True)
            return []




