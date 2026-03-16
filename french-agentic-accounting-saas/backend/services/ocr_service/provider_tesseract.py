# -----------------------------------------------------------------------------
# File: provider_tesseract.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 02-12-2025
# Description: Tesseract OCR provider implementation (free, self-hosted)
# -----------------------------------------------------------------------------

"""
Tesseract OCR Provider
Free, self-hosted OCR solution using pytesseract
"""
import io
import structlog
from typing import Dict
from PIL import Image
import pytesseract

from .config import settings
from .provider import OCRProvider

logger = structlog.get_logger()

class TesseractOCRProvider(OCRProvider):
    """Tesseract OCR provider implementation"""
    
    def __init__(self):
        """Initialize Tesseract OCR provider"""
        # Tesseract should be installed in the system
        # For Docker, it should be in the Dockerfile
        try:
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            logger.info("tesseract_initialized", version=pytesseract.get_tesseract_version())
        except Exception as e:
            logger.warning("tesseract_not_available", error=str(e))
            logger.warning("tesseract_fallback_to_text_extraction", message="Will attempt basic text extraction")
    
    async def extract(self, file_content: bytes, mime_type: str) -> Dict:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            file_content: Image file content as bytes
            mime_type: MIME type of file
        
        Returns:
            Dictionary with extracted text and raw OCR data
        """
        logger.info("tesseract_ocr_extraction_started", mime_type=mime_type)
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(file_content))
            
            # Perform OCR
            # Use French language if available, fallback to English
            try:
                ocr_text = pytesseract.image_to_string(image, lang='fra+eng')
            except:
                # Fallback to English only
                ocr_text = pytesseract.image_to_string(image, lang='eng')
            
            # Get detailed data with bounding boxes (optional, for future use)
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Clean up OCR text
            cleaned_text = self._clean_ocr_text(ocr_text)
            
            logger.info("tesseract_ocr_extraction_completed", 
                       text_length=len(cleaned_text),
                       characters_extracted=len(cleaned_text.replace('\n', '').replace(' ', '')))
            
            # Return only raw text - LLM will extract structured data
            return {
                "text": cleaned_text,
                "raw_response": {
                    "ocr_data": ocr_data,
                    "image_format": image.format,
                    "image_size": image.size
                },
                "confidence_scores": {},  # Tesseract doesn't provide per-field confidence
                "extraction_method": "tesseract_ocr"
            }
            
        except Exception as e:
            logger.error("tesseract_ocr_extraction_failed", error=str(e), exc_info=True)
            # Return empty text on failure
            return {
                "text": "",
                "raw_response": {"error": str(e)},
                "confidence_scores": {},
                "extraction_method": "tesseract_ocr_failed"
            }
    
    def _clean_ocr_text(self, text: str) -> str:
        """
        Clean OCR text output
        
        Removes excessive whitespace while preserving structure
        """
        if not text:
            return ""
        
        # Split into lines
        lines = text.split('\n')
        
        # Remove empty lines and excessive whitespace
        cleaned_lines = []
        for line in lines:
            # Strip leading/trailing whitespace
            line = line.strip()
            
            # Skip completely empty lines
            if not line:
                continue
            
            # Fix common OCR errors
            # Replace multiple spaces with single space
            line = ' '.join(line.split())
            
            cleaned_lines.append(line)
        
        # Join with single newline
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive newlines (more than 2 consecutive)
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        return cleaned_text

