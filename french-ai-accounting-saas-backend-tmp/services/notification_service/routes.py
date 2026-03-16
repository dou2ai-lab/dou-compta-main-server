"""
Enhanced Notification Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Optional
from uuid import UUID
from datetime import datetime
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .models import Notification, NotificationRule
from .schemas import (
    NotificationResponse, NotificationListResponse,
    NotificationRuleCreate, NotificationRuleResponse,
    CreateNotificationRequest,
)
from .engine import dispatch_notification

logger = structlog.get_logger()
router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for the current user."""
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.tenant_id == current_user.tenant_id,
    )
    count_query = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.tenant_id == current_user.tenant_id,
    )
    unread_query = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.tenant_id == current_user.tenant_id,
        Notification.status == "unread",
    )

    if status:
        query = query.where(Notification.status == status)
        count_query = count_query.where(Notification.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    unread_result = await db.execute(unread_query)
    unread_count = unread_result.scalar() or 0

    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    notifications = list(result.scalars().all())

    return NotificationListResponse(
        data=[NotificationResponse(
            id=n.id, user_id=n.user_id, type=n.type,
            title=n.title, body=n.body, channel=n.channel,
            status=n.status, priority=n.priority,
            entity_type=n.entity_type, entity_id=n.entity_id,
            action_url=n.action_url, read_at=n.read_at,
            created_at=n.created_at,
        ) for n in notifications],
        total=total,
        unread_count=unread_count,
    )


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification non trouvee")

    notif.status = "read"
    notif.read_at = datetime.utcnow()
    await db.commit()
    return {"success": True}


@router.post("/read-all")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    await db.execute(
        update(Notification).where(
            Notification.user_id == current_user.id,
            Notification.status == "unread",
        ).values(status="read", read_at=datetime.utcnow())
    )
    await db.commit()
    return {"success": True}


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notifications."""
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.tenant_id == current_user.tenant_id,
            Notification.status == "unread",
        )
    )
    return {"unread_count": result.scalar() or 0}


@router.post("", response_model=NotificationResponse)
async def create_notification(
    payload: CreateNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a notification (admin/system use)."""
    notif = await dispatch_notification(
        db, current_user.tenant_id, payload.user_id,
        payload.type, {"title": payload.title, "body": payload.body or ""},
        entity_type=payload.entity_type, entity_id=payload.entity_id,
        action_url=payload.action_url,
    )
    await db.commit()
    return NotificationResponse(
        id=notif.id, user_id=notif.user_id, type=notif.type,
        title=notif.title, body=notif.body, channel=notif.channel,
        status=notif.status, priority=notif.priority,
        entity_type=notif.entity_type, entity_id=notif.entity_id,
        action_url=notif.action_url, read_at=notif.read_at,
        created_at=notif.created_at,
    )


# --- Notification Rules ---

@router.get("/rules", response_model=list[NotificationRuleResponse])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(NotificationRule).where(
            NotificationRule.tenant_id == current_user.tenant_id,
        ).order_by(NotificationRule.event_type)
    )
    rules = list(result.scalars().all())
    return [NotificationRuleResponse(
        id=r.id, event_type=r.event_type, name=r.name,
        description=r.description, condition=r.condition,
        channels=r.channels, template=r.template,
        is_active=r.is_active, escalation_config=r.escalation_config,
        created_at=r.created_at,
    ) for r in rules]


@router.post("/rules", response_model=NotificationRuleResponse)
async def create_rule(
    payload: NotificationRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = NotificationRule(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **payload.model_dump(exclude_none=True),
    )
    db.add(rule)
    await db.commit()
    return NotificationRuleResponse(
        id=rule.id, event_type=rule.event_type, name=rule.name,
        description=rule.description, condition=rule.condition,
        channels=rule.channels, template=rule.template,
        is_active=rule.is_active, escalation_config=rule.escalation_config,
        created_at=rule.created_at,
    )
