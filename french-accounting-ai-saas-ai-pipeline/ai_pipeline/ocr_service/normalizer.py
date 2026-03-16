# -----------------------------------------------------------------------------
# File: normalizer.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Data normalization service for OCR extracted data including dates, amounts, and VAT
# -----------------------------------------------------------------------------

"""
Data Normalization Service
Normalizes OCR extracted data
"""
from typing import Dict
from datetime import datetime
import re
import structlog

from common.receipt_extraction import extract_from_ocr_text

logger = structlog.get_logger()

class DataNormalizer:
    """Normalizes OCR extracted data"""
    
    async def normalize(self, ocr_data: Dict) -> Dict:
        """
        Normalize OCR extracted data
        
        - Normalize dates to ISO 8601
        - Normalize currency to EUR
        - Normalize amounts to decimal
        - Normalize merchant names
        - Extract VAT amount and rate
        """
        normalized = {}

        # Extract from text when OCR returns only raw text (e.g. Tesseract)
        ocr_text = ocr_data.get("text", "") or ocr_data.get("ocr_text", "")
        extracted = {}
        if ocr_text and ocr_text.strip():
            extracted = extract_from_ocr_text(ocr_text)

        # Normalize merchant name (prefer extracted from text)
        normalized["merchant_name"] = self._normalize_merchant_name(
            extracted.get("merchant_name") or ocr_data.get("merchant_name", "")
        )

        # Normalize date (prefer extracted)
        normalized["expense_date"] = extracted.get("expense_date") or self._normalize_date(
            ocr_data.get("date", "")
        )

        # Normalize amounts (prefer extracted from text when OCR has no structured data)
        raw_total = ocr_data.get("total_amount", 0)
        normalized["total_amount"] = float(extracted["total_amount"]) if extracted.get("total_amount") else self._normalize_amount(raw_total)

        # Normalize currency
        normalized["currency"] = self._normalize_currency(
            ocr_data.get("currency", "EUR")
        )

        # Extract VAT (prefer extracted from text)
        raw_vat = ocr_data.get("vat_amount", 0)
        normalized["vat_amount"] = float(extracted["vat_amount"]) if extracted.get("vat_amount") else self._normalize_amount(raw_vat)
        normalized["vat_rate"] = float(extracted["vat_rate"]) if extracted.get("vat_rate") is not None else self._normalize_vat_rate(ocr_data.get("vat_rate", 0))
        
        # Line items
        normalized["line_items"] = ocr_data.get("line_items", [])
        
        # Preserve confidence scores
        normalized["confidence_scores"] = ocr_data.get("confidence_scores", {})
        
        # Preserve raw OCR text for LLM processing
        normalized["text"] = ocr_data.get("text", "") or ocr_data.get("ocr_text", "")
        normalized["raw_response"] = ocr_data.get("raw_response", {})
        
        logger.info("data_normalized", receipt_id=ocr_data.get("receipt_id"))
        
        return normalized
    
    def _normalize_merchant_name(self, name: str) -> str:
        """Normalize merchant name"""
        if not name:
            return ""
        # Remove extra spaces, trim
        normalized = " ".join(name.split())
        return normalized.strip()
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to ISO 8601 format (YYYY-MM-DD)"""
        if not date_str:
            return None
        
        # Try various date formats
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%d.%m.%Y"
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        logger.warning("date_normalization_failed", date_str=date_str)
        return None
    
    def _normalize_amount(self, amount) -> float:
        """Normalize amount to decimal"""
        if isinstance(amount, (int, float)):
            return float(amount)
        
        if isinstance(amount, str):
            # Remove currency symbols, spaces, commas
            cleaned = re.sub(r'[€$£,\s]', '', amount)
            # Replace decimal comma with dot
            cleaned = cleaned.replace(',', '.')
            try:
                return float(cleaned)
            except ValueError:
                logger.warning("amount_normalization_failed", amount=amount)
                return 0.0
        
        return 0.0
    
    def _normalize_currency(self, currency: str) -> str:
        """Normalize currency to EUR (Phase 2)"""
        # Phase 2: All amounts in EUR
        return "EUR"
    
    def _normalize_vat_rate(self, rate) -> float:
        """Normalize VAT rate to percentage"""
        if isinstance(rate, (int, float)):
            # If rate > 1, assume it's a percentage (e.g., 20 for 20%)
            if rate > 1:
                return float(rate)
            # If rate <= 1, assume it's a decimal (e.g., 0.20 for 20%)
            return float(rate * 100)
        
        if isinstance(rate, str):
            # Remove % symbol
            cleaned = rate.replace('%', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        
        return 0.0









