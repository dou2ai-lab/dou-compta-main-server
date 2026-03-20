# -----------------------------------------------------------------------------
# File: extractor_gemini.py
# -----------------------------------------------------------------------------

import json
import structlog
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
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

        system_instruction, user_prompt = self._build_extraction_prompt(
            request.ocr_text,
            request.language,
            getattr(request, "document_type", None),
            getattr(request, "ocr_pages", None),
            getattr(request, "ocr_lines", None),
            getattr(request, "ocr_blocks", None),
        )

        last_error = None
        for attempt in range(1, 4):
            try:
                prompt = user_prompt
                if attempt > 1:
                    prompt = (
                        user_prompt
                        + "\n\nIMPORTANT: Your previous output was invalid or incomplete. "
                        + "Return ONLY a single valid JSON object. No markdown, no commentary."
                    )

                response = await self._extract_with_gemini(system_instruction, prompt)
                llm_debug = {
                    "attempt": attempt,
                    "system_prompt": (system_instruction or "")[:2000],
                    "user_prompt": (prompt or "")[:4000],
                    "raw_response": (response or "")[:4000],
                }
                extracted = self._parse_gemini_response(response, request.receipt_id, llm_debug=llm_debug)
                logger.info("gemini_extraction_completed", receipt_id=request.receipt_id, attempt=attempt)
                return extracted
            except Exception as e:
                last_error = e
                logger.warning("gemini_extraction_attempt_failed", receipt_id=request.receipt_id, attempt=attempt, error=str(e))

        logger.error("gemini_extraction_failed", receipt_id=request.receipt_id, error=str(last_error))
        return self._fallback_extraction(request)

    def _build_extraction_prompt(
        self,
        ocr_text: str,
        language="fr",
        document_type: Optional[str] = None,
        ocr_pages: Optional[List[str]] = None,
        ocr_lines: Optional[List[dict]] = None,
        ocr_blocks: Optional[List[dict]] = None,
    ):
        """Build structured extraction prompt - extract ALL fields visible on the bill"""
        if len(ocr_text) > 8000:
            lines = ocr_text.split("\n")
            ocr_text = "\n".join(lines[:30] + ["..."] + lines[-15:])

        # Few-shot examples (French invoice). Keep short to reduce token cost while improving robustness.
        few_shot = """
Example 1 (noisy OCR):
OCR:
FACTURE N° FA-2025-001
Date : 14/02/2026
SAS BOULANGERIE DUPONT
Total TTC 597,60 €
TVA 20% 99,60 €

JSON:
{"document_type":"facture_achat","merchant_name":"SAS BOULANGERIE DUPONT","merchant_address":null,"merchant_vat_number":null,"invoice_number":"FA-2025-001","expense_date":"2026-02-14","subtotal":498.0,"total_amount":597.6,"currency":"EUR","vat_amount":99.6,"vat_rate":20,"payment_method":null,"category":null,"description":null,"line_items":[],"others":[],"overall_confidence":0.98,"confidence_scores":{"merchant_name":0.98,"invoice_number":0.99,"expense_date":0.98,"total_amount":0.99,"vat_amount":0.97,"vat_rate":0.96}}

Example 2 (missing VAT, still extract totals/date):
OCR:
FACTURE
CLIENT: ACME SAS
Le 01-03-2026
TOTAL TTC: 32,01 EUR

JSON:
{"document_type":"facture_vente","merchant_name":"ACME SAS","merchant_address":null,"merchant_vat_number":null,"invoice_number":null,"expense_date":"2026-03-01","subtotal":null,"total_amount":32.01,"currency":"EUR","vat_amount":null,"vat_rate":null,"payment_method":null,"category":null,"description":null,"line_items":[],"others":[],"overall_confidence":0.9,"confidence_scores":{"merchant_name":0.7,"expense_date":0.9,"total_amount":0.95}}
""".strip()

        doc_hint = (document_type or "").strip()
        system_instruction = f"""
You are an expert at extracting structured accounting data from {language.upper()} documents.

Supported document_type values (choose the best match):
- facture_achat (purchase invoice)
- facture_vente (sales invoice)
- releve_bancaire (bank statement)
- bulletin_paie (pay slip)
- autre (other)

Pipeline hint: document_type is "{doc_hint or 'unknown'}". Use this hint unless OCR content strongly contradicts it.

Extract EVERY field visible on the bill. Return ONLY valid JSON with this structure:

{{
  "document_type": "facture_achat|facture_vente|releve_bancaire|bulletin_paie|autre",
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
  "others": ["string", "string", "string"],
  "bank_statement": null or {{
    "opening_balance": number or null,
    "closing_balance": number or null,
    "currency": "EUR" or "USD" etc,
    "transactions": [
      {{"date":"YYYY-MM-DD","description":"string","amount":number,"currency":"EUR","type":"debit|credit"}}
    ]
  }},
  "payslip": null or {{
    "employer_name": "string or null",
    "employee_name": "string or null",
    "period": "YYYY-MM or null",
    "gross_pay": number or null,
    "net_pay": number or null,
    "currency": "EUR" or "USD" etc
  }},
  "overall_confidence": 0.0,
  "confidence_scores": {{"merchant_name": 0.9, "total_amount": 0.95, ...}}
}}

Rules:
- Mandatory fields (try very hard): total_amount, expense_date. If missing, still output null.
- NEVER guess values.
- ALWAYS map numbers to the closest label occurrence using layout hints (OCR lines bbox + nearest numeric value).
- If multiple candidate numbers exist, choose the one closest spatially (prefer same line, else nearest line below within a small vertical window, and closest column/x).
- Priority for totals:
  - TOTAL DUE > TOTAL TTC/TOTAL > TOTAL
- Mapping logic:
  - If a label has no number on the same line, take the nearest numeric value BELOW the label (and prefer same-column/x alignment).
  - If multiple numbers are possible, choose only if it is unambiguous; otherwise return null.
- If mapping is unclear or no candidate numeric value is near the label, return `null` for that field.
- Merchant must be the selling entity (vendor/fournisseur/company). Never use "Invoice Number", "Date", "TOTAL" tokens as merchant.
- Extract ALL line items with description, quantity, unit_price, amount, vat_rate when available
- Use null for any field not found
- expense_date: CRITICAL - Look for "Invoice Date", "Date", "Séjour" (stay), "Issue Date". For French: "Séjour: 22/01/2026 - 23/01/2026" use first date (22/01/2026). Formats: DD/MM/YYYY, "April 15, 2050", YYYY-MM-DD. Always output YYYY-MM-DD.
- Amounts: Use numbers only (no € or $). French uses comma as decimal: 136,50 = 136.50; convert to 136.5 in JSON.
- Preserve comma-decimals from OCR logic (e.g. "597,60") when interpreting totals.
- FR receipts: "TOTAL TTC" = total_amount, "TVA" = VAT (vat_rate % and vat_amount), "Chambre" = room, "Petit déjeuner" = breakfast. Extract every line item with its amount.
- For line_items: include every product/service line (Chambre, Petit déjeuner, Taxe de séjour, etc.) with description and amount
- others: include 2–3 additional useful insights if present (e.g. IBAN, BIC, payment reference, contract reference, due date)
- Confidence: confidence_scores values must be between 0 and 1; overall_confidence is also 0–1 (your best estimate).
- Field sources/auditability (best effort):
  - Put higher confidence when the value is directly visible in OCR (e.g. "TOTAL TTC 597,60 €").
  - For bank statements, prioritize bank_statement.transactions and balances; invoice fields may be null.
  - For payslips, prioritize payslip.net_pay / gross_pay / employer_name; invoice fields may be null.

Few-shot examples (follow the same JSON rules strictly):
{few_shot}
""".strip()

        pages_section = ""
        if ocr_pages and isinstance(ocr_pages, list) and len(ocr_pages) > 0:
            chunks = []
            for idx, txt in enumerate(ocr_pages[:20]):  # hard cap for safety
                t = (txt or "").strip()
                if not t:
                    continue
                chunks.append(f"=== PAGE {idx + 1} ===\n{t}")
            if chunks:
                pages_section = "\n\nPAGE-LEVEL OCR (keep structure; do not mix unrelated sections):\n" + "\n\n".join(chunks)

        def _truncate_ocr_lines(lines: Optional[List[dict]], max_items: int = 60) -> list[dict]:
            if not lines:
                return []
            out: list[dict] = []
            for ln in lines[:max_items]:
                if not isinstance(ln, dict):
                    continue
                bbox = ln.get("bbox")
                out.append({
                    "text": str(ln.get("text") or "").strip(),
                    "bbox": bbox if isinstance(bbox, list) and len(bbox) == 4 else None,
                    "page_index": ln.get("page_index"),
                    "block_num": ln.get("block_num"),
                    "line_num": ln.get("line_num"),
                })
            return out

        def _truncate_ocr_blocks(blocks: Optional[List[dict]], max_items: int = 80) -> list[dict]:
            if not blocks:
                return []
            out: list[dict] = []
            for b in blocks[:max_items]:
                if not isinstance(b, dict):
                    continue
                bbox = b.get("bbox")
                out.append({
                    "text": str(b.get("text") or "").strip(),
                    "bbox": bbox if isinstance(bbox, list) and len(bbox) == 4 else None,
                    "page_index": b.get("page_index"),
                })
            return out

        truncated_lines = _truncate_ocr_lines(ocr_lines)
        truncated_blocks = _truncate_ocr_blocks(ocr_blocks)

        user_prompt = f"""
Extract structured accounting data using spatial reasoning.

IMPORTANT:
- Labels and values may be on different lines
- Match values based on vertical proximity and spatial alignment (same column/x first)
- Do NOT guess values
- If mapping is unclear or ambiguous, return null for that field
- TOTAL mapping priority: TOTAL DUE > TOTAL TTC/TOTAL > TOTAL

OCR payload (structured):
{{
  "full_text": {json.dumps(ocr_text)},
  "lines": {json.dumps(truncated_lines, ensure_ascii=False)},
  "blocks": {json.dumps(truncated_blocks, ensure_ascii=False)}
}}
{pages_section}

Return ONLY valid JSON.
Do NOT include markdown or extra text.
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

    def _parse_gemini_response(self, response: str, receipt_id: str, llm_debug: Optional[dict] = None):
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
                document_type=data.get("document_type"),
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
                overall_confidence=float(data["overall_confidence"]) if data.get("overall_confidence") is not None else None,
                others=data.get("others", []) or [],
                bank_statement=data.get("bank_statement"),
                payslip=data.get("payslip"),
                extraction_metadata={
                    "provider": "gemini",
                    "model": self.model_name,
                    "method": "json_mode",
                    "llm_debug": llm_debug,
                }
            )

        except Exception as e:
            logger.error("gemini_response_parse_failed", error=str(e), response=response[:200])
            raise ValueError("Invalid Gemini JSON")

    def _fallback_extraction(self, request: ReceiptExtractionRequest):
        """Fallback rule-based extractor"""
        from .extractor import LLMExtractor
        return LLMExtractor()._fallback_extraction(request)
