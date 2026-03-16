# -----------------------------------------------------------------------------
# File: accounting_poster.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Accounting posting logic with VAT segmentation
# -----------------------------------------------------------------------------

"""
Accounting Posting Logic
Handles accounting entries with correct VAT segmentation for French accounting
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from decimal import Decimal
import structlog

from .connectors import get_erp_connector
from .models import AccountingPosting, ERPConnection
from common.models import Expense

logger = structlog.get_logger()

class AccountingPoster:
    """Accounting posting service with VAT segmentation"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.erp_connector = None
        self.vat_account_mapping = {}
        self.expense_account_mapping = {}
    
    async def initialize_erp_connection(self, erp_connection_id: Optional[str] = None):
        """Initialize ERP connection"""
        try:
            if erp_connection_id:
                result = await self.db.execute(
                    select(ERPConnection).where(
                        and_(
                            ERPConnection.id == erp_connection_id,
                            ERPConnection.tenant_id == self.tenant_id,
                            ERPConnection.is_active == True,
                            ERPConnection.deleted_at.is_(None)
                        )
                    )
                )
                connection = result.scalar_one_or_none()
                if connection:
                    config = connection.configuration.copy()
                    config["provider"] = connection.provider
                    config["connection_type"] = connection.connection_type
                    self.erp_connector = get_erp_connector(config)
                    self.vat_account_mapping = config.get("vat_account_mapping", {})
                    self.expense_account_mapping = config.get("expense_account_mapping", {})
        except Exception as e:
            logger.error("initialize_erp_connection_error", error=str(e))
    
    async def post_expense(
        self,
        expense_id: str,
        erp_connection_id: Optional[str] = None,
        posting_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Post expense to ERP with VAT segmentation"""
        try:
            # Get expense
            result = await self.db.execute(
                select(Expense).where(
                    and_(
                        Expense.id == expense_id,
                        Expense.tenant_id == self.tenant_id,
                        Expense.deleted_at.is_(None)
                    )
                )
            )
            expense = result.scalar_one_or_none()
            
            if not expense:
                raise ValueError(f"Expense {expense_id} not found")
            
            # Initialize ERP connection if needed
            if not self.erp_connector:
                await self.initialize_erp_connection(erp_connection_id)
            
            if not self.erp_connector:
                raise ValueError("ERP connection not configured")
            
            # Prepare accounting entries with VAT segmentation
            entries = await self._prepare_accounting_entries(expense, posting_date)
            
            # Post to ERP
            posting_results = []
            for entry in entries:
                erp_result = await self.erp_connector.post_accounting_entry(entry)
                
                # Save posting record
                posting = AccountingPosting(
                    tenant_id=self.tenant_id,
                    erp_connection_id=erp_connection_id,
                    expense_id=expense_id,
                    posting_date=posting_date or datetime.utcnow(),
                    posting_type=entry["posting_type"],
                    gl_account=entry["gl_account"],
                    amount=entry["amount"],
                    currency=entry.get("currency", "EUR"),
                    vat_rate=entry.get("vat_rate"),
                    vat_amount=entry.get("vat_amount"),
                    vat_account=entry.get("vat_account"),
                    vat_code=entry.get("vat_code"),
                    erp_document_id=erp_result.get("erp_document_id"),
                    erp_status=erp_result.get("status", "pending"),
                    erp_error=erp_result.get("error"),
                    metadata=entry.get("metadata", {})
                )
                
                self.db.add(posting)
                posting_results.append(posting)
            
            await self.db.flush()
            
            return {
                "success": True,
                "expense_id": expense_id,
                "postings": [
                    {
                        "id": str(p.id),
                        "posting_type": p.posting_type,
                        "gl_account": p.gl_account,
                        "amount": float(p.amount),
                        "vat_amount": float(p.vat_amount) if p.vat_amount else None,
                        "erp_document_id": p.erp_document_id,
                        "erp_status": p.erp_status
                    }
                    for p in posting_results
                ]
            }
            
        except Exception as e:
            logger.error("post_expense_error", expense_id=expense_id, error=str(e))
            raise
    
    async def _prepare_accounting_entries(
        self,
        expense: Expense,
        posting_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Prepare accounting entries with VAT segmentation"""
        entries = []
        posting_date = posting_date or datetime.utcnow()
        
        # Get expense account
        expense_account = self._get_expense_account(expense)
        
        # Base expense entry (net amount)
        net_amount = expense.amount
        if expense.vat_amount:
            net_amount = expense.amount - expense.vat_amount
        
        entries.append({
            "posting_type": "expense",
            "gl_account": expense_account,
            "amount": float(net_amount),
            "currency": expense.currency or "EUR",
            "posting_date": posting_date.isoformat(),
            "reference": f"EXP-{expense.id}",
            "description": expense.description or "",
            "metadata": {
                "expense_id": str(expense.id),
                "category": expense.category,
                "merchant": expense.merchant_name
            }
        })
        
        # VAT entry (if applicable)
        if expense.vat_amount and expense.vat_rate:
            vat_account = self._get_vat_account(expense.vat_rate, expense.category)
            vat_code = self._get_vat_code(expense.vat_rate, expense.category)
            
            entries.append({
                "posting_type": "vat",
                "gl_account": vat_account,
                "amount": float(expense.vat_amount),
                "currency": expense.currency or "EUR",
                "posting_date": posting_date.isoformat(),
                "reference": f"EXP-{expense.id}",
                "vat_rate": float(expense.vat_rate),
                "vat_code": vat_code,
                "description": f"VAT {expense.vat_rate}% - {expense.description or ''}",
                "metadata": {
                    "expense_id": str(expense.id),
                    "vat_rate": float(expense.vat_rate),
                    "vat_code": vat_code
                }
            })
        
        # Credit entry (accounts payable or bank)
        # This depends on payment method - for now, use accounts payable
        credit_account = self._get_credit_account(expense)
        
        entries.append({
            "posting_type": "credit",
            "gl_account": credit_account,
            "amount": -float(expense.amount),  # Negative for credit
            "currency": expense.currency or "EUR",
            "posting_date": posting_date.isoformat(),
            "reference": f"EXP-{expense.id}",
            "description": f"Payment for {expense.description or 'expense'}",
            "metadata": {
                "expense_id": str(expense.id),
                "payment_method": "accounts_payable"
            }
        })
        
        return entries
    
    def _get_expense_account(self, expense: Expense) -> str:
        """Get GL account for expense based on category"""
        # Check mapping first
        if expense.category and expense.category in self.expense_account_mapping:
            return self.expense_account_mapping[expense.category]
        
        # Default mapping based on category
        category_mapping = {
            "meals": "611000",  # Meals and entertainment
            "travel": "625000",  # Travel expenses
            "hotel": "625100",  # Hotel expenses
            "transport": "625200",  # Transportation
            "office": "606000",  # Office supplies
            "software": "606100",  # Software expenses
        }
        
        return category_mapping.get(expense.category, "606000")  # Default: Other expenses
    
    def _get_vat_account(self, vat_rate: Decimal, category: Optional[str] = None) -> str:
        """Get VAT account based on rate and category"""
        # Check mapping first
        rate_key = f"{float(vat_rate)}%"
        if rate_key in self.vat_account_mapping:
            return self.vat_account_mapping[rate_key]
        
        # Default VAT accounts (French chart of accounts)
        vat_mapping = {
            20.0: "445660",  # VAT recoverable 20%
            10.0: "445661",  # VAT recoverable 10%
            5.5: "445662",  # VAT recoverable 5.5%
            2.1: "445663",  # VAT recoverable 2.1%
        }
        
        return vat_mapping.get(float(vat_rate), "445660")  # Default: 20% VAT
    
    def _get_vat_code(self, vat_rate: Decimal, category: Optional[str] = None) -> str:
        """Get French VAT code"""
        # French VAT codes
        vat_code_mapping = {
            20.0: "TVA20",  # Standard rate
            10.0: "TVA10",  # Reduced rate
            5.5: "TVA5.5",  # Super reduced rate
            2.1: "TVA2.1",  # Special rate
        }
        
        return vat_code_mapping.get(float(vat_rate), "TVA20")
    
    def _get_credit_account(self, expense: Expense) -> str:
        """Get credit account (accounts payable or bank)"""
        # For now, use accounts payable
        # In production, determine based on payment method
        return "401000"  # Accounts payable




