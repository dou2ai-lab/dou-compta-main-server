"""
Backfill document_embeddings from expense_policies, vat_rules, and receipt_documents.
Run from backend folder with venv activated and DATABASE_URL set:

  .\\venv\\Scripts\\Activate.ps1
  $env:DATABASE_URL = "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit"
  python scripts/backfill_document_embeddings.py

Requires: pip install sentence-transformers (and asyncpg for DB)
"""
import asyncio
import os
import sys

# Set DATABASE_URL for async driver before any DB import
_db_url = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
if _db_url.startswith("postgresql://") and "+asyncpg" not in _db_url:
    os.environ["DATABASE_URL"] = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(CURRENT_DIR)
for p in (BACKEND_ROOT,):
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import select, text
from common.database import AsyncSessionLocal
from common.models import Tenant


async def main():

    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Tenant).limit(1))
        tenant = r.scalar_one_or_none()
        if not tenant:
            print("No tenant found. Create a tenant first.")
            return
        tenant_id = str(tenant.id)
        print(f"Using tenant: {tenant.name} ({tenant_id})")

        # Count existing rows in source tables
        for name, sql in [
            ("expense_policies", "SELECT COUNT(*) FROM expense_policies WHERE tenant_id = :t AND deleted_at IS NULL"),
            ("vat_rules", "SELECT COUNT(*) FROM vat_rules WHERE tenant_id = :t AND deleted_at IS NULL"),
            ("receipt_documents", "SELECT COUNT(*) FROM receipt_documents WHERE tenant_id = :t AND deleted_at IS NULL"),
        ]:
            c = await db.execute(text(sql), {"t": tenant_id})
            n = c.scalar() or 0
            print(f"  {name}: {n} rows")

        print("Loading embedding model (may take a moment)...")
        from services.rag_service.embeddings import EmbeddingsPipeline

        pipeline = EmbeddingsPipeline(db, tenant_id)

        created_by = None
        counts = {}
        try:
            counts["policies"] = await pipeline.embed_policies(created_by=created_by)
            print(f"Embedded policies: {counts['policies']}")
        except Exception as e:
            print(f"embed_policies error: {e}")
            counts["policies"] = 0

        try:
            counts["vat_rules"] = await pipeline.embed_vat_rules(created_by=created_by)
            print(f"Embedded VAT rules: {counts['vat_rules']}")
        except Exception as e:
            print(f"embed_vat_rules error: {e}")
            counts["vat_rules"] = 0

        try:
            counts["receipts"] = await pipeline.embed_receipts(created_by=created_by)
            print(f"Embedded receipts: {counts['receipts']}")
        except Exception as e:
            print(f"embed_receipts error: {e}")
            counts["receipts"] = 0

        await db.commit()

        # Count document_embeddings
        r2 = await db.execute(
            text("SELECT COUNT(*) FROM document_embeddings WHERE tenant_id = :t AND deleted_at IS NULL"),
            {"t": tenant_id},
        )
        total = r2.scalar() or 0
        print(f"Total document_embeddings rows for tenant: {total}")


if __name__ == "__main__":
    asyncio.run(main())
