# -----------------------------------------------------------------------------
# File: seed_gl_accounts.py
# Description: Seed default GL accounts for all tenants (for Categories & GL dropdowns)
# -----------------------------------------------------------------------------
"""
Add default GL accounts so the Categories & GL page has options like "6200 – Travel Expense".

Run from project root (uses DATABASE_URL from backend/.env):
  python backend/scripts/seed_gl_accounts.py

Or inside admin container:
  docker exec dou-admin python scripts/seed_gl_accounts.py
"""
import asyncio
import os
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend_dir))
_env_file = _backend_dir / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        pass

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from common.models import Tenant
from services.admin.models import GLAccount

import common.models  # noqa: F401
import services.admin.models  # noqa: F401

_raw = os.getenv("DATABASE_URL")
if not _raw:
    print("DATABASE_URL not set. Set it in backend/.env or the environment.")
    sys.exit(1)
DATABASE_URL = _raw.replace("postgresql://", "postgresql+asyncpg://", 1) if _raw.startswith("postgresql://") else _raw

DEFAULT_GL_ACCOUNTS = [
    ("6200", "Travel Expense", "expense"),
    ("6001", "Meals and catering", "expense"),
    ("6002", "Accommodation", "expense"),
    ("6003", "Transport and fuel", "expense"),
    ("6004", "Office supplies", "expense"),
    ("6005", "Training and education", "expense"),
    ("6006", "Professional services", "expense"),
    ("6010", "Other expenses", "expense"),
]


async def seed_gl_accounts():
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Tenant))
            tenants = result.scalars().all()
            if not tenants:
                print("No tenants found. Run seed_data.py first.")
                return

            added = 0
            for tenant in tenants:
                existing = await db.execute(
                    select(GLAccount.account_code).where(
                        GLAccount.tenant_id == tenant.id,
                        GLAccount.deleted_at.is_(None),
                    )
                )
                existing_codes = {str(r[0]) for r in existing.all()}
                to_add = [(code, name, acc_type) for code, name, acc_type in DEFAULT_GL_ACCOUNTS if code not in existing_codes]
                if not to_add:
                    print(f"Tenant {tenant.name} ({tenant.slug}): already has default GL accounts. Skipping.")
                    continue
                for code, account_name, acc_type in to_add:
                    gl = GLAccount(
                        tenant_id=tenant.id,
                        account_code=code,
                        account_name=account_name,
                        account_type=acc_type,
                        is_active=True,
                    )
                    db.add(gl)
                    added += 1
                print(f"Tenant {tenant.name} ({tenant.slug}): added {len(to_add)} GL accounts ({', '.join(c for c, _, _ in to_add)}).")

            await db.commit()
            print(f"\nDone. Added {added} GL accounts total.")
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_gl_accounts())
