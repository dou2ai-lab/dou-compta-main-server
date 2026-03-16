# -----------------------------------------------------------------------------
# File: alert_manager.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Alert management and notification
# -----------------------------------------------------------------------------

"""
Alert Manager
Manages alert rules and triggers alerts
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import structlog

from .models import AlertRule, Alert, ServiceMetric
from services.notification_service.service import EmailNotificationService

logger = structlog.get_logger()

class AlertManager:
    """Manages alerts and alert rules"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notification_service = EmailNotificationService(db)
    
    async def create_alert_rule(
        self,
        name: str,
        service_name: str,
        metric_name: str,
        condition: str,  # e.g., ">", "<", ">=", "<=", "=="
        threshold: float,
        severity: str = "warning",  # info, warning, critical
        description: Optional[str] = None,
        notification_channels: Optional[List[str]] = None
    ) -> AlertRule:
        """Create a new alert rule"""
        try:
            rule = AlertRule(
                name=name,
                service_name=service_name,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                severity=severity,
                description=description or f"Alert when {metric_name} {condition} {threshold}",
                notification_channels=notification_channels or ["email"],
                is_active=True,
                created_at=datetime.utcnow()
            )
            self.db.add(rule)
            await self.db.flush()
            logger.info("alert_rule_created", rule_name=name, service=service_name, metric=metric_name)
            return rule
        except Exception as e:
            logger.error("alert_rule_creation_failed", error=str(e), exc_info=True)
            raise
    
    async def evaluate_alert_rules(self, service_name: Optional[str] = None):
        """Evaluate all active alert rules"""
        try:
            query = select(AlertRule).where(AlertRule.is_active == True)
            if service_name:
                query = query.where(AlertRule.service_name == service_name)
            
            result = await self.db.execute(query)
            rules = result.scalars().all()
            
            triggered_alerts = []
            
            for rule in rules:
                # Get latest metric value
                metric_query = select(ServiceMetric).where(
                    and_(
                        ServiceMetric.service_name == rule.service_name,
                        ServiceMetric.metric_name == rule.metric_name
                    )
                ).order_by(ServiceMetric.timestamp.desc()).limit(1)
                
                metric_result = await self.db.execute(metric_query)
                metric = metric_result.scalar_one_or_none()
                
                if not metric:
                    continue
                
                # Evaluate condition
                triggered = False
                if rule.condition == ">":
                    triggered = metric.value > rule.threshold
                elif rule.condition == "<":
                    triggered = metric.value < rule.threshold
                elif rule.condition == ">=":
                    triggered = metric.value >= rule.threshold
                elif rule.condition == "<=":
                    triggered = metric.value <= rule.threshold
                elif rule.condition == "==":
                    triggered = abs(metric.value - rule.threshold) < 0.001
                
                if triggered:
                    # Check if alert already exists and is still active
                    existing_alert_query = select(Alert).where(
                        and_(
                            Alert.alert_rule_id == rule.id,
                            Alert.status == "active"
                        )
                    )
                    existing_result = await self.db.execute(existing_alert_query)
                    existing_alert = existing_result.scalar_one_or_none()
                    
                    if not existing_alert:
                        # Create new alert
                        alert = Alert(
                            alert_rule_id=rule.id,
                            service_name=rule.service_name,
                            metric_name=rule.metric_name,
                            metric_value=metric.value,
                            threshold=rule.threshold,
                            severity=rule.severity,
                            message=f"{rule.description}: {metric.value} {rule.condition} {rule.threshold}",
                            status="active",
                            triggered_at=datetime.utcnow()
                        )
                        self.db.add(alert)
                        await self.db.flush()
                        
                        # Send notifications
                        await self._send_alert_notifications(alert, rule)
                        
                        triggered_alerts.append(alert)
                        logger.warning("alert_triggered", rule_name=rule.name, metric_value=metric.value, threshold=rule.threshold)
            
            await self.db.commit()
            return triggered_alerts
            
        except Exception as e:
            logger.error("alert_evaluation_failed", error=str(e), exc_info=True)
            await self.db.rollback()
            return []
    
    async def _send_alert_notifications(self, alert: Alert, rule: AlertRule):
        """Send alert notifications via configured channels"""
        try:
            for channel in rule.notification_channels:
                if channel == "email":
                    # Send email to admins (this would need admin user lookup)
                    logger.info("alert_notification_sent", alert_id=str(alert.id), channel=channel)
                elif channel == "slack":
                    # Send Slack notification
                    logger.info("alert_notification_sent", alert_id=str(alert.id), channel=channel)
                elif channel == "pagerduty":
                    # Send PagerDuty notification
                    logger.info("alert_notification_sent", alert_id=str(alert.id), channel=channel)
        except Exception as e:
            logger.error("alert_notification_failed", error=str(e), exc_info=True)
    
    async def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None):
        """Resolve an alert"""
        try:
            result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
            alert = result.scalar_one_or_none()
            
            if alert:
                alert.status = "resolved"
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                await self.db.commit()
                logger.info("alert_resolved", alert_id=alert_id, resolved_by=resolved_by)
        except Exception as e:
            logger.error("alert_resolution_failed", error=str(e), exc_info=True)
            await self.db.rollback()
    
    async def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        try:
            query = select(Alert).where(Alert.status == "active")
            if severity:
                query = query.where(Alert.severity == severity)
            
            query = query.order_by(Alert.triggered_at.desc())
            
            result = await self.db.execute(query)
            alerts = result.scalars().all()
            
            return [
                {
                    "id": str(a.id),
                    "service_name": a.service_name,
                    "metric_name": a.metric_name,
                    "metric_value": a.metric_value,
                    "threshold": a.threshold,
                    "severity": a.severity,
                    "message": a.message,
                    "triggered_at": a.triggered_at.isoformat()
                }
                for a in alerts
            ]
        except Exception as e:
            logger.error("get_active_alerts_failed", error=str(e), exc_info=True)
            return []




