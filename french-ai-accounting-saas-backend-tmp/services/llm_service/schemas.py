# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: Pydantic schemas for LLM extraction service including extraction request/response and validation
# -----------------------------------------------------------------------------

"""
Pydantic schemas for LLM Service
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import date
from decimal import Decimal
import structlog

logger = structlog.get_logger()

class ExtractedField(BaseModel):
    """Single extracted field with confidence"""
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    raw_value: Optional[str] = None

class ReceiptExtractionRequest(BaseModel):
    """Request for LLM extraction from OCR text"""
    ocr_text: str = Field(..., min_length=1, description="Raw OCR extracted text")
    receipt_id: str = Field(..., description="Receipt document ID")
    tenant_id: str = Field(..., description="Tenant ID")
    language: str = Field(default="fr", description="Receipt language (fr, en, etc.)")
    document_type: Optional[str] = Field(
        None,
        description="Hint from pipeline: facture_achat|facture_vente|releve_bancaire|bulletin_paie|autre",
    )
    ocr_pages: Optional[List[str]] = Field(
        default=None,
        description="Optional page-level OCR texts (PAGE 1..N) for multi-page documents",
    )
    ocr_lines: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional line-level OCR structure with bbox (for deterministic label alignment).",
    )
    ocr_blocks: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional block-level OCR structure (layout hints).",
    )

class ReceiptExtractionResponse(BaseModel):
    """Extracted receipt data with validation"""
    receipt_id: str
    document_type: Optional[str] = Field(
        None,
        description="One of: facture_achat, facture_vente, releve_bancaire, bulletin_paie, autre",
    )
    merchant_name: Optional[str] = Field(None, description="Merchant/store name")
    merchant_address: Optional[str] = Field(None, description="Merchant address")
    merchant_vat_number: Optional[str] = Field(None, description="Merchant VAT/SIRET number")
    invoice_number: Optional[str] = Field(None, description="Invoice or receipt number")
    expense_date: Optional[date] = Field(None, description="Expense date (YYYY-MM-DD)")
    subtotal: Optional[Decimal] = Field(None, ge=0, description="Subtotal before VAT")
    total_amount: Optional[Decimal] = Field(None, ge=0, description="Total amount including VAT")
    currency: str = Field(default="EUR", max_length=3, description="Currency code (ISO 4217)")
    vat_amount: Optional[Decimal] = Field(None, ge=0, description="VAT amount")
    vat_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="VAT rate percentage")
    payment_method: Optional[str] = Field(None, description="Payment method (card, cash, etc.)")
    category: Optional[str] = Field(None, description="Expense category: meals, travel, accommodation, transport, office, training")
    description: Optional[str] = Field(None, description="Summary of purchased items")
    line_items: List[Dict] = Field(default_factory=list, description="Line items: [{description, quantity, unit_price, amount, vat_rate}]")
    others: List[str] = Field(default_factory=list, description="2–3 additional insights (IBAN, payment ref, contract ref, etc.)")
    # Document-type specific extractions (kept optional so invoice UI stays stable)
    bank_statement: Optional[Dict[str, Any]] = Field(
        None,
        description="For releve_bancaire: {opening_balance, closing_balance, transactions:[{date, description, amount, currency, type}] }",
    )
    payslip: Optional[Dict[str, Any]] = Field(
        None,
        description="For bulletin_paie: {employer_name, employee_name, period, gross_pay, net_pay, taxes}",
    )
    confidence_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores per field")
    overall_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence 0.0–1.0",
    )
    status: Optional[str] = Field(
        None,
        description="One of: completed, needs_review, rejected, REQUIRES_MANUAL_VALIDATION",
    )
    field_sources: Dict[str, str] = Field(
        default_factory=dict,
        description="Per-field extraction source: llm|ocr|regex|mixed",
    )
    field_reasoning: Dict[str, str] = Field(
        default_factory=dict,
        description="Short per-field reasoning/evidence for auditability",
    )
    extraction_metadata: Dict = Field(default_factory=dict, description="Additional extraction metadata")
    
    @field_validator('expense_date')
    @classmethod
    def validate_date(cls, v):
        """Validate date is not in the future"""
        if v:
            today = date.today()
            # Allow dates up to today
            if v > today:
                logger.warning("future_date_detected", date=str(v), today=str(today))
                # Return None instead of raising error to allow processing to continue
                return None
            # Validate date is reasonable (not too old)
            if v.year < 1990:
                logger.warning("date_too_old", date=str(v))
                return None
        return v
    
    @field_validator('vat_rate')
    @classmethod
    def validate_vat_rate(cls, v):
        """Validate VAT rate is reasonable for France"""
        if v is not None:
            # Common French VAT rates: 0%, 2.1%, 5.5%, 10%, 20%
            common_rates = [0, 2.1, 5.5, 10, 20]
            if v not in common_rates and not (0 <= v <= 100):
                # Allow other rates but log warning
                pass
        return v

class ExtractionValidationResult(BaseModel):
    """Validation result for extracted data"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_data: Optional[ReceiptExtractionResponse] = None

class ExpenseCreationRequest(BaseModel):
    """Request to create expense from extracted data"""
    receipt_id: str
    extracted_data: ReceiptExtractionResponse
    user_id: str
    tenant_id: str
    category: Optional[str] = None
    description: Optional[str] = None
    auto_submit: bool = Field(default=False, description="Auto-submit expense after creation")

