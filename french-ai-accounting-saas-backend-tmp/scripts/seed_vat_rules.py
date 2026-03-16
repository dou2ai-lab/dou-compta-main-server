# -----------------------------------------------------------------------------
# Seed French VAT rules into vat_rules table for RAG and VAT engine.
# Usage: from backend folder: python scripts/seed_vat_rules.py
#        Or: set DATABASE_URL and run (default port 5433).
# -----------------------------------------------------------------------------
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

from common.models import Tenant
from services.admin.models import VatRule

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


def seed_vat_rules():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        tenant = db.execute(select(Tenant).limit(1)).scalar_one_or_none()
        if not tenant:
            print("No tenant found. Create a tenant first.")
            return
        print(f"Seeding VAT rules for tenant: {tenant.name}")

        rules_data = [
            {"category": "Restaurant", "vat_rate": Decimal("10.00"), "vat_code": "FR-TVA-10", "is_default": False},
            {"category": "Hotel", "vat_rate": Decimal("10.00"), "vat_code": "FR-TVA-10", "is_default": False},
            {"category": "Transport", "vat_rate": Decimal("10.00"), "vat_code": "FR-TVA-10", "is_default": False},
            {"category": "Default", "vat_rate": Decimal("20.00"), "vat_code": "FR-TVA-20", "is_default": True},
        ]
        for r in rules_data:
            existing = db.execute(
                select(VatRule).where(
                    VatRule.tenant_id == tenant.id,
                    VatRule.category == r["category"],
                    VatRule.deleted_at.is_(None),
                )
            ).scalar_one_or_none()
            if existing:
                print(f"  Skip (exists): {r['category']} {r['vat_rate']}%")
                continue
            rule = VatRule(
                tenant_id=tenant.id,
                category=r["category"],
                vat_rate=r["vat_rate"],
                vat_code=r["vat_code"],
                is_default=r["is_default"],
            )
            db.add(rule)
            print(f"  Added: {r['category']} {r['vat_rate']}%")
        db.commit()
        print("VAT rules seeded. Use Audit Q&A → Index VAT rules to embed for RAG.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_vat_rules()
