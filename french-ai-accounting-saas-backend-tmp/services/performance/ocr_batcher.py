# -----------------------------------------------------------------------------
# File: ocr_batcher.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: OCR batching service for performance optimization
# -----------------------------------------------------------------------------

"""
OCR Batching Service
Batches OCR requests for improved performance
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog
import asyncio
from collections import deque

from services.file_service.models import ReceiptDocument
from services.ocr_service.provider import OCRProvider

logger = structlog.get_logger()

class OCRBatcher:
    """OCR batching service"""
    
    def __init__(
        self,
        db: AsyncSession,
        batch_size: int = 10,
        batch_timeout: int = 5  # seconds
    ):
        self.db = db
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_batch: deque = deque()
        self.batch_lock = asyncio.Lock()
        self.processing = False
    
    async def add_receipt(
        self,
        receipt_id: str,
        file_path: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Add receipt to batch for OCR processing"""
        try:
            async with self.batch_lock:
                self.pending_batch.append({
                    "receipt_id": receipt_id,
                    "file_path": file_path,
                    "tenant_id": tenant_id,
                    "added_at": datetime.utcnow()
                })
                
                # Trigger batch processing if batch is full
                if len(self.pending_batch) >= self.batch_size:
                    asyncio.create_task(self._process_batch())
                elif not self.processing:
                    # Start timeout timer
                    asyncio.create_task(self._process_batch_with_timeout())
            
            return {
                "success": True,
                "receipt_id": receipt_id,
                "queued": True,
                "batch_size": len(self.pending_batch)
            }
        except Exception as e:
            logger.error("ocr_batch_add_error", error=str(e))
            raise
    
    async def _process_batch_with_timeout(self):
        """Process batch after timeout"""
        await asyncio.sleep(self.batch_timeout)
        await self._process_batch()
    
    async def _process_batch(self):
        """Process current batch"""
        if self.processing:
            return
        
        async with self.batch_lock:
            if not self.pending_batch:
                self.processing = False
                return
            
            self.processing = True
            batch = list(self.pending_batch)
            self.pending_batch.clear()
        
        try:
            # Process batch in parallel
            tasks = [
                self._process_single_receipt(item)
                for item in batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed = len(results) - successful
            
            logger.info(
                "ocr_batch_processed",
                batch_size=len(batch),
                successful=successful,
                failed=failed
            )
        except Exception as e:
            logger.error("ocr_batch_process_error", error=str(e))
        finally:
            async with self.batch_lock:
                self.processing = False
    
    async def _process_single_receipt(
        self,
        item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process single receipt in batch"""
        try:
            receipt_id = item["receipt_id"]
            file_path = item["file_path"]
            tenant_id = item["tenant_id"]
            
            # Get receipt
            result = await self.db.execute(
                select(ReceiptDocument).where(
                    and_(
                        ReceiptDocument.id == receipt_id,
                        ReceiptDocument.tenant_id == tenant_id
                    )
                )
            )
            receipt = result.scalar_one_or_none()
            
            if not receipt:
                return {"success": False, "error": "Receipt not found"}
            
            # Process OCR
            ocr_provider = OCRProvider()
            ocr_result = await ocr_provider.extract_text(file_path)
            
            # Update receipt (ReceiptDocument uses meta_data JSONB for OCR data)
            if not receipt.meta_data:
                receipt.meta_data = {}
            receipt.meta_data["ocr_text"] = ocr_result.get("text", "")
            receipt.meta_data["ocr_confidence"] = ocr_result.get("confidence", 0.0)
            receipt.meta_data["ocr_processed_at"] = datetime.utcnow().isoformat()
            receipt.ocr_status = "completed"
            receipt.ocr_completed_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "receipt_id": receipt_id,
                "ocr_text": ocr_result.get("text", "")
            }
        except Exception as e:
            logger.error(
                "ocr_batch_single_error",
                receipt_id=item.get("receipt_id"),
                error=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def flush(self):
        """Flush remaining items in batch"""
        await self._process_batch()




