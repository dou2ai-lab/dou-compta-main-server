"""
Notification Engine - Event-driven notification dispatch.
Evaluates notification rules and creates notifications based on domain events.
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from typing import Optional

from .models import Notification, NotificationRule

logger = structlog.get_logger()

# French notification templates
TEMPLATES = {
    "expense.approved": {
        "title": "Depense approuvee",
        "body": "Votre depense de {amount} EUR a ete approuvee.",
        "priority": "normal",
    },
    "expense.rejected": {
        "title": "Depense rejetee",
        "body": "Votre depense de {amount} EUR a ete rejetee. Motif: {reason}",
        "priority": "high",
    },
    "expense.submitted": {
        "title": "Nouvelle depense a approuver",
        "body": "Une depense de {amount} EUR soumise par {submitter} attend votre approbation.",
        "priority": "normal",
    },
    "declaration.due": {
        "title": "Echeance fiscale proche",
        "body": "La declaration {declaration_type} est due le {due_date}.",
        "priority": "high",
    },
    "declaration.overdue": {
        "title": "Echeance fiscale depassee",
        "body": "La declaration {declaration_type} devait etre deposee le {due_date}. Risque de penalites.",
        "priority": "urgent",
    },
    "anomaly.detected": {
        "title": "Anomalie detectee",
        "body": "Une anomalie a ete detectee (score de risque: {risk_score}). Verification requise.",
        "priority": "high",
    },
    "entry.created": {
        "title": "Ecriture comptable generee",
        "body": "L'ecriture {entry_number} a ete generee dans le journal {journal_code}.",
        "priority": "low",
    },
    "document.received": {
        "title": "Document recu",
        "body": "Un nouveau document a ete recu et classe automatiquement.",
        "priority": "normal",
    },
    "reconciliation.completed": {
        "title": "Rapprochement termine",
        "body": "{matched_count} ecritures rapprochees automatiquement.",
        "priority": "normal",
    },
}


async def evaluate_rules(
    db: AsyncSession, tenant_id: UUID, event_type: str, payload: dict
) -> list[NotificationRule]:
    """Find active notification rules matching an event type."""
    result = await db.execute(
        select(NotificationRule).where(
            NotificationRule.tenant_id == tenant_id,
            NotificationRule.event_type == event_type,
            NotificationRule.is_active == True,
        )
    )
    rules = list(result.scalars().all())

    # Filter by condition evaluation
    matched = []
    for rule in rules:
        if _evaluate_condition(rule.condition, payload):
            matched.append(rule)
    return matched


def _evaluate_condition(condition: dict, payload: dict) -> bool:
    """Simple condition evaluator. Supports basic field matching."""
    if not condition:
        return True

    for key, expected in condition.items():
        actual = payload.get(key)
        if isinstance(expected, dict):
            op = expected.get("op", "eq")
            val = expected.get("value")
            if op == "eq" and actual != val:
                return False
            elif op == "gt" and (actual is None or float(actual) <= float(val)):
                return False
            elif op == "lt" and (actual is None or float(actual) >= float(val)):
                return False
            elif op == "in" and actual not in val:
                return False
        else:
            if actual != expected:
                return False
    return True


def render_template(event_type: str, payload: dict) -> tuple[str, str, str]:
    """Render notification title and body from template + payload."""
    template = TEMPLATES.get(event_type, {
        "title": event_type.replace(".", " ").title(),
        "body": str(payload),
        "priority": "normal",
    })

    title = template["title"]
    body = template["body"]
    priority = template.get("priority", "normal")

    try:
        body = body.format(**payload)
    except (KeyError, IndexError):
        pass

    return title, body, priority


async def dispatch_notification(
    db: AsyncSession,
    tenant_id: UUID,
    user_id: UUID,
    event_type: str,
    payload: dict,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    action_url: Optional[str] = None,
) -> Notification:
    """Create a notification from an event."""
    title, body, priority = render_template(event_type, payload)

    notification = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        type=event_type,
        title=title,
        body=body,
        channel="in_app",
        priority=priority,
        entity_type=entity_type,
        entity_id=entity_id,
        action_url=action_url,
    )
    db.add(notification)
    await db.flush()

    logger.info(
        "notification_dispatched",
        user_id=str(user_id),
        event_type=event_type,
        priority=priority,
    )
    return notification


async def process_event(
    db: AsyncSession,
    tenant_id: UUID,
    event_type: str,
    payload: dict,
    target_user_ids: list[UUID],
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
) -> list[Notification]:
    """Process a domain event: evaluate rules and dispatch notifications."""
    rules = await evaluate_rules(db, tenant_id, event_type, payload)

    # If no rules match, use default behavior (always notify)
    notifications = []
    for user_id in target_user_ids:
        notif = await dispatch_notification(
            db, tenant_id, user_id, event_type, payload,
            entity_type=entity_type, entity_id=entity_id,
        )
        notifications.append(notif)

    return notifications
