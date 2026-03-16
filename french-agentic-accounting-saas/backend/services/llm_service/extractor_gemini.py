# -----------------------------------------------------------------------------
# File: extractor_gemini.py
# -----------------------------------------------------------------------------

import json
import structlog
from datetime import datetime
from decimal import Decimal
import google.generativeai as genai

from .config import settings
from .schemas import ReceiptExtractionRequest, ReceiptExtractionResponse

logger = structlog.get_logger()


class GeminiExtractor:
    """Google Gemini-based OCR extraction"""

    def __init__(self):
        self.provider = "gemini"
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Gemini client"""
        try:
            api_key = settings.GEMINI_API_KEY
            if not api_key:
                logger.warning("gemini_api_key_not_configured")
                self.api_key = None
                return

            genai.configure(api_key=api_key)

            # Use configured model name
            self.model_name = settings.GEMINI_MODEL or "models/gemini-2.0-flash"

            self.api_key = api_key
            logger.info("gemini_client_initialized", model=self.model_name)

        except Exception as e:
            logger.error("gemini_initialization_failed", error=str(e))
            self.api_key = None

    async def extract(self, request: ReceiptExtractionRequest) -> ReceiptExtractionResponse:
        """Extract structured data"""
        if not self.api_key:
            return self._fallback_extraction(request)

        try:
            system_instruction, user_prompt = self._build_extraction_prompt(
                request.ocr_text, request.language
            )

            response = await self._extract_with_gemini(
                system_instruction,
                user_prompt
            )

            extracted = self._parse_gemini_response(response, request.receipt_id)
            logger.info("gemini_extraction_completed", receipt_id=request.receipt_id)
            return extracted

        except Exception as e:
            logger.error("gemini_extraction_failed", error=str(e))
            return self._fallback_extraction(request)

    def _build_extraction_prompt(self, ocr_text: str, language="fr"):
        """Build structured extraction prompt - extract ALL fields visible on the bill"""
        if len(ocr_text) > 8000:
            lines = ocr_text.split("\n")
            ocr_text = "\n".join(lines[:30] + ["..."] + lines[-15:])

        system_instruction = f"""
You are an expert at extracting structured data from {language.upper()} receipts and invoices.
Extract EVERY field visible on the bill. Return ONLY valid JSON with this structure:

{{
  "merchant_name": "string or null",
  "merchant_address": "string or null - full address if present",
  "merchant_vat_number": "string or null - VAT number, SIRET, TVA number",
  "invoice_number": "string or null - invoice/receipt number",
  "expense_date": "YYYY-MM-DD or null",
  "subtotal": number or null - amount before VAT/tax,
  "total_amount": number or null - final total including VAT,
  "currency": "EUR" or "USD" etc,
  "vat_amount": number or null,
  "vat_rate": number or null - percentage (e.g. 20 for 20%),
  "payment_method": "string or null - card, cash, check, Visa, etc",
  "category": "string or null - meals, travel, accommodation, transport, office, training (infer from items)",
  "description": "string or null - brief summary of items purchased",
  "line_items": [
    {{"description": "item name", "quantity": 1, "unit_price": 0.0, "amount": 0.0, "vat_rate": 20}}
  ],
  "confidence_scores": {{"merchant_name": 0.9, "total_amount": 0.95, ...}}
}}

Rules:
- Extract ALL line items with description, quantity, unit_price, amount, vat_rate when available
- Use null for any field not found
- expense_date: CRITICAL - Look for "Invoice Date", "Date", "Séjour" (stay), "Issue Date". For French: "Séjour: 22/01/2026 - 23/01/2026" use first date (22/01/2026). Formats: DD/MM/YYYY, "April 15, 2050", YYYY-MM-DD. Always output YYYY-MM-DD.
- Amounts: Use numbers only (no € or $). French uses comma as decimal: 136,50 = 136.50; convert to 136.5 in JSON.
- FR receipts: "TOTAL TTC" = total_amount, "TVA" = VAT (vat_rate % and vat_amount), "Chambre" = room, "Petit déjeuner" = breakfast. Extract every line item with its amount.
- For line_items: include every product/service line (Chambre, Petit déjeuner, Taxe de séjour, etc.) with description and amount
""".strip()

        user_prompt = f"""
Extract ALL structured data from this receipt/invoice OCR text:

{ocr_text}

Return ONLY valid JSON with every field you can extract.
""".strip()

        return system_instruction, user_prompt

    async def _extract_with_gemini(self, system_instruction: str, user_prompt: str) -> str:
        """Extract using Gemini API with correct v1beta format"""
        generation_config = {
            "temperature": 0.1,
            "top_p": 0.9,
            "max_output_tokens": 4000,
            "response_mime_type": "application/json",
        }

        try:
            # CRITICAL: Use system_instruction parameter (NOT in messages)
            # Gemini 2.0 doesn't support {"role": "system"} in messages
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=system_instruction  # ← CORRECT WAY for Gemini 2.0
            )

            # Send only the user message (system instruction is already set in model)
            response = await model.generate_content_async(user_prompt)

            logger.info("gemini_api_call_success", model=self.model_name)
            return response.text

        except Exception as e:
            logger.error("gemini_model_failed", model=self.model_name, error=str(e))
            raise

    def _parse_gemini_response(self, response: str, receipt_id: str):
        """Parse JSON response"""
        try:
            text = response.strip()

            if text.startswith("```"):
                text = text.strip("```").strip()

            data = json.loads(text)

            def parse_decimal(v):
                if v is None:
                    return None
                try:
                    s = str(v).strip().replace(" ", "")
                    if "," in s and "." not in s:
                        parts = s.rsplit(",", 1)
                        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) <= 2:
                            s = parts[0].replace(",", "") + "." + parts[1]
                        else:
                            s = s.replace(",", "")
                    return Decimal(s) if s else None
                except:
                    return None

            def parse_date(v):
                if v is None or not isinstance(v, (str, int, float)):
                    return None
                s = str(v).strip()
                if not s:
                    return None
                # Try common formats
                formats = [
                    "%Y-%m-%d",
                    "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
                    "%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y",
                    "%Y/%m/%d", "%d %B %Y", "%d %b %Y",
                    "%B %d, %Y", "%b %d, %Y",
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(s, fmt).date()
                    except ValueError:
                        continue
                return None

            return ReceiptExtractionResponse(
                receipt_id=receipt_id,
                merchant_name=data.get("merchant_name"),
                merchant_address=data.get("merchant_address"),
                merchant_vat_number=data.get("merchant_vat_number"),
                invoice_number=data.get("invoice_number"),
                expense_date=parse_date(data.get("expense_date")),
                subtotal=parse_decimal(data.get("subtotal")),
                total_amount=parse_decimal(data.get("total_amount")),
                currency=data.get("currency", "EUR"),
                vat_amount=parse_decimal(data.get("vat_amount")),
                vat_rate=parse_decimal(data.get("vat_rate")),
                payment_method=data.get("payment_method"),
                category=data.get("category"),
                description=data.get("description"),
                line_items=data.get("line_items", []),
                confidence_scores=data.get("confidence_scores", {}),
                extraction_metadata={
                    "provider": "gemini",
                    "model": self.model_name,
                    "method": "json_mode"
                }
            )

        except Exception as e:
            logger.error("gemini_response_parse_failed", error=str(e), response=response[:200])
            raise ValueError("Invalid Gemini JSON")

    def _fallback_extraction(self, request: ReceiptExtractionRequest):
        """Fallback rule-based extractor"""
        from .extractor import LLMExtractor
        return LLMExtractor()._fallback_extraction(request)
