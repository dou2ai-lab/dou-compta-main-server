# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Business logic for file upload, encryption, storage, and management operations
# -----------------------------------------------------------------------------

"""
File Service Business Logic
"""
import uuid
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from fastapi import UploadFile
import structlog

from .models import ReceiptDocument
from .storage import StorageService
from .encryption import EncryptionService
from .events import EventPublisher
from .config import settings

logger = structlog.get_logger()

class FileService:
    """File upload and management service"""
    
    def __init__(self, db_session, storage: StorageService, encryption: EncryptionService, events: EventPublisher):
        self.db = db_session
        self.storage = storage
        self.encryption = encryption
        self.events = events
    
    async def upload_file(
        self,
        file: UploadFile,
        user_id: str,
        tenant_id: str,
        expense_id: Optional[str] = None
    ) -> dict:
        """
        Upload and process a receipt file
        
        1. Validate file type and size
        2. Generate file ID and encryption key
        3. Encrypt file content
        4. Upload to object storage
        5. Save metadata to database
        6. Publish receipt.uploaded event
        """
        import uuid as uuid_lib
        
        try:
            # Validate file
            await self._validate_file(file)
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Generate file hash for deduplication
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Generate IDs
            receipt_id = str(uuid.uuid4())
            file_id = str(uuid.uuid4())
            
            # Encrypt file (disabled in local/dev to avoid KMS / key setup issues)
            # For development we simply store the raw file bytes and leave
            # encryption_key_id as None. In production this can be re-enabled.
            encryption_key_id = None
            encrypted_content = file_content
            
            # Convert tenant_id to UUID if it's a string
            try:
                tenant_uuid = uuid_lib.UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
            except (ValueError, AttributeError) as e:
                logger.error("invalid_tenant_id", tenant_id=tenant_id, error=str(e))
                raise ValueError(f"Invalid tenant_id format: {tenant_id}")
            
            # Upload to storage
            try:
                storage_path = await self.storage.upload_file(
                    file_content=encrypted_content,
                    file_id=file_id,
                    tenant_id=tenant_id,
                    file_name=file.filename or "receipt"
                )
            except Exception as storage_error:
                logger.error("storage_upload_failed", error=str(storage_error), exc_info=True)
                raise ValueError(f"Failed to upload file to storage: {str(storage_error)}")
            
            # Convert expense_id to UUID if provided
            expense_uuid = None
            if expense_id:
                try:
                    expense_uuid = uuid_lib.UUID(expense_id)
                except (ValueError, AttributeError) as e:
                    logger.warning("invalid_expense_id", expense_id=expense_id, error=str(e))
                    # Don't fail the upload if expense_id is invalid, just log it
            
            # Save metadata to database
            try:
                receipt_doc = ReceiptDocument(
                    id=uuid_lib.UUID(receipt_id),
                    file_id=uuid_lib.UUID(file_id),
                    tenant_id=tenant_uuid,
                    expense_id=expense_uuid,
                    file_name=(file.filename or "receipt")[:255],  # Ensure it fits in VARCHAR(255)
                    file_size=file_size,
                    mime_type=file.content_type,
                    storage_path=storage_path[:500],  # Ensure it fits in VARCHAR(500)
                    encryption_key_id=encryption_key_id,
                    file_hash=file_hash,
                    upload_status="completed",
                    ocr_status="pending",
                    meta_data={}  # Explicitly set default
                )
                self.db.add(receipt_doc)
                await self.db.flush()
                await self.db.commit()
                await self.db.refresh(receipt_doc)
            except Exception as db_error:
                await self.db.rollback()
                logger.error("database_save_failed", error=str(db_error), error_type=type(db_error).__name__, exc_info=True)
                # Include more details in error message
                error_msg = f"Failed to save receipt to database: {str(db_error)}"
                if hasattr(db_error, 'orig'):
                    error_msg += f" (Original: {str(db_error.orig)})"
                raise ValueError(error_msg)
            
            # Publish event (don't fail upload if event publishing fails)
            try:
                await self.events.publish_receipt_uploaded(
                    receipt_id=receipt_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    file_metadata={
                        "file_id": file_id,
                        "file_name": file.filename,
                        "mime_type": file.content_type,
                        "file_size": file_size,
                        "storage_path": storage_path,
                        "encryption_key_id": encryption_key_id
                    }
                )
            except Exception as event_error:
                logger.warning("event_publish_failed", error=str(event_error), receipt_id=receipt_id)
                # Don't fail the upload if event publishing fails
            
            logger.info("file_uploaded", receipt_id=receipt_id, file_id=file_id)
            
            from .schemas import ReceiptUploadResponse
            return ReceiptUploadResponse(
                receipt_id=receipt_id,
                file_id=file_id,
                status="uploaded",
                ocr_status="pending",
                file_name=file.filename or "receipt",
                file_size=file_size,
                mime_type=file.content_type or "application/octet-stream",
                uploaded_at=receipt_doc.created_at.isoformat() if receipt_doc.created_at else datetime.utcnow().isoformat(),
                expense_id=expense_id
            )
        except ValueError as ve:
            # Re-raise ValueError as-is (validation errors)
            raise
        except Exception as e:
            logger.error("upload_file_failed", error=str(e), exc_info=True)
            raise ValueError(f"Failed to upload file: {str(e)}")
    
    async def _validate_file(self, file: UploadFile):
        """Validate file type and size"""
        # Check MIME type
        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"File type not supported. Allowed types: {', '.join(settings.ALLOWED_MIME_TYPES)}")
        
        # Check file size
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer
        
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise ValueError(f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / 1024 / 1024}MB")
    
    async def get_receipt(self, receipt_id: str, user_id: str, tenant_id: str) -> dict:
        """Get receipt metadata"""
        from sqlalchemy import select
        import uuid as uuid_lib
        
        result = await self.db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                ReceiptDocument.tenant_id == uuid_lib.UUID(tenant_id),
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise ValueError("Receipt not found")
        
        # Map to response format matching ReceiptUploadResponse schema
        return {
            "receipt_id": str(receipt.id),
            "file_id": str(receipt.file_id),
            "status": receipt.upload_status,
            "ocr_status": receipt.ocr_status,
            "file_name": receipt.file_name,
            "file_size": receipt.file_size,
            "mime_type": receipt.mime_type,
            "uploaded_at": receipt.created_at.isoformat() if receipt.created_at else datetime.utcnow().isoformat(),
            "expense_id": str(receipt.expense_id) if receipt.expense_id else None,
            "meta_data": receipt.meta_data or {}
        }
    
    async def get_receipt_status(self, receipt_id: str, user_id: str, tenant_id: str):
        """Get receipt upload and OCR status"""
        from sqlalchemy import select
        from .schemas import ReceiptStatusResponse
        import uuid as uuid_lib
        
        result = await self.db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                ReceiptDocument.tenant_id == uuid_lib.UUID(tenant_id),
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise ValueError("Receipt not found")
        
        return ReceiptStatusResponse(
            receipt_id=str(receipt.id),
            upload_status=receipt.upload_status,
            ocr_status=receipt.ocr_status,
            ocr_job_id=str(receipt.ocr_job_id) if receipt.ocr_job_id else None,
            last_updated=receipt.updated_at.isoformat() if receipt.updated_at else receipt.created_at.isoformat() if receipt.created_at else datetime.utcnow().isoformat()
        )
    
    async def generate_download_url(
        self,
        receipt_id: str,
        user_id: str,
        tenant_id: str,
        expires_in: int = 3600
    ):
        """Generate signed URL for downloading receipt"""
        from sqlalchemy import select
        import uuid as uuid_lib
        
        result = await self.db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                ReceiptDocument.tenant_id == uuid_lib.UUID(tenant_id),
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise ValueError("Receipt not found")
        
        # Generate presigned URL
        url = self.storage.generate_presigned_url(receipt.storage_path, expires_in)
        
        from .schemas import ReceiptDownloadResponse
        return ReceiptDownloadResponse(
            receipt_id=str(receipt.id),
            download_url=url,
            expires_in=expires_in,
            expires_at=(datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        )
    
    async def delete_receipt(self, receipt_id: str, user_id: str, tenant_id: str):
        """Delete receipt file and metadata"""
        from sqlalchemy import select
        from datetime import datetime
        import uuid as uuid_lib
        
        result = await self.db.execute(
            select(ReceiptDocument).where(
                ReceiptDocument.id == uuid_lib.UUID(receipt_id),
                ReceiptDocument.tenant_id == uuid_lib.UUID(tenant_id),
                ReceiptDocument.deleted_at.is_(None)
            )
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            raise ValueError("Receipt not found")
        
        # Soft delete
        receipt.deleted_at = datetime.utcnow()
        await self.db.commit()
        
        # Schedule async deletion from storage (in production, use background task)
        # await self.storage.delete_file(receipt.storage_path)









