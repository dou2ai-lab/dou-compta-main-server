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
from fastapi.responses import JSONResponse
from typing import Optional
import structlog
import uuid
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import traceback
import asyncio
import httpx

from .schemas import (
    ReceiptUploadResponse,
    ReceiptStatusResponse,
    ReceiptDownloadResponse,
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
