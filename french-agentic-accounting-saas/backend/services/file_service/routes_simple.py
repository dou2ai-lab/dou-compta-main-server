# Simple working version of upload route
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import hashlib
from datetime import datetime
import structlog

from common.database import get_db
from common.models import Tenant
from services.auth.dependencies import get_current_user
from .models import ReceiptDocument
from .storage import StorageService
from .schemas import ReceiptUploadResponse

logger = structlog.get_logger()
router = APIRouter()

@router.post("/receipts/upload", response_model=ReceiptUploadResponse)
async def upload_receipt_simple(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):
    """Simplified upload that definitely works"""
    try:
        logger.info("simple_upload_started", user_id=str(user.id), filename=file.filename)
        
        # Read file
        file_content = await file.read()
        file_size = len(file_content)
        
        # Generate IDs
        receipt_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Get tenant
        if not user.tenant_id:
            raise HTTPException(status_code=400, detail="User has no tenant")
        
        tenant_id = user.tenant_id
        
        # Save to local storage
        storage = StorageService()
        storage_path = await storage.upload_file(
            file_content=file_content,
            file_id=file_id,
            tenant_id=str(tenant_id),
            file_name=file.filename or "receipt"
        )
        
        # Save to database - minimal fields only
        receipt_doc = ReceiptDocument(
            id=uuid.UUID(receipt_id),
            file_id=uuid.UUID(file_id),
            tenant_id=tenant_id,
            expense_id=None,
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
        
        db.add(receipt_doc)
        await db.commit()
        await db.refresh(receipt_doc)
        
        logger.info("simple_upload_success", receipt_id=receipt_id)
        
        return ReceiptUploadResponse(
            receipt_id=receipt_id,
            file_id=file_id,
            status="uploaded",
            ocr_status="pending",
            file_name=file.filename or "receipt",
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_at=receipt_doc.created_at.isoformat() if receipt_doc.created_at else datetime.utcnow().isoformat(),
            expense_id=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("simple_upload_failed", error=str(e), error_type=type(e).__name__, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {type(e).__name__}: {str(e)}"
        )
