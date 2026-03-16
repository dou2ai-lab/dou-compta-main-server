# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Monitoring service Pydantic schemas
# -----------------------------------------------------------------------------

"""
Monitoring Service Schemas
Pydantic models for request/response validation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

class MetricRecordRequest(BaseModel):
    """Request to record a metric"""
    service_name: str = Field(..., description="Name of the service")
    metric_name: str = Field(..., description="Name of the metric")
    value: float = Field(..., description="Metric value")
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")
    timestamp: Optional[datetime] = Field(None, description="Metric timestamp")

class MetricResponse(BaseModel):
    """Metric response"""
    id: str
    service_name: str
    metric_name: str
    value: float
    labels: Dict[str, str]
    timestamp: str

class AggregatedMetricResponse(BaseModel):
    """Aggregated metric response"""
    value: float
    count: int
    min: Optional[float] = None
    max: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class ServiceHealthResponse(BaseModel):
    """Service health response"""
    service_name: str
    status: str
    last_seen: Optional[str] = None
    metrics_count: int
    time_since_last_seconds: Optional[float] = None

class SLODefinitionRequest(BaseModel):
    """Request to define an SLO"""
    service_name: str
    metric_name: str
    target_value: float
    window_days: int = 30
    description: Optional[str] = None

class SLOResponse(BaseModel):
    """SLO response"""
    id: str
    service_name: str
    metric_name: str
    target_value: float
    target_type: str
    window_days: int
    description: Optional[str] = None
    created_at: str

class SLOComplianceResponse(BaseModel):
    """SLO compliance response"""
    slo_id: str
    service_name: str
    metric_name: str
    target_value: float
    actual_value: float
    compliance: bool
    error_budget: float
    error_budget_percentage: float
    metrics_count: int
    start_time: str
    end_time: str

class AlertRuleRequest(BaseModel):
    """Request to create an alert rule"""
    name: str
    service_name: str
    metric_name: str
    condition: str = Field(..., description="Condition: >, <, >=, <=, ==")
    threshold: float
    severity: str = "warning"
    description: Optional[str] = None
    notification_channels: Optional[List[str]] = ["email"]

class AlertRuleResponse(BaseModel):
    """Alert rule response"""
    id: str
    name: str
    service_name: str
    metric_name: str
    condition: str
    threshold: float
    severity: str
    description: Optional[str] = None
    notification_channels: List[str]
    is_active: bool
    created_at: str

class AlertResponse(BaseModel):
    """Alert response"""
    id: str
    service_name: str
    metric_name: str
    metric_value: float
    threshold: float
    severity: str
    message: str
    status: str
    triggered_at: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None




