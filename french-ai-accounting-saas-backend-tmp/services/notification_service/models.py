"""
SQLAlchemy ORM models for the enhanced Notification Service.
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text)
    channel = Column(String(20), default="in_app")
    status = Column(String(20), default="unread")
    priority = Column(String(10), default="normal")
    entity_type = Column(String(50))
    entity_id = Column(UUID(as_uuid=True))
    action_url = Column(String(500))
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    condition = Column(JSONB, default={})
    channels = Column(JSONB, default=["in_app"])
    template = Column(String(100))
    is_active = Column(Boolean, default=True)
    escalation_config = Column(JSONB)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
