"""
Celery tasks for async receipt processing.

Queue flow:
- upload returns immediately with receipt_id
- celery task runs OCR + LLM pipeline and updates receipt_documents
"""

from __future__ import annotations

import asyncio
import os

from celery import Celery
import structlog

logger = structlog.get_logger()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "doucompta",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)


@celery_app.task(name="file_service.process_receipt")
def process_receipt(receipt_id: str, tenant_id: str, user_id: str, file_metadata: dict) -> None:
    """
    Run async receipt pipeline inside a Celery worker.
    """
    logger.info("celery_receipt_task_started", receipt_id=receipt_id)

    async def _run() -> None:
        from .receipt_pipeline import run_receipt_pipeline
        await run_receipt_pipeline(
            receipt_id=receipt_id,
            tenant_id=tenant_id,
            user_id=user_id,
            file_metadata=file_metadata,
        )

    try:
        asyncio.run(_run())
        logger.info("celery_receipt_task_completed", receipt_id=receipt_id)
    except Exception as e:
        logger.error("celery_receipt_task_failed", receipt_id=receipt_id, error=str(e), exc_info=True)
        raise

