# -----------------------------------------------------------------------------
# Export worker: consumes report.export requests and generates CSV/Excel.
# Uses queue so heavy export never runs inside the API.
# -----------------------------------------------------------------------------
import asyncio
import json
import os
import sys
import time
import threading
import uuid
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosed
import structlog

logger = structlog.get_logger()

_consumer_running = threading.Event()
_consumer_running.set()

EXPORT_QUEUE = "report.export"


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


async def _generate_report_export(report_id: str, tenant_id: str, format: str) -> bytes:
    """Generate CSV or Excel for a report. Runs in async context."""
    from common.database import AsyncSessionLocal
    from sqlalchemy import select
    from common.models import Expense, ExpenseReport, ExpenseReportItem  # ExpenseReport/Item in common.models

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ExpenseReport).where(
                ExpenseReport.id == report_id,
                ExpenseReport.tenant_id == tenant_id,
                ExpenseReport.deleted_at.is_(None),
            )
        )
        report = result.scalar_one_or_none()
        if not report:
            raise ValueError(f"Report {report_id} not found")

        items_result = await db.execute(
            select(ExpenseReportItem.expense_id).where(
                ExpenseReportItem.expense_report_id == report_id
            )
        )
        expense_ids = [row[0] for row in items_result.all()]
        if not expense_ids:
            return b""

        expenses_result = await db.execute(
            select(Expense).where(
                Expense.id.in_(expense_ids),
                Expense.tenant_id == tenant_id,
                Expense.deleted_at.is_(None),
            )
        )
        expenses = expenses_result.scalars().all()

    if format == "csv":
        import csv
        buf = BytesIO()
        writer = csv.writer(buf)
        writer.writerow(["Date", "Merchant", "Category", "Description", "Amount", "Currency", "VAT Amount", "VAT Rate", "Status"])
        for e in expenses:
            writer.writerow([
                e.expense_date.isoformat() if e.expense_date else "",
                e.merchant_name or "",
                e.category or "",
                e.description or "",
                str(e.amount or ""),
                e.currency or "EUR",
                str(e.vat_amount or ""),
                str(e.vat_rate or ""),
                e.status or "",
            ])
        return buf.getvalue()

    if format == "xlsx":
        try:
            import openpyxl
        except ImportError:
            import csv
            buf = BytesIO()
            writer = csv.writer(buf)
            writer.writerow(["Date", "Merchant", "Category", "Description", "Amount", "Currency", "VAT Amount", "VAT Rate", "Status"])
            for e in expenses:
                writer.writerow([
                    e.expense_date.isoformat() if e.expense_date else "",
                    e.merchant_name or "",
                    e.category or "",
                    e.description or "",
                    str(e.amount or ""),
                    e.currency or "EUR",
                    str(e.vat_amount or ""),
                    str(e.vat_rate or ""),
                    e.status or "",
                ])
            return buf.getvalue()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Expenses"
        headers = ["Date", "Merchant", "Category", "Description", "Amount", "Currency", "VAT Amount", "VAT Rate", "Status"]
        ws.append(headers)
        for e in expenses:
            ws.append([
                e.expense_date.isoformat() if e.expense_date else "",
                e.merchant_name or "",
                e.category or "",
                e.description or "",
                float(e.amount) if e.amount is not None else "",
                e.currency or "EUR",
                float(e.vat_amount) if e.vat_amount is not None else "",
                float(e.vat_rate) if e.vat_rate is not None else "",
                e.status or "",
            ])
        out = BytesIO()
        wb.save(out)
        return out.getvalue()

    raise ValueError(f"Unsupported format: {format}")


def _process_export_message(body: bytes):
    msg = json.loads(body.decode("utf-8"))
    report_id = msg.get("report_id")
    tenant_id = msg.get("tenant_id")
    format_type = (msg.get("format") or "csv").lower()
    if not report_id or not tenant_id:
        raise ValueError("report_id and tenant_id required")
    asyncio.run(_generate_report_export(report_id, tenant_id, format_type))
    # In a full implementation we would store the result (e.g. to MinIO) and notify
    logger.info("export_generated", report_id=report_id, format=format_type)


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
            channel.queue_declare(queue=EXPORT_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                try:
                    _process_export_message(body)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error("export_worker_failed", error=str(e), exc_info=True)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue=EXPORT_QUEUE, on_message_callback=callback)
            logger.info("export_worker_started", queue=EXPORT_QUEUE)
            retry_count = 0
            channel.start_consuming()
        except (AMQPConnectionError, ConnectionClosed, AMQPChannelError) as e:
            retry_count += 1
            logger.warning("export_worker_connection_error", error=str(e), retry_count=retry_count)
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
            logger.info("export_worker_stopped")
            break
        except Exception as e:
            retry_count += 1
            logger.error("export_worker_error", error=str(e), exc_info=True)
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

    logger.warning("export_worker_exiting", retry_count=retry_count)


if __name__ == "__main__":
    run_consumer()
