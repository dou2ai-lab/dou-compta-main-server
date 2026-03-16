"""
Quick test script to verify Tesseract OCR is working
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ocr_service.provider import get_ocr_provider
from services.ocr_service.config import settings

async def test_tesseract():
    """Test Tesseract OCR provider"""
    print(f"OCR_PROVIDER setting: {settings.OCR_PROVIDER}")
    
    provider = get_ocr_provider()
    print(f"Provider class: {type(provider).__name__}")
    
    # Test with a simple image (you would pass actual image bytes here)
    # For now, just verify it's initialized correctly
    if hasattr(provider, 'tesseract_initialized'):
        print("✅ Tesseract OCR provider is ready")
    else:
        print("Provider initialized")
    
    return provider

if __name__ == "__main__":
    asyncio.run(test_tesseract())









