# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Monitoring service API routes
# -----------------------------------------------------------------------------

"""
Monitoring Service Routes
FastAPI routes for monitoring endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .schemas import (
    MetricRecordRequest, MetricResponse, AggregatedMetricResponse,
    ServiceHealthResponse, SLODefinitionRequest, SLOResponse,
    SLOComplianceResponse, AlertRuleRequest, AlertRuleResponse, AlertResponse
)
from .metrics_collector import MetricsCollector
from .slo_manager import SLOManager
from .alert_manager import AlertManager

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.post("/metrics", response_model=MetricResponse, status_code=201)
async def record_metric(
    request: MetricRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a metric"""
    collector = MetricsCollector(db)
    await collector.record_metric(
        service_name=request.service_name,
        metric_name=request.metric_name,
        value=request.value,
        labels=request.labels,
        timestamp=request.timestamp
    )
    return {
        "id": "recorded",
        "service_name": request.service_name,
        "metric_name": request.metric_name,
        "value": request.value,
        "labels": request.labels or {},
        "timestamp": (request.timestamp or datetime.utcnow()).isoformat()
    }

@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics(
    service_name: Optional[str] = Query(None),
    metric_name: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(1000, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get metrics"""
    collector = MetricsCollector(db)
    metrics = await collector.get_metrics(
        service_name=service_name,
        metric_name=metric_name,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    return metrics

@router.get("/metrics/aggregated", response_model=AggregatedMetricResponse)
async def get_aggregated_metrics(
    service_name: str = Query(...),
    metric_name: str = Query(...),
    aggregation: str = Query("avg"),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated metrics"""
    collector = MetricsCollector(db)
    result = await collector.get_aggregated_metrics(
        service_name=service_name,
        metric_name=metric_name,
        aggregation=aggregation,
        start_time=start_time,
        end_time=end_time
    )
    return result

@router.get("/health/{service_name}", response_model=ServiceHealthResponse)
async def get_service_health(
    service_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get service health status"""
    collector = MetricsCollector(db)
    health = await collector.get_service_health(service_name)
    return health

@router.get("/health", response_model=List[ServiceHealthResponse])
async def get_all_services_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get health status for all services"""
    collector = MetricsCollector(db)
    # List of known services
    services = [
        "auth-service", "expense-service", "admin-service", "audit-service",
        "file-service", "ocr-service", "llm-service", "policy-service",
        "report-service", "anomaly-service", "rag-service", "erp-service",
        "gdpr-service", "performance-service", "security-service", "monitoring-service"
    ]
    health_statuses = []
    for service_name in services:
        health = await collector.get_service_health(service_name)
        health_statuses.append(health)
    return health_statuses

@router.post("/slos", response_model=SLOResponse, status_code=201)
async def define_slo(
    request: SLODefinitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Define a new SLO"""
    slo_manager = SLOManager(db)
    slo = await slo_manager.define_slo(
        service_name=request.service_name,
        metric_name=request.metric_name,
        target_value=request.target_value,
        window_days=request.window_days,
        description=request.description
    )
    return {
        "id": str(slo.id),
        "service_name": slo.service_name,
        "metric_name": slo.metric_name,
        "target_value": slo.target_value,
        "target_type": slo.target_type,
        "window_days": slo.window_days,
        "description": slo.description,
        "created_at": slo.created_at.isoformat()
    }

@router.get("/slos", response_model=List[SLOResponse])
async def get_all_slos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all SLO definitions"""
    slo_manager = SLOManager(db)
    slos = await slo_manager.get_all_slos()
    return slos

@router.get("/slos/{slo_id}/compliance", response_model=SLOComplianceResponse)
async def get_slo_compliance(
    slo_id: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SLO compliance"""
    slo_manager = SLOManager(db)
    compliance = await slo_manager.calculate_slo_compliance(
        slo_id=slo_id,
        start_time=start_time,
        end_time=end_time
    )
    if "error" in compliance:
        raise HTTPException(status_code=404, detail=compliance["error"])
    return compliance

@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(
    request: AlertRuleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an alert rule"""
    alert_manager = AlertManager(db)
    rule = await alert_manager.create_alert_rule(
        name=request.name,
        service_name=request.service_name,
        metric_name=request.metric_name,
        condition=request.condition,
        threshold=request.threshold,
        severity=request.severity,
        description=request.description,
        notification_channels=request.notification_channels
    )
    return {
        "id": str(rule.id),
        "name": rule.name,
        "service_name": rule.service_name,
        "metric_name": rule.metric_name,
        "condition": rule.condition,
        "threshold": rule.threshold,
        "severity": rule.severity,
        "description": rule.description,
        "notification_channels": rule.notification_channels,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat()
    }

@router.post("/alert-rules/evaluate")
async def evaluate_alert_rules(
    service_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluate all alert rules"""
    alert_manager = AlertManager(db)
    triggered = await alert_manager.evaluate_alert_rules(service_name=service_name)
    return {
        "triggered_count": len(triggered),
        "alerts": [
            {
                "id": str(a.id),
                "service_name": a.service_name,
                "metric_name": a.metric_name,
                "severity": a.severity,
                "message": a.message
            }
            for a in triggered
        ]
    }

@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    severity: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all active alerts"""
    alert_manager = AlertManager(db)
    alerts = await alert_manager.get_active_alerts(severity=severity)
    return alerts

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert"""
    alert_manager = AlertManager(db)
    await alert_manager.resolve_alert(alert_id, resolved_by=str(current_user.id))
    return {"status": "resolved", "alert_id": alert_id}

