# -----------------------------------------------------------------------------
# File: metrics_collector.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Metrics collection service
# -----------------------------------------------------------------------------

"""
Metrics Collector
Collects and aggregates metrics from all services
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import structlog
import json

from .models import ServiceMetric, SLOMetric, AlertRule, Alert

logger = structlog.get_logger()

class MetricsCollector:
    """Collects and aggregates metrics from services"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_metric(
        self,
        service_name: str,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Record a metric"""
        try:
            metric = ServiceMetric(
                service_name=service_name,
                metric_name=metric_name,
                value=value,
                labels=labels or {},
                timestamp=timestamp or datetime.utcnow()
            )
            self.db.add(metric)
            await self.db.flush()
            logger.debug("metric_recorded", service=service_name, metric=metric_name, value=value)
        except Exception as e:
            logger.error("metric_recording_failed", error=str(e), exc_info=True)
    
    async def get_metrics(
        self,
        service_name: Optional[str] = None,
        metric_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get metrics with filters"""
        try:
            query = select(ServiceMetric)
            
            if service_name:
                query = query.where(ServiceMetric.service_name == service_name)
            if metric_name:
                query = query.where(ServiceMetric.metric_name == metric_name)
            if start_time:
                query = query.where(ServiceMetric.timestamp >= start_time)
            if end_time:
                query = query.where(ServiceMetric.timestamp <= end_time)
            
            query = query.order_by(ServiceMetric.timestamp.desc()).limit(limit)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            return [
                {
                    "id": str(m.id),
                    "service_name": m.service_name,
                    "metric_name": m.metric_name,
                    "value": m.value,
                    "labels": m.labels,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in metrics
            ]
        except Exception as e:
            logger.error("get_metrics_failed", error=str(e), exc_info=True)
            return []
    
    async def get_aggregated_metrics(
        self,
        service_name: str,
        metric_name: str,
        aggregation: str = "avg",  # avg, sum, min, max, count
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        group_by: Optional[str] = None  # e.g., "1h", "1d"
    ) -> Dict[str, Any]:
        """Get aggregated metrics"""
        try:
            query = select(ServiceMetric).where(
                and_(
                    ServiceMetric.service_name == service_name,
                    ServiceMetric.metric_name == metric_name
                )
            )
            
            if start_time:
                query = query.where(ServiceMetric.timestamp >= start_time)
            if end_time:
                query = query.where(ServiceMetric.timestamp <= end_time)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {"value": 0, "count": 0}
            
            values = [m.value for m in metrics]
            
            if aggregation == "avg":
                value = sum(values) / len(values)
            elif aggregation == "sum":
                value = sum(values)
            elif aggregation == "min":
                value = min(values)
            elif aggregation == "max":
                value = max(values)
            elif aggregation == "count":
                value = len(values)
            else:
                value = sum(values) / len(values)
            
            return {
                "value": value,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None
            }
        except Exception as e:
            logger.error("get_aggregated_metrics_failed", error=str(e), exc_info=True)
            return {"value": 0, "count": 0}
    
    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status for a service"""
        try:
            # Get latest metrics for the service
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            query = select(ServiceMetric).where(
                and_(
                    ServiceMetric.service_name == service_name,
                    ServiceMetric.timestamp >= start_time,
                    ServiceMetric.timestamp <= end_time
                )
            ).order_by(ServiceMetric.timestamp.desc()).limit(100)
            
            result = await self.db.execute(query)
            metrics = result.scalars().all()
            
            if not metrics:
                return {
                    "service_name": service_name,
                    "status": "unknown",
                    "last_seen": None,
                    "metrics_count": 0
                }
            
            latest_metric = metrics[0]
            time_since_last = (end_time - latest_metric.timestamp).total_seconds()
            
            # Service is healthy if we've seen metrics in the last 2 minutes
            status = "healthy" if time_since_last < 120 else "unhealthy"
            
            return {
                "service_name": service_name,
                "status": status,
                "last_seen": latest_metric.timestamp.isoformat(),
                "metrics_count": len(metrics),
                "time_since_last_seconds": time_since_last
            }
        except Exception as e:
            logger.error("get_service_health_failed", error=str(e), exc_info=True)
            return {
                "service_name": service_name,
                "status": "error",
                "error": str(e)
            }




