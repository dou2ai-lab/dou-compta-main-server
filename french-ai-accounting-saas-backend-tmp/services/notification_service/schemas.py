"""
Pydantic schemas for the Notification Service API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    body: Optional[str] = None
    channel: str
    status: str
    priority: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    action_url: Optional[str] = None
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    data: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationRuleCreate(BaseModel):
    event_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    condition: Optional[dict] = None
    channels: Optional[list] = ["in_app"]
    template: Optional[str] = None
    escalation_config: Optional[dict] = None


class NotificationRuleResponse(BaseModel):
    id: UUID
    event_type: str
    name: str
    description: Optional[str] = None
    condition: Optional[dict] = None
    channels: Optional[list] = None
    template: Optional[str] = None
    is_active: bool
    escalation_config: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateNotificationRequest(BaseModel):
    user_id: UUID
    type: str
    title: str
    body: Optional[str] = None
    channel: str = "in_app"
    priority: str = "normal"
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    action_url: Optional[str] = None
