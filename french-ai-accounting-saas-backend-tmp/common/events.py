"""
Domain Event Bus for DouCompta.
Provides pub/sub pattern using RabbitMQ for inter-service communication.
Events: expense.approved, entry.created, declaration.due, anomaly.detected, etc.
"""
import json
import os
import structlog
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4, UUID
from dataclasses import dataclass, field, asdict
import pika

logger = structlog.get_logger()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_NAME = "doucompta.events"


@dataclass
class DomainEvent:
    event_type: str
    aggregate_type: str
    aggregate_id: str
    tenant_id: str
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, data: str) -> "DomainEvent":
        d = json.loads(data)
        return cls(**d)


def _get_connection() -> Optional[pika.BlockingConnection]:
    """Get RabbitMQ connection. Returns None if unavailable."""
    try:
        params = pika.URLParameters(RABBITMQ_URL)
        params.connection_attempts = 3
        params.retry_delay = 2
        return pika.BlockingConnection(params)
    except Exception as e:
        logger.warning("rabbitmq_connection_failed", error=str(e))
        return None


def _ensure_exchange(channel):
    """Declare the topic exchange."""
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="topic",
        durable=True,
    )


def publish_event(event: DomainEvent) -> bool:
    """
    Publish a domain event to RabbitMQ.
    Returns True if published, False if RabbitMQ unavailable.
    """
    connection = _get_connection()
    if not connection:
        logger.warning("event_not_published_no_rabbitmq", event_type=event.event_type)
        return False

    try:
        channel = connection.channel()
        _ensure_exchange(channel)
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=event.event_type,
            body=event.to_json(),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type="application/json",
                message_id=event.event_id,
                timestamp=int(datetime.now(timezone.utc).timestamp()),
            ),
        )
        logger.info("event_published", event_type=event.event_type, event_id=event.event_id)
        return True
    except Exception as e:
        logger.error("event_publish_failed", event_type=event.event_type, error=str(e))
        return False
    finally:
        try:
            connection.close()
        except Exception:
            pass


async def store_event(db, event: DomainEvent) -> None:
    """Store domain event in the database for audit trail."""
    from sqlalchemy import text
    await db.execute(
        text("""
            INSERT INTO domain_events (id, tenant_id, event_type, aggregate_type, aggregate_id, payload, status)
            VALUES (:id, :tenant_id, :event_type, :aggregate_type, :aggregate_id, :payload, 'published')
        """),
        {
            "id": event.event_id,
            "tenant_id": event.tenant_id,
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "payload": json.dumps(event.payload),
        },
    )


def subscribe(event_type: str, queue_name: str, callback: Callable):
    """
    Subscribe to domain events. Blocking call - run in a worker process.
    event_type supports wildcards: 'expense.*', '*.approved', '#'
    """
    connection = _get_connection()
    if not connection:
        raise ConnectionError("Cannot connect to RabbitMQ")

    channel = connection.channel()
    _ensure_exchange(channel)
    channel.queue_declare(queue=queue_name, durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=event_type)

    def on_message(ch, method, properties, body):
        try:
            event = DomainEvent.from_json(body.decode("utf-8"))
            callback(event)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error("event_handler_failed", error=str(e), event_type=event_type)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_message)
    logger.info("event_subscriber_started", queue=queue_name, event_type=event_type)
    channel.start_consuming()


# Convenience functions for common events

def emit_expense_approved(tenant_id: str, expense_id: str, amount: str, category: str, approved_by: str) -> bool:
    return publish_event(DomainEvent(
        event_type="expense.approved",
        aggregate_type="expense",
        aggregate_id=expense_id,
        tenant_id=tenant_id,
        payload={"amount": amount, "category": category, "approved_by": approved_by},
    ))

def emit_entry_created(tenant_id: str, entry_id: str, entry_number: str, journal_code: str) -> bool:
    return publish_event(DomainEvent(
        event_type="entry.created",
        aggregate_type="journal_entry",
        aggregate_id=entry_id,
        tenant_id=tenant_id,
        payload={"entry_number": entry_number, "journal_code": journal_code},
    ))

def emit_declaration_due(tenant_id: str, declaration_type: str, due_date: str, dossier_id: str) -> bool:
    return publish_event(DomainEvent(
        event_type="declaration.due",
        aggregate_type="declaration",
        aggregate_id=dossier_id,
        tenant_id=tenant_id,
        payload={"declaration_type": declaration_type, "due_date": due_date},
    ))

def emit_anomaly_detected(tenant_id: str, entity_type: str, entity_id: str, risk_score: float, reasons: list) -> bool:
    return publish_event(DomainEvent(
        event_type="anomaly.detected",
        aggregate_type=entity_type,
        aggregate_id=entity_id,
        tenant_id=tenant_id,
        payload={"risk_score": risk_score, "reasons": reasons},
    ))
