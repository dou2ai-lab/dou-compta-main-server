"""Inspection helper: print receipt_documents row and key meta_data fields.

Usage:
    python scripts/check_receipt_for_rag.py <receipt_id>
"""
import asyncio
import os
import sys
import uuid

import structlog
from sqlalchemy import select

# Ensure project/ backend packages are on sys.path regardless of where script is launched from
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_ROOT)
for p in (BACKEND_ROOT, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from common.database import AsyncSessionLocal
from services.file_service.models import ReceiptDocument
from common.models import Expense


logger = structlog.get_logger()


async def main(receipt_id: str) -> None:
    try:
        rid = uuid.UUID(receipt_id)
    except Exception:
        print(f"Invalid UUID: {receipt_id}")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ReceiptDocument).where(ReceiptDocument.id == rid)
        )
        receipt = result.scalar_one_or_none()
        if not receipt:
            print(f"No receipt_documents row found for id={receipt_id}")
            return

        print(f"ReceiptDocument {receipt.id}")
        print(f"  tenant_id:   {receipt.tenant_id}")
        print(f"  file_id:     {receipt.file_id}")
        print(f"  ocr_status:  {receipt.ocr_status}")
        print(f"  has meta_data: {bool(receipt.meta_data)}")

        if receipt.meta_data:
            ocr = receipt.meta_data.get("ocr") or {}
            extraction = receipt.meta_data.get("extraction") or {}
            print("  meta_data.ocr keys:", list(ocr.keys()))
            print("  meta_data.extraction keys:", list(extraction.keys()))
            print("  merchant_name (ocr):", ocr.get("merchant_name"))
            print("  merchant_name (extraction):", extraction.get("merchant_name"))

        # Check linked expense if any
        if receipt.expense_id:
            exp_res = await db.execute(
                select(Expense).where(Expense.id == receipt.expense_id)
            )
            expense = exp_res.scalar_one_or_none()
            if expense:
                print(f"Linked Expense {expense.id}")
                print(f"  merchant_name: {expense.merchant_name}")
                print(f"  expense_date:  {expense.expense_date}")
                print(f"  amount:        {expense.amount} {expense.currency}")
            else:
                print(f"Warning: expense_id={receipt.expense_id} not found in expenses")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/check_receipt_for_rag.py <receipt_id>")
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))

