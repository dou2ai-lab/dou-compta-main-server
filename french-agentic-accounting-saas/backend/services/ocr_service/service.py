# -----------------------------------------------------------------------------
# File: service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Business logic for OCR processing including extraction, normalization, and event publishing
# -----------------------------------------------------------------------------

"""
OCR Service Business Logic
"""
import uuid
from typing import Dict, Optional
import structlog

from .provider import OCRProvider
from .normalizer import DataNormalizer
from .events import EventPublisher
from .config import settings

logger = structlog.get_logger()

class OCRService:
    """OCR processing service"""
    
    def __init__(self, db_session, storage, provider: OCRProvider, normalizer: DataNormalizer, events: EventPublisher, encryption=None):
        self.db = db_session
        self.storage = storage
        self.provider = provider
        self.normalizer = normalizer
        self.events = events
        self.encryption = encryption
    
    async def process_receipt(self, event: Dict):
        """
        Process receipt OCR extraction
        
        1. Create OCR job
        2. Download file from storage
        3. Submit to OCR provider
        4. Extract data
        5. Normalize data
        6. Save results
        7. Update expense record
        8. Publish completion event
        """
        receipt_id = event["receipt_id"]
        tenant_id = event["tenant_id"]
        user_id = event["user_id"]
        file_metadata = event["payload"]
        
        # Create OCR job
        job_id = str(uuid.uuid4())
        idempotency_key = event.get("idempotency_key", str(uuid.uuid4()))
        
        # TODO: Save OCR job to database
        
        try:
            # Publish started event
            await self.events.publish_ocr_started(
                receipt_id=receipt_id,
                tenant_id=tenant_id,
                user_id=user_id,
                job_id=job_id
            )
            
            # Download file from storage
            file_content = await self.storage.download_file(file_metadata["storage_path"])
            
            # Decrypt if needed
            encryption_key_id = file_metadata.get("encryption_key_id")
            if encryption_key_id and self.encryption:
                try:
                    logger.info("decrypting_file_for_ocr", receipt_id=receipt_id, encryption_key_id=encryption_key_id)
                    file_content = await self.encryption.decrypt(file_content, encryption_key_id)
                    logger.info("file_decrypted_for_ocr", receipt_id=receipt_id, decrypted_size=len(file_content))
                except Exception as e:
                    logger.error("file_decryption_failed", receipt_id=receipt_id, error=str(e), exc_info=True)
                    raise Exception(f"Failed to decrypt file for OCR processing: {e}")
            elif not encryption_key_id:
                logger.info("file_not_encrypted", receipt_id=receipt_id, message="Processing unencrypted file")
            
            # Submit to OCR provider
            ocr_result = await self.provider.extract(file_content, file_metadata["mime_type"])
            
            # Normalize extracted data
            normalized_data = await self.normalizer.normalize(ocr_result)
            
            # Save OCR results to database
            from sqlalchemy import select
            import uuid as uuid_lib
            from services.file_service.models import ReceiptDocument
            from datetime import datetime
            
            result = await self.db.execute(
                select(ReceiptDocument).where(
                    ReceiptDocument.id == uuid_lib.UUID(receipt_id)
                )
            )
            receipt_doc = result.scalar_one_or_none()
            
            if receipt_doc:
                # Update OCR status and store OCR data
                receipt_doc.ocr_status = "completed"
                receipt_doc.ocr_job_id = uuid_lib.UUID(job_id)
                receipt_doc.ocr_completed_at = datetime.utcnow()
                
                # Store OCR results in meta_data
                if not receipt_doc.meta_data:
                    receipt_doc.meta_data = {}
                receipt_doc.meta_data["ocr"] = normalized_data
                
                # CRITICAL: Mark JSONB field as modified so SQLAlchemy persists the change
                from sqlalchemy.orm import attributes
                attributes.flag_modified(receipt_doc, "meta_data")
                
                await self.db.commit()
                await self.db.flush()  # Ensure all changes are flushed
                # Don't refresh after commit to avoid connection issues
                logger.info("ocr_results_saved", receipt_id=receipt_id, job_id=job_id)
            else:
                logger.warning("receipt_not_found_for_ocr_update", receipt_id=receipt_id)
            
            # Update expense record if linked
            if file_metadata.get("expense_id"):
                # TODO: Update expense with extracted data
                pass
            
            # Publish completion event
            await self.events.publish_ocr_completed(
                receipt_id=receipt_id,
                tenant_id=tenant_id,
                user_id=user_id,
                job_id=job_id,
                extracted_data=normalized_data
            )
            
            logger.info("ocr_processing_completed", job_id=job_id, receipt_id=receipt_id)
            
        except Exception as e:
            logger.error("ocr_processing_failed", job_id=job_id, error=str(e), exc_info=True)
            
            # Update receipt status on failure
            try:
                from sqlalchemy import select
                import uuid as uuid_lib
                from services.file_service.models import ReceiptDocument
                from datetime import datetime
                from sqlalchemy.orm import attributes
                
                result = await self.db.execute(
                    select(ReceiptDocument).where(
                        ReceiptDocument.id == uuid_lib.UUID(receipt_id)
                    )
                )
                receipt_doc = result.scalar_one_or_none()
                
                if receipt_doc:
                    # In development, fail-open so the UI can proceed (frontend blocks on ocr_status=failed)
                    if settings.OCR_FAIL_OPEN and settings.ENVIRONMENT != "production":
                        if not receipt_doc.meta_data:
                            receipt_doc.meta_data = {}
                        receipt_doc.meta_data.setdefault("ocr", {})
                        receipt_doc.meta_data["ocr_error"] = str(e)
                        attributes.flag_modified(receipt_doc, "meta_data")

                        receipt_doc.ocr_status = "completed"
                        receipt_doc.ocr_completed_at = datetime.utcnow()
                        receipt_doc.ocr_job_id = uuid_lib.UUID(job_id)
                        await self.db.commit()
                        await self.db.flush()
                        logger.warning(
                            "ocr_failed_but_marked_completed_fail_open",
                            receipt_id=receipt_id,
                            job_id=job_id,
                            error=str(e),
                        )
                        # Also publish "completed" so downstream flow continues
                        try:
                            await self.events.publish_ocr_completed(
                                receipt_id=receipt_id,
                                tenant_id=tenant_id,
                                user_id=user_id,
                                job_id=job_id,
                                extracted_data=receipt_doc.meta_data.get("ocr", {}) if receipt_doc.meta_data else {},
                            )
                        except Exception:
                            # Don't crash on event publish
                            pass
                        return

                    # Production (or strict mode): mark as failed
                    receipt_doc.ocr_status = "failed"
                    await self.db.commit()
            except Exception as db_error:
                logger.error("failed_to_update_ocr_status", error=str(db_error))
            
            # Publish failed event
            await self.events.publish_ocr_failed(
                receipt_id=receipt_id,
                tenant_id=tenant_id,
                user_id=user_id,
                job_id=job_id,
                error=str(e)
            )
            
            # TODO: Retry or send to DLQ
            raise









