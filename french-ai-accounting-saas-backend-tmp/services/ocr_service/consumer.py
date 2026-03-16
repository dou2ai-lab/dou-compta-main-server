# -----------------------------------------------------------------------------
# File: consumer.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Message queue consumer for OCR service to process receipt.uploaded events
# -----------------------------------------------------------------------------

"""
Message Queue Consumer for OCR Service
Consumes receipt.uploaded events
"""
import asyncio
import json
import structlog
from typing import Dict
import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosed
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .config import settings
from .service import OCRService
from .provider import OCRProvider
from .normalizer import DataNormalizer
from .events import EventPublisher
from common.database import AsyncSessionLocal
from services.file_service.storage import StorageService

logger = structlog.get_logger()

# Use thread pool executor to run async code in isolated threads
# This prevents event loop conflicts with database connections
_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="ocr_consumer")

# Global flag to control consumer lifecycle
_consumer_running = threading.Event()
_consumer_running.set()

def _create_connection():
    """Create RabbitMQ connection with retry logic"""
    import urllib.parse
    # Support both MESSAGE_QUEUE_URL and RABBITMQ_URL env vars
    queue_url = settings.MESSAGE_QUEUE_URL or settings.RABBITMQ_URL or "amqp://localhost:5672"
    parsed = urllib.parse.urlparse(queue_url)
    # Default to RabbitMQ's standard dev credentials if none provided in URL
    credentials = pika.PlainCredentials(parsed.username or 'guest', parsed.password or 'guest')
    # Handle virtual host: if path is '/' or empty, use '/', otherwise use path without leading slash
    vhost = parsed.path[1:] if parsed.path and len(parsed.path) > 1 else '/'
    parameters = pika.ConnectionParameters(
        host=parsed.hostname or 'localhost',
        port=parsed.port or 5672,
        virtual_host=vhost,
        credentials=credentials,
        heartbeat=600,  # 10 minutes heartbeat
        blocked_connection_timeout=300,  # 5 minutes timeout
        connection_attempts=3,
        retry_delay=2
    )
    return pika.BlockingConnection(parameters)

def start_consumer():
    """Start consuming messages from queue (runs in background thread)"""
    logger.info("ocr_consumer_starting", provider=settings.MESSAGE_QUEUE_PROVIDER)
    
    if settings.MESSAGE_QUEUE_PROVIDER == "rabbitmq":
        retry_count = 0
        max_retries = 10
        retry_delay = 5  # seconds
        
        while _consumer_running.is_set() and retry_count < max_retries:
            connection = None
            channel = None
            try:
                connection = _create_connection()
                channel = connection.channel()
                
                # Declare queue
                channel.queue_declare(queue='receipt.uploaded', durable=True)
                
                def callback(ch, method, properties, body):
                    """Process message"""
                    event = None
                    receipt_id = 'unknown'
                    try:
                        event = json.loads(body.decode('utf-8'))
                        receipt_id = event.get("receipt_id", "unknown")
                        logger.info("message_received", receipt_id=receipt_id)
                        
                        # Run async code in a thread pool executor to avoid event loop conflicts
                        # Each thread gets its own event loop, ensuring database connections work correctly
                        future = _executor.submit(
                            lambda: asyncio.run(process_receipt_uploaded(event))
                        )
                        future.result(timeout=300)  # 5 minute timeout for processing
                        
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except asyncio.TimeoutError:
                        logger.error("message_processing_timeout", receipt_id=receipt_id)
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    except Exception as e:
                        logger.error("message_processing_failed", error=str(e), receipt_id=receipt_id, exc_info=True)
                        # Don't requeue if we've tried too many times or if it's a permanent error
                        should_requeue = not isinstance(e, (ValueError, TypeError))
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=should_requeue)
                
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(queue='receipt.uploaded', on_message_callback=callback)
                
                logger.info("ocr_consumer_started", queue="receipt.uploaded")
                retry_count = 0  # Reset retry count on successful connection
                
                # Start consuming (blocking call)
                channel.start_consuming()
                
            except (AMQPConnectionError, ConnectionClosed, AMQPChannelError) as e:
                retry_count += 1
                logger.warning("rabbitmq_connection_error", error=str(e), retry_count=retry_count, exc_info=True)
                
                # Clean up connection
                try:
                    if channel and not channel.is_closed:
                        channel.close()
                    if connection and not connection.is_closed:
                        connection.close()
                except Exception:
                    pass
                
                if retry_count < max_retries and _consumer_running.is_set():
                    logger.info("retrying_connection", delay=retry_delay, retry_count=retry_count)
                    time.sleep(retry_delay)
                else:
                    logger.error("max_retries_reached", max_retries=max_retries)
                    break
                    
            except KeyboardInterrupt:
                logger.info("consumer_stopped_by_user")
                break
            except Exception as e:
                logger.error("consumer_unexpected_error", error=str(e), exc_info=True)
                retry_count += 1
                if retry_count < max_retries and _consumer_running.is_set():
                    time.sleep(retry_delay)
                else:
                    break
            finally:
                # Clean up connection
                try:
                    if channel and not channel.is_closed:
                        channel.close()
                    if connection and not connection.is_closed:
                        connection.close()
                except Exception:
                    pass
        
        logger.warning("ocr_consumer_exiting", provider=settings.MESSAGE_QUEUE_PROVIDER)
    else:
        logger.warning("message_queue_provider_not_configured", provider=settings.MESSAGE_QUEUE_PROVIDER)

async def process_receipt_uploaded(event: Dict):
    """
    Process receipt.uploaded event
    
    Args:
        event: Event payload from message queue
    """
    try:
        logger.info("processing_receipt_uploaded", receipt_id=event.get("receipt_id"))
        
        # Initialize services - use context manager for proper cleanup
        async with AsyncSessionLocal() as db:
            try:
                from .provider import get_ocr_provider
                from services.file_service.encryption import EncryptionService
                storage = StorageService()
                provider = get_ocr_provider()
                normalizer = DataNormalizer()
                events = EventPublisher()
                encryption = EncryptionService()  # Initialize encryption service for decryption
                
                ocr_service = OCRService(db, storage, provider, normalizer, events, encryption)
                await ocr_service.process_receipt(event)
                # Note: OCRService.process_receipt() already commits, so we don't commit again
            except Exception as db_error:
                await db.rollback()
                logger.error("database_operation_failed", error=str(db_error), receipt_id=event.get("receipt_id"), exc_info=True)
                raise
            finally:
                # Ensure session is closed
                await db.close()
            
    except Exception as e:
        logger.error("event_processing_failed", error=str(e), exc_info=True)
        # TODO: Send to DLQ









