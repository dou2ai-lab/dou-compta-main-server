# -----------------------------------------------------------------------------
# In-process receipt pipeline when RabbitMQ is not available.
# Runs OCR -> normalize -> LLM extract -> update receipt -> create expense.
# -----------------------------------------------------------------------------
import asyncio
import uuid as uuid_lib
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import attributes
import structlog

from common.database import AsyncSessionLocal
from common.models import Expense
from common.receipt_extraction import extract_from_ocr_text
from .models import ReceiptDocument
from .storage import StorageService
from .encryption import EncryptionService
from .config import settings

logger = structlog.get_logger()


def _extract_from_ocr_text(ocr_text: str) -> dict:
    """Delegate to shared extraction module."""
    return extract_from_ocr_text(ocr_text)

def _log_pipeline_step(step: str, receipt_id: str, error: str = None, extra: dict = None):
    """Log pipeline step for debugging (and optionally to debug.log)."""
    data = {"receipt_id": receipt_id, "step": step}
    if error:
        data["error"] = error
    if extra:
        data.update(extra)
    logger.info("receipt_pipeline_step", **data)
    try:
        import json
        import time
        path = getattr(settings, "DEBUG_LOG_PATH", None) or r"e:\French Accounting SAAS\.cursor\debug.log"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "message": "pipeline_step",
                "data": data,
                "timestamp": int(time.time() * 1000),
            }) + "\n")
    except Exception:
        pass


async def run_receipt_pipeline(
    receipt_id: str,
    tenant_id: str,
    user_id: str,
    file_metadata: dict,
) -> None:
    """
    Run OCR -> normalize -> LLM extract -> save -> create expense.
    Use when message queue is not available.
    """
    _log_pipeline_step("start", receipt_id)
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ReceiptDocument).where(
                    ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                    ReceiptDocument.deleted_at.is_(None),
                )
            )
            receipt = result.scalar_one_or_none()
            if not receipt:
                logger.warning("receipt_not_found", receipt_id=receipt_id)
                return

            storage = StorageService()
            encryption_svc = EncryptionService()

            # Step 1: Download file
            try:
                storage_path = file_metadata.get("storage_path")
                if not storage_path:
                    raise ValueError("file_metadata.storage_path is missing")
                file_content = await storage.download_file(storage_path)
                if not file_content or len(file_content) == 0:
                    raise ValueError("Downloaded file is empty")
                _log_pipeline_step("download_ok", receipt_id, extra={"size": len(file_content)})
            except Exception as e:
                _log_pipeline_step("download_failed", receipt_id, error=str(e))
                raise

            if file_metadata.get("encryption_key_id") and settings.ENCRYPTION_ENABLED:
                try:
                    file_content = await encryption_svc.decrypt(
                        file_content, file_metadata["encryption_key_id"]
                    )
                except Exception as e:
                    logger.error("decrypt_failed", receipt_id=receipt_id, error=str(e))
                    receipt.ocr_status = "failed"
                    if not receipt.meta_data:
                        receipt.meta_data = {}
                    receipt.meta_data["pipeline_error"] = f"Decrypt failed: {e}"
                    attributes.flag_modified(receipt, "meta_data")
                    await db.commit()
                    return

            # Step 2: OCR (convert PDF to image first so Tesseract/Paddle get image bytes)
            try:
                from services.ocr_service.provider import get_ocr_provider
                from services.ocr_service.normalizer import DataNormalizer

                mime_type = file_metadata.get("mime_type") or "image/png"
                ocr_input = file_content
                ocr_mime = mime_type
                if mime_type == "application/pdf":
                    try:
                        from services.ocr_service.worker import _pdf_to_first_image_bytes
                        ocr_input = _pdf_to_first_image_bytes(file_content)
                        ocr_mime = "image/png"
                    except Exception as pdf_err:
                        logger.warning("receipt_pipeline_pdf_to_image_failed", receipt_id=receipt_id, error=str(pdf_err))

                provider = get_ocr_provider()
                normalizer = DataNormalizer()
                ocr_result = await provider.extract(ocr_input, ocr_mime)
                _log_pipeline_step("ocr_ok", receipt_id, extra={
                    "has_text": bool(ocr_result.get("text") or ocr_result.get("ocr_text")),
                    "text_len": len(ocr_result.get("text") or ocr_result.get("ocr_text") or ""),
                })
            except Exception as e:
                _log_pipeline_step("ocr_failed", receipt_id, error=str(e))
                raise

            normalized = await normalizer.normalize(ocr_result)
            ocr_text_raw = ocr_result.get("text") or ocr_result.get("ocr_text") or ""

            # Enrich with regex extraction (fallback when LLM not available)
            if ocr_text_raw and ocr_text_raw.strip():
                extracted = _extract_from_ocr_text(ocr_text_raw)
                for k, v in extracted.items():
                    if v is not None and (normalized.get(k) is None or normalized.get(k) == 0 or normalized.get(k) == ""):
                        normalized[k] = v

            # Update receipt with OCR
            receipt.ocr_status = "completed"
            if not receipt.meta_data:
                receipt.meta_data = {}
            receipt.meta_data["ocr"] = normalized
            attributes.flag_modified(receipt, "meta_data")
            await db.commit()
            await db.refresh(receipt)
            logger.info("ocr_saved", receipt_id=receipt_id)

            ocr_text = normalized.get("text", "") or normalized.get("ocr_text", "")
            if not (ocr_text and ocr_text.strip()):
                logger.warning("no_ocr_text", receipt_id=receipt_id)
                # Still save an empty extraction so frontend can show form for manual entry
                from services.llm_service.schemas import ReceiptExtractionResponse
                empty_extraction = ReceiptExtractionResponse(
                    receipt_id=receipt_id,
                    merchant_name=None,
                    expense_date=None,
                    total_amount=None,
                    currency="EUR",
                    vat_amount=None,
                    vat_rate=None,
                    confidence_scores={},
                )
                result2 = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                receipt2 = result2.scalar_one_or_none()
                if receipt2:
                    if not receipt2.meta_data:
                        receipt2.meta_data = {}
                    receipt2.meta_data["extraction"] = empty_extraction.model_dump(mode="json")
                    attributes.flag_modified(receipt2, "meta_data")
                    await db.commit()
                _log_pipeline_step("extraction_saved_empty", receipt_id)
                return

            # Step 3: LLM extraction (optional - skip if not available)
            extraction = None
            expense = None
            try:
                from services.llm_service.extractor import LLMExtractor
                from services.llm_service.schemas import ReceiptExtractionRequest

                extractor = LLMExtractor()
                req = ReceiptExtractionRequest(
                    ocr_text=ocr_text,
                    receipt_id=receipt_id,
                    tenant_id=tenant_id,
                    language="fr",
                )
                extraction = await extractor.extract(req)
                _log_pipeline_step("llm_ok", receipt_id, extra={"has_extraction": bool(extraction)})
            except Exception as e:
                _log_pipeline_step("llm_failed", receipt_id, error=str(e))
                # Continue without LLM - OCR data is already saved, user can fill form manually

            # Save extraction to receipt if LLM succeeded; merge into ocr so all fields available
            # Fill extraction nulls from OCR (regex fallback) - e.g. date when Gemini misses it
            if extraction:
                result2 = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                receipt2 = result2.scalar_one_or_none()
                if receipt2:
                    if not receipt2.meta_data:
                        receipt2.meta_data = {}
                    ocr_dict = receipt2.meta_data.get("ocr") or {}
                    ext_dict = extraction.model_dump(mode="json")
                    # Fill null/zero extraction fields from OCR (regex fallback)
                    for field in ("expense_date", "merchant_name", "total_amount", "vat_amount", "vat_rate"):
                        ext_val = ext_dict.get(field)
                        ocr_val = ocr_dict.get(field)
                        fill_from_ocr = ocr_val is not None and (
                            ext_val is None or
                            (field in ("total_amount", "vat_amount") and ext_val == 0)
                        )
                        if fill_from_ocr:
                            ext_dict[field] = ocr_val
                    receipt2.meta_data["extraction"] = ext_dict
                    # Merge extraction into ocr so consumers reading only ocr get all fields
                    for k, v in ext_dict.items():
                        if v is not None and k not in ("confidence_scores", "extraction_metadata"):
                            ocr_dict[k] = v
                    receipt2.meta_data["ocr"] = ocr_dict
                    attributes.flag_modified(receipt2, "meta_data")
                    await db.commit()
                logger.info("extraction_saved", receipt_id=receipt_id)

            # Use merged data for expense creation (extraction + OCR fallback)
            merged_date = extraction.expense_date if extraction else None
            merged_amount = extraction.total_amount if extraction else None
            if extraction and receipt2 and receipt2.meta_data:
                ext = receipt2.meta_data.get("extraction") or {}
                if merged_date is None and ext.get("expense_date"):
                    try:
                        merged_date = datetime.strptime(str(ext["expense_date"]), "%Y-%m-%d").date()
                    except (ValueError, TypeError):
                        pass
                if merged_amount is None and ext.get("total_amount") is not None:
                    try:
                        merged_amount = Decimal(str(ext["total_amount"]))
                    except (ValueError, TypeError):
                        pass

            if extraction and merged_amount and merged_date:
                expense = Expense(
                    tenant_id=uuid_lib.UUID(tenant_id),
                    submitted_by=uuid_lib.UUID(user_id),
                    amount=merged_amount,
                    currency=extraction.currency or "EUR",
                    expense_date=merged_date,
                    category=None,
                    description=extraction.description or f"Receipt from {extraction.merchant_name or 'Unknown'}",
                    merchant_name=extraction.merchant_name,
                    vat_amount=extraction.vat_amount,
                    vat_rate=float(extraction.vat_rate) if extraction.vat_rate is not None else None,
                    status="draft",
                    meta_data={
                        "receipt_id": receipt_id,
                        "auto_created": True,
                        "extraction_confidence": extraction.confidence_scores,
                    },
                )
                db.add(expense)
                await db.flush()
                # Link receipt to the auto-created expense
                result_receipt = await db.execute(
                    select(ReceiptDocument).where(
                        ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                        ReceiptDocument.deleted_at.is_(None),
                    )
                )
                rec = result_receipt.scalar_one_or_none()
                if rec:
                    rec.expense_id = expense.id
                    logger.info("receipt_linked_to_expense", receipt_id=receipt_id, expense_id=str(expense.id))
                    await db.commit()
                else:
                    await db.commit()
                logger.info("expense_created", receipt_id=receipt_id, expense_id=str(expense.id))

            # Step 4: Embed receipt into RAG document store so audit QA can retrieve it
            try:
                from services.rag_service.embeddings import EmbeddingsPipeline

                # Re-fetch latest receipt (to get file_name, meta_data)
                result3 = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                rec_for_embed = result3.scalar_one_or_none() or receipt

                ocr_dict = {}
                if rec_for_embed and rec_for_embed.meta_data:
                    ocr_dict = rec_for_embed.meta_data.get("ocr") or {}

                # Build a human-readable content block mixing extraction summary and OCR text
                ocr_text_for_embed = ocr_dict.get("text") or ocr_dict.get("ocr_text") or ocr_text
                title_parts = ["Receipt"]
                if extraction and extraction.merchant_name:
                    title_parts.append(extraction.merchant_name)
                if merged_date:
                    title_parts.append(str(merged_date))
                title = " - ".join(title_parts)

                file_name = getattr(rec_for_embed, "file_name", None) or file_metadata.get("file_name") or "receipt"
                content_lines = [
                    f"Receipt ID: {receipt_id}",
                    f"File name: {file_name}",
                    f"Tenant ID: {tenant_id}",
                ]
                if extraction:
                    content_lines.extend(
                        [
                            f"Merchant: {extraction.merchant_name or 'Unknown'}",
                            f"Date: {merged_date}" if merged_date else "",
                            f"Total amount: {merged_amount} {extraction.currency or 'EUR'}" if merged_amount else "",
                            f"VAT amount: {extraction.vat_amount} at {extraction.vat_rate}%" if extraction.vat_amount is not None else "",
                            f"Description: {extraction.description}" if extraction.description else "",
                        ]
                    )
                content_lines.append("")
                content_lines.append("OCR Text:")
                content_lines.append(ocr_text_for_embed or "")

                content = "\n".join([line for line in content_lines if line is not None])

                metadata = {
                    "receipt_id": receipt_id,
                    "tenant_id": tenant_id,
                    "file_id": str(getattr(rec_for_embed, "file_id", "")) if rec_for_embed else None,
                    "expense_id": str(expense.id) if expense else None,
                    "merchant_name": extraction.merchant_name if extraction else None,
                    "expense_date": str(merged_date) if merged_date else None,
                    "total_amount": float(merged_amount) if merged_amount else None,
                }

                pipeline = EmbeddingsPipeline(db, tenant_id)
                await pipeline.embed_document(
                    document_type="receipt",
                    document_id=receipt_id,
                    title=title,
                    content=content,
                    created_by=user_id,
                    metadata=metadata,
                )
                _log_pipeline_step(
                    "rag_receipt_embedded",
                    receipt_id,
                    extra={"has_extraction": bool(extraction), "has_ocr_text": bool(ocr_text_for_embed)},
                )
            except Exception as e:
                # Never fail the receipt pipeline because RAG embedding failed
                logger.error("embed_receipt_rag_failed", receipt_id=receipt_id, error=str(e))
        _log_pipeline_step("done", receipt_id)
    except Exception as e:
        _log_pipeline_step("pipeline_failed", receipt_id, error=str(e))
        logger.error("receipt_pipeline_failed", receipt_id=receipt_id, error=str(e), exc_info=True)
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(ReceiptDocument).where(ReceiptDocument.id == uuid_lib.UUID(receipt_id))
                )
                r = result.scalar_one_or_none()
                if r:
                    r.ocr_status = "failed"
                    if not r.meta_data:
                        r.meta_data = {}
                    r.meta_data["pipeline_error"] = str(e)
                    attributes.flag_modified(r, "meta_data")
                    await db.commit()
        except Exception:
            pass
