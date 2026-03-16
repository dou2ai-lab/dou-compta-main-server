# -----------------------------------------------------------------------------
# Receipt worker: consumes receipt.uploaded from RabbitMQ and runs full pipeline
# (OCR -> extraction -> draft expense). Heavy processing stays out of the API.
# -----------------------------------------------------------------------------
import asyncio
import json
import os
import sys
import time
import threading

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosed
import structlog

logger = structlog.get_logger()

_consumer_running = threading.Event()
_consumer_running.set()


def _create_connection():
    queue_url = os.environ.get("MESSAGE_QUEUE_URL") or os.environ.get("RABBITMQ_URL") or "amqp://guest:guest@localhost:5672/"
    import urllib.parse
    parsed = urllib.parse.urlparse(queue_url)
    credentials = pika.PlainCredentials(parsed.username or "guest", parsed.password or "guest")
    vhost = parsed.path[1:] if parsed.path and len(parsed.path) > 1 else "/"
    parameters = pika.ConnectionParameters(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5672,
        virtual_host=vhost,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
        connection_attempts=5,
        retry_delay=2,
    )
    return pika.BlockingConnection(parameters)


def _process_message(body: bytes):
    """Run full receipt pipeline (OCR + extraction + draft expense) in a new event loop."""
    event = json.loads(body.decode("utf-8"))
    receipt_id = event.get("receipt_id")
    tenant_id = event.get("tenant_id")
    user_id = event.get("user_id")
    payload = event.get("payload") or {}
    if not receipt_id or not tenant_id or not user_id:
        raise ValueError("receipt_id, tenant_id, user_id required")
    file_metadata = {
        "storage_path": payload.get("storage_path"),
        "mime_type": payload.get("mime_type") or "image/png",
        "file_id": payload.get("file_id"),
        "file_name": payload.get("file_name"),
        "encryption_key_id": payload.get("encryption_key_id"),
    }
    from services.file_service.receipt_pipeline import run_receipt_pipeline
    asyncio.run(
        run_receipt_pipeline(
            receipt_id=receipt_id,
            tenant_id=tenant_id,
            user_id=user_id,
            file_metadata=file_metadata,
        )
    )


def run_consumer():
    retry_count = 0
    max_retries = 30
    retry_delay = 5

    while _consumer_running.is_set() and retry_count < max_retries:
        connection = None
        channel = None
        try:
            connection = _create_connection()
            channel = connection.channel()
            channel.queue_declare(queue="receipt.uploaded", durable=True)
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                receipt_id = "unknown"
                try:
                    event = json.loads(body.decode("utf-8"))
                    receipt_id = event.get("receipt_id", "unknown")
                    logger.info("receipt_worker_message_received", receipt_id=receipt_id)
                    _process_message(body)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except asyncio.TimeoutError:
                    logger.error("receipt_worker_timeout", receipt_id=receipt_id)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                except Exception as e:
                    logger.error("receipt_worker_failed", receipt_id=receipt_id, error=str(e), exc_info=True)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue="receipt.uploaded", on_message_callback=callback)
            logger.info("receipt_worker_started", queue="receipt.uploaded")
            retry_count = 0
            channel.start_consuming()
        except (AMQPConnectionError, ConnectionClosed, AMQPChannelError) as e:
            retry_count += 1
            logger.warning("receipt_worker_connection_error", error=str(e), retry_count=retry_count)
            try:
                if channel and not channel.is_closed:
                    channel.close()
                if connection and not connection.is_closed:
                    connection.close()
            except Exception:
                pass
            if retry_count < max_retries and _consumer_running.is_set():
                time.sleep(retry_delay)
            else:
                break
        except KeyboardInterrupt:
            logger.info("receipt_worker_stopped")
            break
        except Exception as e:
            retry_count += 1
            logger.error("receipt_worker_error", error=str(e), exc_info=True)
            try:
                if channel and not channel.is_closed:
                    channel.close()
                if connection and not connection.is_closed:
                    connection.close()
            except Exception:
                pass
            if retry_count < max_retries:
                time.sleep(retry_delay)
            else:
                break

    logger.warning("receipt_worker_exiting", retry_count=retry_count)


if __name__ == "__main__":
    run_consumer()
