# -----------------------------------------------------------------------------
# File: events.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Event publisher for OCR service to publish OCR processing events to message queue
# -----------------------------------------------------------------------------

"""
Event Publisher for OCR Service
Publishes OCR events
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
        if self.provider == "rabbitmq":
            try:
                import urllib.parse
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
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                # Declare queues
                self.channel.queue_declare(queue='receipt.ocr.started', durable=True)
                self.channel.queue_declare(queue='receipt.ocr.completed', durable=True)
                self.channel.queue_declare(queue='receipt.ocr.failed', durable=True)
                logger.info("rabbitmq_connection_established")
            except AMQPConnectionError as e:
                logger.warning("rabbitmq_connection_failed", error=str(e))
                self.connection = None
                self.channel = None
    
    async def publish_ocr_started(
        self,
        receipt_id: str,
        tenant_id: str,
        user_id: str,
        job_id: str
    ):
        """Publish receipt.ocr.started event"""
        event = {
            "event_type": "receipt.ocr.started",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "receipt_id": receipt_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "payload": {
                "job_id": job_id,
                "provider": settings.OCR_PROVIDER
            },
            "idempotency_key": str(uuid.uuid4())
        }
        
        # Publish to message queue
        try:
            if self.provider == "rabbitmq" and self.channel:
                self.channel.basic_publish(
                    exchange='',
                    routing_key='receipt.ocr.started',
                    body=json.dumps(event),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                logger.info("event_published", event_type="receipt.ocr.started", job_id=job_id)
            else:
                logger.info("event_logged_only", event_type="receipt.ocr.started", job_id=job_id, event=event)
        except Exception as e:
            logger.error("event_publish_failed", error=str(e), event_type="receipt.ocr.started", job_id=job_id)
    
    async def publish_ocr_completed(
        self,
        receipt_id: str,
        tenant_id: str,
        user_id: str,
        job_id: str,
        extracted_data: Dict
    ):
        """Publish receipt.ocr.completed event"""
        event = {
            "event_type": "receipt.ocr.completed",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "receipt_id": receipt_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "payload": {
                "job_id": job_id,
                "extracted_data": extracted_data
            },
            "idempotency_key": str(uuid.uuid4())
        }
        
        # Publish to message queue
        try:
            if self.provider == "rabbitmq" and self.channel:
                self.channel.basic_publish(
                    exchange='',
                    routing_key='receipt.ocr.completed',
                    body=json.dumps(event),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                logger.info("event_published", event_type="receipt.ocr.completed", job_id=job_id)
            else:
                logger.info("event_logged_only", event_type="receipt.ocr.completed", job_id=job_id, event=event)
        except Exception as e:
            logger.error("event_publish_failed", error=str(e), event_type="receipt.ocr.completed", job_id=job_id)
    
    async def publish_ocr_failed(
        self,
        receipt_id: str,
        tenant_id: str,
        user_id: str,
        job_id: str,
        error: str
    ):
        """Publish receipt.ocr.failed event"""
        event = {
            "event_type": "receipt.ocr.failed",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "receipt_id": receipt_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "payload": {
                "job_id": job_id,
                "error_code": "PROVIDER_ERROR",
                "error_message": error,
                "retry_count": 0
            },
            "idempotency_key": str(uuid.uuid4())
        }
        
        # Publish to message queue
        try:
            if self.provider == "rabbitmq" and self.channel:
                self.channel.basic_publish(
                    exchange='',
                    routing_key='receipt.ocr.failed',
                    body=json.dumps(event),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        content_type='application/json'
                    )
                )
                logger.info("event_published", event_type="receipt.ocr.failed", job_id=job_id)
            else:
                logger.info("event_logged_only", event_type="receipt.ocr.failed", job_id=job_id, event=event)
        except Exception as e:
            logger.error("event_publish_failed", error=str(e), event_type="receipt.ocr.failed", job_id=job_id)









