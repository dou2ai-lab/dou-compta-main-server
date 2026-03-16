# -----------------------------------------------------------------------------
# File: provider.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: OCR provider abstraction supporting Google Document AI and Azure Form Recognizer
# -----------------------------------------------------------------------------

"""
OCR Provider Abstraction
Supports Tesseract (free), Google Document AI, and Azure Form Recognizer
"""
from typing import Dict, Optional
import structlog

from .config import settings

logger = structlog.get_logger()

class OCRProvider:
    """Abstract OCR provider interface"""
    
    async def extract(self, file_content: bytes, mime_type: str) -> Dict:
        """
        Extract data from receipt using OCR
        
        Args:
            file_content: File content as bytes
            mime_type: MIME type of file
        
        Returns:
            Extracted data dictionary
        """
        # No OCR available (e.g. Tesseract not installed). Return empty so the user
        # can enter details manually instead of seeing the same fake "Extracted Merchant" every time.
        logger.warning("ocr_not_available", message="Using no-OCR fallback; extraction will be empty. Install Tesseract for real OCR.")
        return {
            "merchant_name": None,
            "date": None,
            "total_amount": None,
            "vat_amount": None,
            "vat_rate": None,
            "currency": "EUR",
            "line_items": [],
            "text": "",
            "ocr_text": "",
            "confidence_scores": {},
            "raw_response": {}
        }

class GoogleDocumentAIProvider(OCRProvider):
    """Google Document AI provider"""
    
    def __init__(self):
        self.project_id = settings.GOOGLE_PROJECT_ID
        self.location = settings.GOOGLE_LOCATION
        self.processor_id = settings.GOOGLE_PROCESSOR_ID
        # TODO: Initialize Google Document AI client
    
    async def extract(self, file_content: bytes, mime_type: str) -> Dict:
        """Extract using Google Document AI"""
        logger.info("google_ocr_extraction_started", mime_type=mime_type)
        
        # TODO: Implement Google Document AI extraction
        # client = documentai.DocumentProcessorServiceClient()
        # ...
        logger.warning("google_document_ai_not_implemented", message="Returning empty extraction; implement client for real OCR.")
        return {
            "merchant_name": None,
            "date": None,
            "total_amount": None,
            "vat_amount": None,
            "vat_rate": None,
            "currency": "EUR",
            "line_items": [],
            "text": "",
            "ocr_text": "",
            "confidence_scores": {},
            "raw_response": {}
        }

class AzureFormRecognizerProvider(OCRProvider):
    """Azure Form Recognizer provider"""
    
    def __init__(self):
        self.endpoint = settings.AZURE_ENDPOINT
        self.key = settings.AZURE_KEY
        self.region = settings.AZURE_REGION
        # TODO: Initialize Azure Form Recognizer client
    
    async def extract(self, file_content: bytes, mime_type: str) -> Dict:
        """Extract using Azure Form Recognizer"""
        logger.info("azure_ocr_extraction_started", mime_type=mime_type)
        
        # TODO: Implement Azure Form Recognizer extraction
        # client = DocumentAnalysisClient(endpoint=self.endpoint, credential=self.key)
        # ...
        logger.warning("azure_form_recognizer_not_implemented", message="Returning empty extraction; implement client for real OCR.")
        return {
            "merchant_name": None,
            "date": None,
            "total_amount": None,
            "vat_amount": None,
            "vat_rate": None,
            "currency": "EUR",
            "line_items": [],
            "text": "",
            "ocr_text": "",
            "confidence_scores": {},
            "raw_response": {}
        }

def get_ocr_provider() -> OCRProvider:
    """Factory function to get OCR provider. Supports tesseract, paddle/paddleocr, google_document_ai, azure_form_recognizer."""
    p = (settings.OCR_PROVIDER or "").strip().lower()
    if p == "tesseract":
        try:
            from .provider_tesseract import TesseractOCRProvider
            return TesseractOCRProvider()
        except Exception as e:
            logger.warning("tesseract_provider_init_failed_falling_back", error=str(e))
            return OCRProvider()
    if p in ("paddle", "paddleocr"):
        try:
            from .provider_paddle import PaddleOCRProvider
            prov = PaddleOCRProvider()
            if getattr(prov, "_ocr", None) is not None:
                return prov
            logger.warning("paddle_ocr_not_available_falling_back_to_tesseract")
        except Exception as e:
            logger.warning("paddle_provider_init_failed_falling_back", error=str(e))
        try:
            from .provider_tesseract import TesseractOCRProvider
            return TesseractOCRProvider()
        except Exception as e2:
            logger.warning("tesseract_fallback_failed", error=str(e2))
            return OCRProvider()
    if p == "google_document_ai":
        return GoogleDocumentAIProvider()
    if p == "azure_form_recognizer":
        return AzureFormRecognizerProvider()
    # Default to Tesseract
    logger.warning("unknown_ocr_provider", provider=settings.OCR_PROVIDER, defaulting_to="tesseract")
    try:
        from .provider_tesseract import TesseractOCRProvider
        return TesseractOCRProvider()
    except Exception as e:
        logger.warning("tesseract_provider_init_failed_falling_back", error=str(e))
        return OCRProvider()









