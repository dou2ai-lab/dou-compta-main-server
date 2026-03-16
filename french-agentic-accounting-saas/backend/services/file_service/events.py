# -----------------------------------------------------------------------------
# File: events.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Event publisher for file service to publish receipt.uploaded events to message queue
# -----------------------------------------------------------------------------

"""
Event Publisher for File Service
Publishes receipt.uploaded events
"""
import uuid
import json
from datetime import datetime
from typing import Dict
import structlog
import pika
from pika.exceptions import AMQPConnectionError

from .config import settings

logger = structlog.get_logger()

class EventPublisher:
    """Publishes events to message queue"""
    
    def __init__(self):
        self.provider = settings.MESSAGE_QUEUE_PROVIDER
        # Support both MESSAGE_QUEUE_URL and RABBITMQ_URL env vars
        self.queue_url = settings.MESSAGE_QUEUE_URL or settings.RABBITMQ_URL or "amqp://localhost:5672"
        self.connection = None
        self.channel = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize RabbitMQ connection"""
        try:
            if self.provider == "rabbitmq":
                # Parse connection URL
                import urllib.parse
                logger.info("initializing_rabbitmq", queue_url=self.queue_url)
                parsed = urllib.parse.urlparse(self.queue_url)
                # Default to RabbitMQ's standard dev credentials if none provided in URL
                credentials = pika.PlainCredentials(parsed.username or 'guest', parsed.password or 'guest')
                # Handle virtual host: if path is '/' or empty, use '/', otherwise use path without leading slash
                vhost = parsed.path[1:] if parsed.path and len(parsed.path) > 1 else '/'
                parameters = pika.ConnectionParameters(
                    host=parsed.hostname or 'localhost',
                    port=parsed.port or 5672,
                    virtual_host=vhost,
                    credentials=credentials
                )
                logger.info("connecting_to_rabbitmq", host=parsed.hostname, port=parsed.port, vhost=vhost)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                # Declare queue
                self.channel.queue_declare(queue='receipt.uploaded', durable=True)
                logger.info("rabbitmq_connection_established", queue="receipt.uploaded")
        except AMQPConnectionError as e:
            logger.warning("rabbitmq_connection_failed", error=str(e), exc_info=True, msg="Events will be logged only")
            self.connection = None
            self.channel = None
        except Exception as e:
            logger.warning("message_queue_init_failed", error=str(e), exc_info=True, msg="Events will be logged only")
            self.connection = None
            self.channel = None
    
    async def publish_receipt_uploaded(
        self,
        receipt_id: str,
        tenant_id: str,
        user_id: str,
        file_metadata: Dict
    ):
        """
        Publish receipt.uploaded event
        
        Event payload:
        {
            "event_type": "receipt.uploaded",
            "event_id": "uuid",
            "timestamp": "ISO8601",
            "receipt_id": "uuid",
            "tenant_id": "uuid",
            "user_id": "uuid",
            "payload": {
                "file_id": "uuid",
                "file_name": "...",
                "mime_type": "...",
                "file_size": 1024,
                "storage_path": "s3://...",
                "encryption_key_id": "uuid"
            },
            "idempotency_key": "uuid"
        }
        """
        event = {
            "event_type": "receipt.uploaded",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "receipt_id": receipt_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "payload": file_metadata,
            "idempotency_key": str(uuid.uuid4())
        }
        
        # Publish to message queue
        try:
            if self.provider == "rabbitmq" and self.channel:
                self.channel.basic_publish(
                    exchange='',
                    routing_key='receipt.uploaded',
                    body=json.dumps(event),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make message persistent
                        content_type='application/json'
                    )
                )
                logger.info("event_published", event_type="receipt.uploaded", receipt_id=receipt_id)
            else:
                # Fallback: just log the event
                logger.info("event_logged_only", event_type="receipt.uploaded", receipt_id=receipt_id, event=event)
        except Exception as e:
            logger.error("event_publish_failed", error=str(e), event_type="receipt.uploaded", receipt_id=receipt_id)
            # Don't fail the upload if event publishing fails









