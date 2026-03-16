# -----------------------------------------------------------------------------
# File: extractor.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: LLM-based extraction service for extracting structured data from OCR text
# -----------------------------------------------------------------------------

"""
LLM-based Extraction Service
Extracts structured data from OCR text using LLM
"""
import json
import structlog
from typing import Dict, Optional
from datetime import datetime, date
from decimal import Decimal

from .config import settings
from .schemas import ReceiptExtractionRequest, ReceiptExtractionResponse

logger = structlog.get_logger()

class LLMExtractor:
    """LLM-based data extraction from OCR text"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize LLM provider client"""
        if self.provider == "openai":
            try:
                import openai
                if settings.OPENAI_API_KEY:
                    self.client = openai.AsyncOpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        base_url=settings.OPENAI_BASE_URL or None,
                        timeout=settings.OPENAI_TIMEOUT
                    )
                    self.model = settings.OPENAI_MODEL
                    logger.info("openai_client_initialized", model=self.model)
                else:
                    logger.warning("openai_api_key_not_configured", provider="openai")
                    self.client = None
            except ImportError:
                logger.warning("openai_not_installed", provider="openai")
                self.client = None
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(
                    api_key=settings.ANTHROPIC_API_KEY or None,
                    timeout=settings.ANTHROPIC_TIMEOUT
                )
                self.model = settings.ANTHROPIC_MODEL
            except ImportError:
                logger.warning("anthropic_not_installed", provider="anthropic")
                self.client = None
        elif self.provider == "gemini":
            try:
                from .extractor_gemini import GeminiExtractor
                self.gemini_extractor = GeminiExtractor()
                # Gemini extractor doesn't need a client attribute - it creates models per request
                # Check if API key is configured
                if hasattr(self.gemini_extractor, 'api_key') and self.gemini_extractor.api_key:
                    self.model = self.gemini_extractor.model_name
                    # Don't set self.client for Gemini - it's not needed
                    logger.info("gemini_extractor_initialized", model=self.model, api_key_configured=True)
                else:
                    logger.warning("gemini_api_key_not_configured")
                    self.gemini_extractor = None
                    self.client = None
            except Exception as e:
                logger.warning("gemini_not_available", error=str(e), exc_info=True)
                self.gemini_extractor = None
                self.client = None
        else:
            self.client = None
            logger.warning("llm_provider_not_configured", provider=self.provider)
    
    async def extract(self, request: ReceiptExtractionRequest) -> ReceiptExtractionResponse:
        """
        Extract structured data from OCR text using LLM
        
        Args:
            request: Extraction request with OCR text
            
        Returns:
            Extracted receipt data
        """
        # Handle Gemini separately - it has its own extractor
        if self.provider == "gemini":
            if hasattr(self, 'gemini_extractor') and self.gemini_extractor:
                if hasattr(self.gemini_extractor, 'api_key') and self.gemini_extractor.api_key:
                    try:
                        logger.info("using_gemini_extraction", receipt_id=request.receipt_id)
                        return await self.gemini_extractor.extract(request)
                    except Exception as e:
                        logger.error("gemini_extraction_failed", error=str(e), receipt_id=request.receipt_id, exc_info=True)
                        logger.warning("falling_back_to_rule_based", receipt_id=request.receipt_id)
                        return self._fallback_extraction(request)
                else:
                    logger.warning("llm_extraction_fallback", reason="Gemini API key not configured")
                    return self._fallback_extraction(request)
            else:
                logger.warning("llm_extraction_fallback", reason="Gemini extractor not initialized")
                return self._fallback_extraction(request)
        
        # For other LLM providers, check if client is available
        if not self.client:
            logger.warning("llm_extraction_fallback", reason=f"LLM provider '{self.provider}' client not configured")
            return self._fallback_extraction(request)
        
        try:
            # Build prompt for LLM
            prompt = self._build_extraction_prompt(request.ocr_text, request.language)
            
            # Call LLM
            if self.provider == "openai":
                response = await self._extract_with_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._extract_with_anthropic(prompt)
            else:
                logger.warning("llm_extraction_fallback", reason=f"Unsupported provider: {self.provider}")
                return self._fallback_extraction(request)
            
            # Parse and validate response
            extracted_data = self._parse_llm_response(response, request.receipt_id)
            
            logger.info("llm_extraction_completed", receipt_id=request.receipt_id)
            return extracted_data
            
        except Exception as e:
            logger.error("llm_extraction_failed", error=str(e), receipt_id=request.receipt_id, exc_info=True)
            # Fallback to rule-based extraction
            return self._fallback_extraction(request)
    
    def _build_extraction_prompt(self, ocr_text: str, language: str = "fr") -> str:
        """Build extraction prompt for LLM"""
        if language == "fr":
            system_prompt = """You are an expert at extracting structured data from French receipts. Extract the following fields:
- merchant_name: The name of the merchant/store
- expense_date: The date of the expense in YYYY-MM-DD format
- total_amount: The total amount including VAT (as a decimal number)
- currency: The currency code (EUR for France)
- vat_amount: The VAT amount (as a decimal number)
- vat_rate: The VAT rate as a percentage (e.g., 20 for 20%)

Return ONLY valid JSON in this exact format:
{
  "merchant_name": "string or null",
  "expense_date": "YYYY-MM-DD or null",
  "total_amount": number or null,
  "currency": "EUR",
  "vat_amount": number or null,
  "vat_rate": number or null,
  "line_items": [],
  "confidence_scores": {
    "merchant_name": 0.0-1.0,
    "expense_date": 0.0-1.0,
    "total_amount": 0.0-1.0,
    "vat_amount": 0.0-1.0,
    "vat_rate": 0.0-1.0
  }
}

If a field cannot be extracted, use null. Be precise with dates and amounts."""
        else:
            system_prompt = """You are an expert at extracting structured data from receipts. Extract merchant name, date, total amount, VAT amount, and VAT rate. Return valid JSON only."""
        
        return f"{system_prompt}\n\nOCR Text:\n{ocr_text}\n\nExtracted JSON:"
    
    async def _extract_with_openai(self, prompt: str) -> str:
        """Extract using OpenAI API"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from receipts. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    
    async def _extract_with_anthropic(self, prompt: str) -> str:
        """Extract using Anthropic API"""
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            temperature=settings.OPENAI_TEMPERATURE,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    
    def _parse_llm_response(self, response: str, receipt_id: str) -> ReceiptExtractionResponse:
        """Parse LLM response and create extraction response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            data = json.loads(response)
            
            # Parse date
            expense_date = None
            if data.get("expense_date"):
                try:
                    expense_date = datetime.strptime(data["expense_date"], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass
            
            # Parse amounts
            total_amount = None
            if data.get("total_amount") is not None:
                try:
                    total_amount = Decimal(str(data["total_amount"]))
                except (ValueError, TypeError):
                    pass
            
            vat_amount = None
            if data.get("vat_amount") is not None:
                try:
                    vat_amount = Decimal(str(data["vat_amount"]))
                except (ValueError, TypeError):
                    pass
            
            vat_rate = None
            if data.get("vat_rate") is not None:
                try:
                    vat_rate = Decimal(str(data["vat_rate"]))
                except (ValueError, TypeError):
                    pass
            
            return ReceiptExtractionResponse(
                receipt_id=receipt_id,
                merchant_name=data.get("merchant_name"),
                expense_date=expense_date,
                total_amount=total_amount,
                currency=data.get("currency", "EUR"),
                vat_amount=vat_amount,
                vat_rate=vat_rate,
                line_items=data.get("line_items", []),
                confidence_scores=data.get("confidence_scores", {}),
                extraction_metadata={"provider": self.provider, "model": self.model}
            )
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error("llm_response_parse_failed", error=str(e), response=response[:200])
            raise ValueError(f"Failed to parse LLM response: {e}")
    
    def _fallback_extraction(self, request: ReceiptExtractionRequest) -> ReceiptExtractionResponse:
        """Fallback rule-based extraction when LLM is not available"""
        import re
        from datetime import datetime
        
        ocr_text = request.ocr_text
        extracted = {
            "merchant_name": None,
            "expense_date": None,
            "total_amount": None,
            "currency": "EUR",
            "vat_amount": None,
            "vat_rate": None,
            "confidence_scores": {}
        }
        
        # Extract total amount (look for patterns like "TOTAL: 45.50", "Subtotal: $107.96", or "$45.50")
        amount_patterns = [
            r'Subtotal[:\s]+\$?([\d,\.]+)',
            r'TOTAL[:\s]+\$?([\d,\.]+)',
            r'\$([\d,\.]+)\s*(?:EUR|€|USD)?',
            r'([\d,\.]+)\s*EUR',
            r'([\d,\.]+)\s*€'
        ]
        # Also look for the largest amount mentioned (likely the total)
        all_amounts = []
        for pattern in amount_patterns:
            matches = re.finditer(pattern, ocr_text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '').replace('$', '')
                    amount_value = Decimal(amount_str)
                    all_amounts.append(amount_value)
                except (ValueError, AttributeError):
                    continue
        
        # Use the largest amount found as total (but skip very small amounts like VAT rates)
        if all_amounts:
            valid_amounts = [a for a in all_amounts if a > 1.0]  # Skip amounts <= 1 (likely not totals)
            if valid_amounts:
                extracted["total_amount"] = max(valid_amounts)
                extracted["confidence_scores"]["total_amount"] = 0.7
        
        # Extract date - handle multiple formats
        months_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Try month name format first: "November 27, 2024" or "Nov 27, 2024"
        month_name_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\s,]+(\d{1,2}),?\s+(\d{4})'
        match = re.search(month_name_pattern, ocr_text, re.IGNORECASE)
        if match:
            try:
                month_name, day_str, year_str = match.groups()
                month = months_map.get(month_name.lower())
                day = int(day_str)
                year = int(year_str)
                parsed_date = date(year, month, day)
                if parsed_date <= date.today():
                    extracted["expense_date"] = parsed_date
                    extracted["confidence_scores"]["expense_date"] = 0.7
                else:
                    logger.warning("parsed_future_date", date=str(parsed_date))
            except (ValueError, KeyError) as e:
                logger.debug("date_parsing_failed", error=str(e))
        
        # If month name format didn't work, try numeric formats
        if not extracted.get("expense_date"):
            date_patterns = [
                # Format: DD/MM/YYYY or DD-MM-YYYY
                r'Date[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
                r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
                # Format: YYYY-MM-DD (but not receipt numbers)
                r'(?<!Receipt\s*#:)(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, ocr_text)
                if match:
                    try:
                        groups = match.groups()
                        # Check if it's YYYY-MM-DD format (year is first group)
                        if len(groups[0]) == 4 and int(groups[0]) > 2000 and int(groups[0]) < 2100:
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:
                            # DD/MM/YYYY format
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                        
                        parsed_date = date(year, month, day)
                        # Validate date is reasonable (not in future, not too old)
                        if parsed_date <= date.today() and parsed_date.year >= 2000:
                            extracted["expense_date"] = parsed_date
                            extracted["confidence_scores"]["expense_date"] = 0.6
                            break
                    except (ValueError, AttributeError, IndexError) as e:
                        logger.debug("date_parsing_failed", pattern=pattern, error=str(e))
                        continue
        
        # Extract merchant (first significant line, usually merchant name)
        merchant_patterns = [
            r'^([A-Z][A-Za-z0-9\s&]+(?:Electronics|Market|Store|Shop|Restaurant|Café|Hotel|Ltd|Inc|Corp|LLC))',  # Common business names
            r'^([A-Z][A-Za-z\s]{5,50})(?:\n|$)',  # First capitalized line of reasonable length
            r'CHEZ[:\s]+([A-Z][A-Z\s]+)',
            r'FROM[:\s]+([A-Z][A-Z\s]+)',
        ]
        for pattern in merchant_patterns:
            match = re.search(pattern, ocr_text, re.MULTILINE | re.IGNORECASE)
            if match:
                merchant = match.group(1).strip()
                # Filter out common false positives
                if merchant and not any(word.lower() in merchant.lower() for word in ['Receipt', 'Date', 'Time', 'ITEM', 'QTY', 'PRICE']):
                    extracted["merchant_name"] = merchant
                    extracted["confidence_scores"]["merchant_name"] = 0.7
                    break
        
        # Extract VAT (look for "TVA" or "VAT" followed by amount or rate)
        vat_patterns = [
            r'VAT\s*\((\d+)%\)[:\s]*\$?([\d,\.]+)',  # VAT (20%): $21.59
            r'VAT[:\s]+\$?([\d,\.]+)',  # VAT: $21.59
            r'TVA[:\s]+([\d,\.]+)',
            r'([\d,\.]+)\s*%?\s*TVA'
        ]
        for pattern in vat_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 2:
                        # Pattern with rate and amount: VAT (20%): $21.59
                        vat_rate_str = groups[0].replace(',', '.')
                        vat_amount_str = groups[1].replace(',', '').replace('$', '')
                        extracted["vat_rate"] = Decimal(vat_rate_str)
                        extracted["vat_amount"] = Decimal(vat_amount_str)
                        extracted["confidence_scores"]["vat_rate"] = 0.8
                        extracted["confidence_scores"]["vat_amount"] = 0.8
                    else:
                        # Single value - determine if rate or amount
                        vat_str = groups[0].replace(',', '').replace('$', '')
                        vat_value = Decimal(vat_str)
                        # If value > 50, assume it's a rate percentage, else assume amount
                        if vat_value > 50:
                            extracted["vat_rate"] = vat_value
                            extracted["confidence_scores"]["vat_rate"] = 0.5
                        else:
                            extracted["vat_amount"] = vat_value
                            extracted["confidence_scores"]["vat_amount"] = 0.5
                    break
                except (ValueError, AttributeError, IndexError):
                    continue
        
        return ReceiptExtractionResponse(
            receipt_id=request.receipt_id,
            merchant_name=extracted["merchant_name"],
            expense_date=extracted["expense_date"],
            total_amount=extracted["total_amount"],
            currency=extracted["currency"],
            vat_amount=extracted["vat_amount"],
            vat_rate=extracted["vat_rate"],
            line_items=[],
            confidence_scores=extracted["confidence_scores"],
            extraction_metadata={"provider": "fallback", "method": "rule-based"}
        )

