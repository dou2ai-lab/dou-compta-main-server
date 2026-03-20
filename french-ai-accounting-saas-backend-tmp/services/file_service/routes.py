# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: API routes for file upload, download, and management endpoints
# REBUILT FROM SCRATCH - SIMPLE WORKING VERSION
# -----------------------------------------------------------------------------

"""
File Service Routes - Rebuilt Simple Version
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
import structlog
import uuid
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
import asyncio
import httpx
import os
import json

from .schemas import (
    ReceiptUploadResponse,
    ReceiptStatusResponse,
    ReceiptDownloadResponse,
    ReceiptCorrectionsRequest,
)
from .models import ReceiptDocument
from .storage import StorageService
from .events import EventPublisher
from common.database import get_db
from services.auth.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()

@router.post("/receipts/upload", response_model=ReceiptUploadResponse)
async def upload_receipt(
    file: UploadFile = File(...),
    expense_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Upload a receipt file - SIMPLE WORKING VERSION
    
    Steps:
    1. Validate user and file
    2. Read file content
    3. Save to local storage
    4. Save metadata to database
    5. Return success
    """
    print("\n" + "="*80)
    print("UPLOAD STARTED - ROUTE HIT!")
    print("="*80)
    print(f"File: {file.filename if file else 'None'}")
    print(f"Expense ID: {expense_id}")
    print(f"User: {user.id if user else 'None'}")
    print(f"Tenant: {user.tenant_id if user and hasattr(user, 'tenant_id') else 'None'}")
    
    try:
        # Step 1: Validate
        print(f"Step 1: Validating user...")
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")
        if not user.tenant_id:
            raise HTTPException(status_code=400, detail="User has no tenant")
        
        print(f"  User ID: {user.id}")
        print(f"  Tenant ID: {user.tenant_id}")
        print(f"  File name: {file.filename}")
        print(f"  File type: {file.content_type}")
        
        # Step 2: Read file
        print(f"\nStep 2: Reading file...")
        file_content = await file.read()
        file_size = len(file_content)
        print(f"  File size: {file_size} bytes")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Step 3: Generate IDs
        print(f"\nStep 3: Generating IDs...")
        receipt_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        file_hash = hashlib.sha256(file_content).hexdigest()
        print(f"  Receipt ID: {receipt_id}")
        print(f"  File ID: {file_id}")
        
        # Step 4: Save to storage
        print(f"\nStep 4: Saving to storage...")
        try:
            storage = StorageService()
            print(f"  Storage provider: {storage.provider}")
            
            storage_path = await storage.upload_file(
                file_content=file_content,
                file_id=file_id,
                tenant_id=str(user.tenant_id),
                file_name=file.filename or "receipt"
            )
            print(f"  Storage path: {storage_path}")
        except Exception as e:
            print(f"  ERROR: Storage failed: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Storage failed: {str(e)}")
        
        # Step 5: Save to database
        print(f"\nStep 5: Saving to database...")
        try:
            # Convert expense_id if provided
            expense_uuid = None
            if expense_id:
                try:
                    expense_uuid = uuid.UUID(expense_id)
                except ValueError:
                    print(f"  Warning: Invalid expense_id, ignoring: {expense_id}")
            
            receipt_doc = ReceiptDocument(
                id=uuid.UUID(receipt_id),
                file_id=uuid.UUID(file_id),
                tenant_id=user.tenant_id,
                expense_id=expense_uuid,
                file_name=(file.filename or "receipt")[:255],
                file_size=file_size,
                mime_type=file.content_type,
                storage_path=storage_path[:500],
                encryption_key_id=None,
                file_hash=file_hash,
                upload_status="completed",
                ocr_status="pending",
                meta_data={}
            )
            
            print(f"  Adding to database session...")
            db.add(receipt_doc)
            
            print(f"  Flushing...")
            await db.flush()
            
            print(f"  Committing...")
            await db.commit()
            
            print(f"  Refreshing...")
            await db.refresh(receipt_doc)
            
            print(f"  Success! Receipt saved with ID: {receipt_doc.id}")
            
        except Exception as e:
            print(f"  ERROR: Database save failed: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            await db.rollback()
            
            # More detailed error info
            error_detail = str(e)
            if hasattr(e, 'orig'):
                error_detail += f" (Original: {e.orig})"
            if hasattr(e, 'statement'):
                error_detail += f" (SQL: {e.statement})"
            
            raise HTTPException(status_code=500, detail=f"Database save failed: {error_detail}")
        
        # Step 6: Return response
        print(f"\nStep 6: Preparing response...")
        uploaded_at = receipt_doc.created_at.isoformat() if receipt_doc.created_at else datetime.utcnow().isoformat()
        
        # Step 6.5: Publish event to trigger OCR processing (RabbitMQ consumer in ocr-service)
        # Do not fail the upload if publishing fails, but log clearly.
        print(f"\nStep 6.5: Publishing receipt.uploaded event...")
        event_payload = {
            "receipt_id": receipt_id,
            "tenant_id": str(user.tenant_id),
            "user_id": str(user.id),
            "payload": {
                "file_id": file_id,
                "file_name": file.filename,
                "mime_type": file.content_type,
                "file_size": file_size,
                "storage_path": storage_path,
                "encryption_key_id": None,
                "expense_id": str(expense_uuid) if expense_uuid else None,
            },
            "idempotency_key": str(uuid.uuid4()),
        }
        try:
            publisher = EventPublisher()
            await publisher.publish_receipt_uploaded(
                receipt_id=receipt_id,
                tenant_id=str(user.tenant_id),
                user_id=str(user.id),
                file_metadata={
                    "file_id": file_id,
                    "file_name": file.filename,
                    "mime_type": file.content_type,
                    "file_size": file_size,
                    "storage_path": storage_path,
                    "encryption_key_id": None,
                    "expense_id": str(expense_uuid) if expense_uuid else None,
                },
            )
            print("  Event published (or logged if MQ unavailable)")
        except Exception as e:
            print(f"  WARNING: Event publish failed: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())

        # Step 6.6: Run OCR in-process (avoids need for separate OCR service / RabbitMQ)
        # Capture values for this upload so the task uses this receipt's data (closure bug fix:
        # without this, multiple uploads can cause all tasks to use the latest upload's receipt_id/file.)
        _receipt_id = receipt_id
        _tenant_id = str(user.tenant_id)
        _user_id = str(user.id)
        _file_meta = {
            "storage_path": storage_path,
            "mime_type": file.content_type or "application/octet-stream",
            "file_id": file_id,
            "file_name": file.filename or "receipt",
        }

        async def _run_ocr_in_process():
            try:
                from .receipt_pipeline import run_receipt_pipeline
                await run_receipt_pipeline(
                    receipt_id=_receipt_id,
                    tenant_id=_tenant_id,
                    user_id=_user_id,
                    file_metadata=_file_meta,
                )
                print(f"  OCR pipeline completed for receipt {_receipt_id}")
            except Exception as e:
                print(f"  WARNING: OCR pipeline failed: {type(e).__name__}: {str(e)}")

        print("\nStep 6.6: Running OCR pipeline in-process...")
        use_queue = os.getenv("USE_QUEUE", "false").strip().lower() in ("1", "true", "yes", "on")
        if use_queue:
            try:
                from .tasks import process_receipt
                process_receipt.delay(_receipt_id, _tenant_id, _user_id, _file_meta)
                print("  Queued background processing via Celery/Redis")
            except Exception as e:
                print(f"  WARNING: Queue enqueue failed, falling back to in-process task: {type(e).__name__}: {str(e)}")
                asyncio.create_task(_run_ocr_in_process())
        else:
            asyncio.create_task(_run_ocr_in_process())

        response = ReceiptUploadResponse(
            receipt_id=receipt_id,
            file_id=file_id,
            status="uploaded",
            ocr_status="pending",
            file_name=file.filename or "receipt",
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_at=uploaded_at,
            expense_id=expense_id
        )
        
        print("="*80)
        print("UPLOAD SUCCESS!")
        print("="*80 + "\n")
        
        return response
        
    except HTTPException:
        print("="*80)
        print("UPLOAD FAILED (HTTPException)")
        print("="*80 + "\n")
        raise
    except Exception as e:
        print("="*80)
        print(f"UPLOAD FAILED: {type(e).__name__}: {str(e)}")
        print(traceback.format_exc())
        print("="*80 + "\n")
        
        logger.error("upload_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {type(e).__name__}: {str(e)}"
        )


@router.post("/receipts/extract")
async def extract_receipt_data(
    file: UploadFile = File(...),
    language: Optional[str] = Query("fr", description="Receipt language for extraction"),
    user=Depends(get_current_user),
):
    """
    Full pipeline: upload file → OCR → document classification → field extraction.
    Returns document_type (invoice|receipt|bank_statement|payslip|other), ocr_text,
    supplier, invoice_number, invoice_date, vat_amount, total_amount, currency, etc.
    """
    try:
        file_content = await file.read()
        if not file_content or len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        mime_type = file.content_type or "image/jpeg"
        from services.llm_service.invoice_pipeline import run_invoice_pipeline
        result = await run_invoice_pipeline(
            file_content=file_content,
            mime_type=mime_type,
            tenant_id=str(getattr(user, "tenant_id", "dev")),
            language=language or "fr",
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("extract_pipeline_failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {type(e).__name__}: {str(e)}",
        )


@router.get("/receipts/{receipt_id}", response_model=ReceiptUploadResponse)
async def get_receipt(
    receipt_id: str,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Get receipt metadata"""
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid.UUID(receipt_id),
                ReceiptDocument.tenant_id == user.tenant_id,
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        return ReceiptUploadResponse(
            receipt_id=str(receipt.id),
            file_id=str(receipt.file_id),
            status=receipt.upload_status,
            ocr_status=receipt.ocr_status,
            file_name=receipt.file_name,
            file_size=receipt.file_size,
            mime_type=receipt.mime_type,
            uploaded_at=receipt.created_at.isoformat() if receipt.created_at else datetime.utcnow().isoformat(),
            expense_id=str(receipt.expense_id) if receipt.expense_id else None,
            meta_data=receipt.meta_data or {}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/receipts/{receipt_id}/status", response_model=ReceiptStatusResponse)
async def get_receipt_status(
    receipt_id: str,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Get receipt upload and OCR status"""
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid.UUID(receipt_id),
                ReceiptDocument.tenant_id == user.tenant_id,
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        return ReceiptStatusResponse(
            receipt_id=str(receipt.id),
            upload_status=receipt.upload_status,
            ocr_status=receipt.ocr_status,
            ocr_job_id=str(receipt.ocr_job_id) if receipt.ocr_job_id else None,
            last_updated=receipt.updated_at.isoformat() if receipt.updated_at else receipt.created_at.isoformat() if receipt.created_at else datetime.utcnow().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/receipts/{receipt_id}/download", response_model=ReceiptDownloadResponse)
async def get_download_url(
    receipt_id: str,
    expires_in: int = Query(3600, ge=60, le=86400),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Get signed URL for downloading receipt file"""
    from sqlalchemy import select
    from .storage import StorageService
    
    try:
        result = await db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid.UUID(receipt_id),
                ReceiptDocument.tenant_id == user.tenant_id,
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        storage = StorageService()
        url = storage.generate_presigned_url(receipt.storage_path, expires_in)
        
        return ReceiptDownloadResponse(
            receipt_id=str(receipt.id),
            download_url=url,
            expires_in=expires_in,
            expires_at=(datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/receipts/{receipt_id}")
async def delete_receipt(
    receipt_id: str,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Delete receipt file and metadata"""
    from sqlalchemy import select
    
    try:
        result = await db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid.UUID(receipt_id),
                ReceiptDocument.tenant_id == user.tenant_id,
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        receipt.deleted_at = datetime.utcnow()
        await db.commit()
        
        return {"success": True, "data": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/receipts/{receipt_id}/corrections")
async def submit_receipt_corrections(
    receipt_id: str,
    payload: ReceiptCorrectionsRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Store user corrections for human-in-the-loop learning + training dataset.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import attributes
    from .models_feedback import ReceiptFieldCorrection, ReceiptTrainingSnapshot

    result = await db.execute(
        select(ReceiptDocument).where(
            ReceiptDocument.id == uuid.UUID(receipt_id),
            ReceiptDocument.tenant_id == user.tenant_id,
            ReceiptDocument.deleted_at.is_(None),
        )
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    meta = receipt.meta_data or {}
    ocr_snapshot = meta.get("ocr")
    llm_snapshot = meta.get("extraction")
    predicted = payload.predicted_extraction or llm_snapshot

    # Store per-field rows: { field, predicted_value, corrected_value }
    corrected = payload.corrected_values or {}
    for field_name, corrected_value in corrected.items():
        predicted_value = predicted.get(field_name) if isinstance(predicted, dict) else None
        row = ReceiptFieldCorrection(
            receipt_id=receipt.id,
            tenant_id=user.tenant_id,
            user_id=user.id,
            field_name=str(field_name),
            predicted_value=predicted_value,
            corrected_value=corrected_value,
            predicted_snapshot=predicted if isinstance(predicted, dict) else None,
            ocr_snapshot=ocr_snapshot if isinstance(ocr_snapshot, dict) else None,
            llm_snapshot=llm_snapshot if isinstance(llm_snapshot, dict) else None,
        )
        db.add(row)

    # Update receipt meta_data with corrected fields (audit trail)
    meta.setdefault("corrections", {})
    meta["corrections"]["corrected_values"] = corrected
    meta["corrections"]["predicted_extraction"] = predicted if isinstance(predicted, dict) else None
    receipt.meta_data = meta
    attributes.flag_modified(receipt, "meta_data")

    # Upsert training snapshot (latest corrected)
    snap = ReceiptTrainingSnapshot(
        receipt_id=receipt.id,
        tenant_id=user.tenant_id,
        user_id=user.id,
        file_hash=receipt.file_hash,
        document_type=(meta.get("document_type") if isinstance(meta, dict) else None),
        ocr_output=ocr_snapshot if isinstance(ocr_snapshot, dict) else None,
        llm_output=llm_snapshot if isinstance(llm_snapshot, dict) else None,
        extraction_output=llm_snapshot if isinstance(llm_snapshot, dict) else None,
        corrected_output=corrected,
    )
    db.add(snap)

    await db.commit()
    return {"success": True, "data": {"receipt_id": receipt_id}}


@router.get("/training/export")
async def export_training_dataset(
    format: str = Query("jsonl", description="Export format: jsonl or csv"),
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Export training dataset rows (tenant-scoped) with:
    - OCR text
    - LLM output
    - corrected output
    """
    from sqlalchemy import select
    from .models_feedback import ReceiptTrainingSnapshot

    q = (
        select(ReceiptTrainingSnapshot)
        .where(ReceiptTrainingSnapshot.tenant_id == user.tenant_id)
        .order_by(ReceiptTrainingSnapshot.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(q)
    rows = res.scalars().all()

    if format.lower() == "jsonl":
        lines = []
        for r in rows:
            ocr = r.ocr_output or {}
            ocr_text = None
            if isinstance(ocr, dict):
                ocr_text = ocr.get("raw_text") or ocr.get("text")
            record = {
                "receipt_id": str(r.receipt_id),
                "document_type": r.document_type,
                "ocr_text": ocr_text,
                "llm_output": r.llm_output,
                "corrected_output": r.corrected_output,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            lines.append(json.dumps(record, ensure_ascii=False))
        body = "\n".join(lines) + ("\n" if lines else "")
        return Response(content=body, media_type="application/jsonl")

    if format.lower() == "csv":
        import csv
        import io

        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["receipt_id", "document_type", "ocr_text", "llm_output_json", "corrected_output_json", "created_at"])
        for r in rows:
            ocr = r.ocr_output or {}
            ocr_text = None
            if isinstance(ocr, dict):
                ocr_text = ocr.get("raw_text") or ocr.get("text")
            w.writerow([
                str(r.receipt_id),
                r.document_type or "",
                (ocr_text or "").replace("\r", " ").replace("\n", "\\n"),
                json.dumps(r.llm_output or {}, ensure_ascii=False),
                json.dumps(r.corrected_output or {}, ensure_ascii=False),
                r.created_at.isoformat() if r.created_at else "",
            ])
        return Response(content=out.getvalue(), media_type="text/csv")

    raise HTTPException(status_code=400, detail="Invalid format. Use jsonl or csv.")


@router.get("/training/eval")
async def evaluate_training_dataset(
    limit: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Compute evaluation metrics from training snapshots:
    - field-level accuracy
    - % correct total_amount
    - % correct expense_date
    """
    from sqlalchemy import select
    from .models_feedback import ReceiptTrainingSnapshot

    res = await db.execute(
        select(ReceiptTrainingSnapshot)
        .where(ReceiptTrainingSnapshot.tenant_id == user.tenant_id)
        .order_by(ReceiptTrainingSnapshot.created_at.desc())
        .limit(limit)
    )
    rows = res.scalars().all()

    def _norm_num(v):
        if v is None:
            return None
        try:
            return round(float(v), 2)
        except (TypeError, ValueError):
            return None

    def _eq_num(a, b, tol=0.02):
        na = _norm_num(a)
        nb = _norm_num(b)
        if na is None or nb is None:
            return False
        return abs(na - nb) <= tol

    def _eq_str(a, b):
        if a is None or b is None:
            return False
        return str(a).strip() == str(b).strip()

    field_counts = {}
    field_correct = {}
    total_amount_correct = 0
    total_amount_count = 0
    expense_date_correct = 0
    expense_date_count = 0

    for r in rows:
        pred = r.extraction_output or r.llm_output or {}
        corr = r.corrected_output or {}
        if not isinstance(pred, dict) or not isinstance(corr, dict):
            continue

        for field, corr_val in corr.items():
            if corr_val is None:
                continue
            field_counts[field] = field_counts.get(field, 0) + 1
            pred_val = pred.get(field)

            ok = False
            if field in ("total_amount", "vat_amount", "vat_rate", "subtotal"):
                ok = _eq_num(pred_val, corr_val)
            else:
                ok = _eq_str(pred_val, corr_val)
            if ok:
                field_correct[field] = field_correct.get(field, 0) + 1

        if "total_amount" in corr and corr.get("total_amount") is not None:
            total_amount_count += 1
            if _eq_num((pred or {}).get("total_amount"), corr.get("total_amount")):
                total_amount_correct += 1

        if "expense_date" in corr and corr.get("expense_date") is not None:
            expense_date_count += 1
            if _eq_str((pred or {}).get("expense_date"), corr.get("expense_date")):
                expense_date_correct += 1

    field_accuracy = {
        f: (field_correct.get(f, 0) / c) if c else 0.0
        for f, c in field_counts.items()
    }

    return {
        "success": True,
        "data": {
            "sample_size": len(rows),
            "field_accuracy": field_accuracy,
            "total_amount_accuracy": (total_amount_correct / total_amount_count) if total_amount_count else None,
            "expense_date_accuracy": (expense_date_correct / expense_date_count) if expense_date_count else None,
            "counts": {
                "total_amount": {"correct": total_amount_correct, "total": total_amount_count},
                "expense_date": {"correct": expense_date_correct, "total": expense_date_count},
            },
        },
        "error": None,
        "meta": {},
    }


@router.get("/metrics")
async def file_service_metrics(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Lightweight metrics for demo/ops visibility (tenant-scoped).
    """
    from sqlalchemy import func, select
    from .models import ReceiptDocument
    from .models_feedback import ReceiptTrainingSnapshot, ReceiptFieldCorrection

    def _count(model, where):
        return select(func.count()).select_from(model).where(where)

    tenant = user.tenant_id
    receipts_total = (await db.execute(_count(ReceiptDocument, ReceiptDocument.tenant_id == tenant))).scalar() or 0
    receipts_completed = (await db.execute(_count(ReceiptDocument, (ReceiptDocument.tenant_id == tenant) & (ReceiptDocument.ocr_status == "completed")))).scalar() or 0
    receipts_failed = (await db.execute(_count(ReceiptDocument, (ReceiptDocument.tenant_id == tenant) & (ReceiptDocument.ocr_status == "failed")))).scalar() or 0

    snapshots_total = (await db.execute(_count(ReceiptTrainingSnapshot, ReceiptTrainingSnapshot.tenant_id == tenant))).scalar() or 0
    corrections_total = (await db.execute(_count(ReceiptFieldCorrection, ReceiptFieldCorrection.tenant_id == tenant))).scalar() or 0

    return {
        "success": True,
        "data": {
            "receipts_total": receipts_total,
            "receipts_completed": receipts_completed,
            "receipts_failed": receipts_failed,
            "training_snapshots_total": snapshots_total,
            "field_corrections_total": corrections_total,
        },
        "error": None,
        "meta": {},
    }
