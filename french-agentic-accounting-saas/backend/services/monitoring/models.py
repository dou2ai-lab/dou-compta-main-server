# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Monitoring service database models
# -----------------------------------------------------------------------------

"""
Monitoring Service Models
Database models for metrics, SLOs, and alerts
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from common.database import Base

class ServiceMetric(Base):
    """Service metric data"""
    __tablename__ = "service_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    labels = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class SLOMetric(Base):
    """Service Level Objective definition"""
    __tablename__ = "slo_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    target_value = Column(Float, nullable=False)
    target_type = Column(String(20), default="minimum")  # minimum, maximum
    window_days = Column(Integer, default=30)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class AlertRule(Base):
    """Alert rule definition"""
    __tablename__ = "alert_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    service_name = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    condition = Column(String(10), nullable=False)  # >, <, >=, <=, ==
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), default="warning")  # info, warning, critical
    description = Column(Text)
    notification_channels = Column(ARRAY(String), default=["email"])
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    alerts = relationship("Alert", back_populates="rule")

class Alert(Base):
    """Active or resolved alert"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id"), nullable=False, index=True)
    service_name = Column(String(100), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="active", index=True)  # active, resolved, acknowledged
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(255))
    
    rule = relationship("AlertRule", back_populates="alerts")




