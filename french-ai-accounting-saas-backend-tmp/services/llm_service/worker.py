# -----------------------------------------------------------------------------
# File: worker.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: Background worker for processing OCR completed events and extracting data with LLM
# -----------------------------------------------------------------------------

"""
Background Worker for LLM Service
Processes OCR completed events and extracts structured data
"""
import asyncio
import json
import structlog
from typing import Dict
import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosed
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from .config import settings
from .extractor import LLMExtractor
from .schemas import ReceiptExtractionRequest, ReceiptExtractionResponse
from common.database import AsyncSessionLocal
from services.file_service.models import ReceiptDocument
from services.file_service.storage import StorageService
from sqlalchemy import select
import uuid as uuid_lib

logger = structlog.get_logger()

# Global flag to control worker lifecycle
_worker_running = threading.Event()
_worker_running.set()

def _create_llm_connection():
    """Create RabbitMQ connection with retry logic"""
    import urllib.parse
    queue_url = settings.MESSAGE_QUEUE_URL or settings.RABBITMQ_URL or "amqp://localhost:5672"
    parsed = urllib.parse.urlparse(queue_url)
    credentials = pika.PlainCredentials(parsed.username or 'dou_user', parsed.password or 'dou_password')
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

class LLMWorker:
    """Background worker for LLM extraction"""
    
    def __init__(self):
        self.extractor = LLMExtractor()
        self.storage = StorageService()
        # Use thread pool executor to run async code in isolated threads
        # This prevents event loop conflicts with database connections
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="llm_worker")
    
    def start(self):
        """Start consuming messages from queue"""
        logger.info("llm_worker_starting", provider=settings.MESSAGE_QUEUE_PROVIDER)
        
        if settings.MESSAGE_QUEUE_PROVIDER == "rabbitmq":
            retry_count = 0
            max_retries = 10
            retry_delay = 5  # seconds
            
            while _worker_running.is_set() and retry_count < max_retries:
                connection = None
                channel = None
                try:
                    connection = _create_llm_connection()
                    channel = connection.channel()
                    
                    # Declare queues
                    channel.queue_declare(queue='receipt.ocr.completed', durable=True)
                    channel.queue_declare(queue='receipt.extraction.completed', durable=True)
                    
                    def callback(ch, method, properties, body):
                        """Process OCR completed message"""
                        event = None
                        receipt_id = 'unknown'
                        try:
                            event = json.loads(body.decode('utf-8'))
                            receipt_id = event.get("receipt_id", "unknown")
                            logger.info("ocr_completed_event_received", receipt_id=receipt_id)
                            
                            # Run async code in a thread pool executor to avoid event loop conflicts
                            # Each thread gets its own event loop, ensuring database connections work correctly
                            future = self.executor.submit(
                                lambda: asyncio.run(self.process_ocr_completed(event))
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
                    channel.basic_consume(queue='receipt.ocr.completed', on_message_callback=callback)
                    
                    logger.info("llm_worker_started", queue="receipt.ocr.completed")
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
                    
                    if retry_count < max_retries and _worker_running.is_set():
                        logger.info("retrying_connection", delay=retry_delay, retry_count=retry_count)
                        time.sleep(retry_delay)
                    else:
                        logger.error("max_retries_reached", max_retries=max_retries)
                        break
                        
                except KeyboardInterrupt:
                    logger.info("worker_stopped_by_user")
                    break
                except Exception as e:
                    logger.error("worker_unexpected_error", error=str(e), exc_info=True)
                    retry_count += 1
                    if retry_count < max_retries and _worker_running.is_set():
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
            
            logger.warning("llm_worker_exiting", provider=settings.MESSAGE_QUEUE_PROVIDER)
        else:
            logger.warning("message_queue_provider_not_configured", provider=settings.MESSAGE_QUEUE_PROVIDER)
    
    async def process_ocr_completed(self, event: Dict):
        """
        Process OCR completed event and extract structured data
        
        Args:
            event: OCR completed event from message queue
        """
        receipt_id = None
        tenant_id = None
        user_id = None
        ocr_text = None
        
        try:
            receipt_id = event.get("receipt_id")
            if not receipt_id:
                logger.error("missing_receipt_id_in_event", event=event)
                return
            
            logger.info("processing_ocr_completed", receipt_id=receipt_id, event_keys=list(event.keys()))
            
            # Use a SINGLE database session for the entire operation to avoid event loop issues
            async with AsyncSessionLocal() as db:
                try:
                    # Fetch receipt from database first - this is the source of truth
                    result = await db.execute(
                        select(ReceiptDocument).where(
                            ReceiptDocument.id == uuid_lib.UUID(receipt_id)
                        )
                    )
                    receipt = result.scalar_one_or_none()
                    
                    if not receipt:
                        logger.error("receipt_not_found", receipt_id=receipt_id)
                        return
                    
                    # Get tenant_id from receipt (always available)
                    tenant_id = str(receipt.tenant_id)
                    
                    # Try to get user_id from event, otherwise use tenant_id as fallback (for expense creation)
                    user_id = event.get("user_id")
                    if not user_id:
                        # Try to get from receipt meta_data if stored there
                        if receipt.meta_data and receipt.meta_data.get("uploaded_by"):
                            user_id = receipt.meta_data.get("uploaded_by")
                        else:
                            # Use tenant_id as fallback - we'll handle this in auto-create expense
                            logger.warning("user_id_not_found", receipt_id=receipt_id, message="Will skip auto-create expense if user_id required")
                            user_id = None
                    
                    # Get OCR text from event payload or from receipt meta_data
                    payload = event.get("payload", {})
                    extracted_data = payload.get("extracted_data", {})
                    ocr_text = extracted_data.get("text", "") or extracted_data.get("ocr_text", "")
                    
                    # If OCR text not in event, fetch from receipt meta_data
                    if not ocr_text and receipt.meta_data:
                        ocr_data = receipt.meta_data.get("ocr", {})
                        ocr_text = ocr_data.get("text", "")
                        if ocr_text:
                            logger.info("fetched_ocr_text_from_database", receipt_id=receipt_id)
                    
                    if not ocr_text:
                        logger.warning("no_ocr_text_found", receipt_id=receipt_id)
                        return
                    
                    if not tenant_id:
                        logger.error("tenant_id_not_found", receipt_id=receipt_id)
                        return
                    
                except Exception as fetch_error:
                    await db.rollback()
                    logger.error("error_fetching_receipt_data", error=str(fetch_error), receipt_id=receipt_id, exc_info=True)
                    raise
                finally:
                    await db.close()
            
            # Now we have all the data we need (tenant_id, user_id, ocr_text, receipt_id)
            # All are simple strings/primitives, not database-bound objects
            
            if not ocr_text:
                logger.warning("no_ocr_text_found", receipt_id=receipt_id)
                return
            
            if not tenant_id:
                logger.error("tenant_id_not_found", receipt_id=receipt_id)
                return
            
            logger.info("extraction_ready", receipt_id=receipt_id, tenant_id=tenant_id, has_user_id=bool(user_id), ocr_text_length=len(ocr_text))
            
            # Create extraction request (using primitives only, no db references)
            extraction_request = ReceiptExtractionRequest(
                ocr_text=ocr_text,
                receipt_id=receipt_id,
                tenant_id=tenant_id,
                language="fr"  # Default to French for France
            )
            
            # Perform LLM extraction OUTSIDE the database context to avoid event loop conflicts
            logger.info("starting_llm_extraction", receipt_id=receipt_id)
            extraction_result = await self.extractor.extract(extraction_request)
            logger.info("llm_extraction_completed", receipt_id=receipt_id)
            
            # Now save the extraction result using a NEW database session
            async with AsyncSessionLocal() as db:
                try:
                    # Update receipt document with extraction result
                    result = await db.execute(
                        select(ReceiptDocument).where(
                            ReceiptDocument.id == uuid_lib.UUID(receipt_id)
                        )
                    )
                    receipt = result.scalar_one_or_none()
                    
                    if receipt:
                        # Store extraction result in metadata
                        if not receipt.meta_data:
                            receipt.meta_data = {}
                        receipt.meta_data["extraction"] = extraction_result.model_dump(mode='json')
                        
                        # CRITICAL: Mark JSONB field as modified so SQLAlchemy persists the change
                        from sqlalchemy.orm import attributes
                        attributes.flag_modified(receipt, "meta_data")
                        
                        await db.commit()
                        await db.flush()  # Ensure changes are written immediately
                        
                        logger.info("extraction_saved", receipt_id=receipt_id)
                        
                        # Publish extraction completed event (user_id can be None)
                        if user_id:
                            await self._publish_extraction_completed(
                                receipt_id=receipt_id,
                                tenant_id=tenant_id,
                                user_id=user_id,
                                extraction_result=extraction_result
                            )
                        else:
                            logger.warning("skipping_extraction_event_no_user_id", receipt_id=receipt_id)
                        
                        # Auto-create expense if enabled (only if user_id available)
                        if user_id:
                            await self._auto_create_expense(
                                receipt_id=receipt_id,
                                tenant_id=tenant_id,
                                user_id=user_id,
                                extraction_result=extraction_result,
                                db=db
                            )
                        else:
                            logger.info("skipping_auto_create_no_user_id", receipt_id=receipt_id)
                    else:
                        logger.warning("receipt_not_found", receipt_id=receipt_id)
                except Exception as db_error:
                    await db.rollback()
                    logger.error("database_error_saving_extraction", error=str(db_error), receipt_id=receipt_id, exc_info=True)
                    raise
                finally:
                    await db.close()
            
        except Exception as e:
            logger.error("ocr_processing_failed", error=str(e), exc_info=True)
            # TODO: Send to DLQ
    
    async def _publish_extraction_completed(
        self,
        receipt_id: str,
        tenant_id: str,
        user_id: str,
        extraction_result: ReceiptExtractionResponse
    ):
        """Publish extraction completed event"""
        try:
            import urllib.parse
            from datetime import datetime
            import uuid
            
            queue_url = settings.MESSAGE_QUEUE_URL or settings.RABBITMQ_URL or "amqp://localhost:5672"
            parsed = urllib.parse.urlparse(queue_url)
            credentials = pika.PlainCredentials(parsed.username or 'dou_user', parsed.password or 'dou_password')
            # Handle virtual host: if path is '/' or empty, use '/', otherwise use path without leading slash
            vhost = parsed.path[1:] if parsed.path and len(parsed.path) > 1 else '/'
            parameters = pika.ConnectionParameters(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 5672,
                virtual_host=vhost,
                credentials=credentials
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue='receipt.extraction.completed', durable=True)
            
            # Serialize extraction result with proper date handling
            extraction_dict = extraction_result.model_dump(mode='json')
            
            event = {
                "event_type": "receipt.extraction.completed",
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "receipt_id": receipt_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "payload": extraction_dict,
                "idempotency_key": str(uuid.uuid4())
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='receipt.extraction.completed',
                body=json.dumps(event, default=str),  # Use default=str to handle any remaining non-serializable objects
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            logger.info("extraction_completed_event_published", receipt_id=receipt_id)
        except Exception as e:
            logger.error("extraction_event_publish_failed", error=str(e), receipt_id=receipt_id)
        finally:
            # Clean up connection
            try:
                if 'channel' in locals() and channel and not channel.is_closed:
                    channel.close()
                if 'connection' in locals() and connection and not connection.is_closed:
                    connection.close()
            except Exception:
                pass
    
    async def _auto_create_expense(
        self,
        receipt_id: str,
        tenant_id: str,
        user_id: str,
        extraction_result: ReceiptExtractionResponse,
        db
    ):
        """Auto-create expense from extracted data"""
        try:
            # Only create if we have minimum required fields
            if not extraction_result.total_amount or not extraction_result.expense_date:
                logger.info("insufficient_data_for_auto_create", receipt_id=receipt_id)
                return
            
            from common.models import Expense
            from datetime import datetime
            
            # Create expense
            expense = Expense(
                tenant_id=uuid_lib.UUID(tenant_id),
                submitted_by=uuid_lib.UUID(user_id),
                amount=extraction_result.total_amount,
                currency=extraction_result.currency,
                expense_date=extraction_result.expense_date,
                category=None,  # Will be suggested by category service
                description=f"Receipt from {extraction_result.merchant_name or 'Unknown merchant'}",
                merchant_name=extraction_result.merchant_name,
                vat_amount=extraction_result.vat_amount,
                vat_rate=extraction_result.vat_rate,
                status="draft",
                meta_data={
                    "receipt_id": receipt_id,
                    "auto_created": True,
                    "extraction_confidence": extraction_result.confidence_scores
                }
            )
            
            db.add(expense)
            await db.flush()
            await db.commit()
            
            logger.info("expense_auto_created", expense_id=str(expense.id), receipt_id=receipt_id)
            
        except Exception as e:
            logger.error("expense_auto_create_failed", error=str(e), receipt_id=receipt_id, exc_info=True)
            await db.rollback()

def start_worker():
    """Start the LLM worker"""
    try:
        logger.info("llm_worker_process_starting")
        worker = LLMWorker()
        logger.info("llm_worker_instance_created")
        worker.start()
    except KeyboardInterrupt:
        logger.info("llm_worker_stopped_by_user")
        _worker_running.clear()
    except Exception as e:
        logger.error("llm_worker_failed_to_start", error=str(e), exc_info=True)
        raise

if __name__ == "__main__":
    start_worker()

