"""
Script to reprocess a receipt with Tesseract OCR and Gemini LLM
Run this to reprocess an existing receipt
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common.database import AsyncSessionLocal
from services.file_service.models import ReceiptDocument
from services.file_service.storage import StorageService
from services.ocr_service.provider import get_ocr_provider
from services.ocr_service.normalizer import DataNormalizer
from services.ocr_service.events import EventPublisher
from services.ocr_service.service import OCRService
from sqlalchemy import select

async def reprocess_receipt(receipt_id: str):
    """Reprocess a receipt with current OCR/LLM setup"""
    async with AsyncSessionLocal() as db:
        # Get receipt
        result = await db.execute(
            select(ReceiptDocument).where(ReceiptDocument.id == uuid.UUID(receipt_id))
        )
        receipt = result.scalar_one_or_none()
        
        if not receipt:
            print(f"Receipt {receipt_id} not found")
            return
        
        print(f"Found receipt: {receipt.file_name}")
        print(f"Current OCR status: {receipt.ocr_status}")
        
        # Create event payload
        event = {
            "receipt_id": receipt_id,
            "tenant_id": str(receipt.tenant_id),
            "user_id": str(receipt.tenant_id),  # We don't have user_id in receipt, use tenant_id
            "payload": {
                "file_id": str(receipt.file_id),
                "file_name": receipt.file_name,
                "mime_type": receipt.mime_type,
                "file_size": receipt.file_size,
                "storage_path": receipt.storage_path,
                "encryption_key_id": receipt.encryption_key_id
            }
        }
        
        # Initialize services
        storage = StorageService()
        provider = get_ocr_provider()
        normalizer = DataNormalizer()
        events = EventPublisher()
        
        ocr_service = OCRService(db, storage, provider, normalizer, events)
        
        print("Starting OCR processing...")
        await ocr_service.process_receipt(event)
        print("✅ OCR processing completed!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reprocess_receipt.py <receipt_id>")
        sys.exit(1)
    
    receipt_id = sys.argv[1]
    asyncio.run(reprocess_receipt(receipt_id))

























