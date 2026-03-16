# -----------------------------------------------------------------------------
# File: seed_categories.py
# Description: Seed default expense categories for tenants that have none
# -----------------------------------------------------------------------------

"""
Add default expense categories from the backend for all tenants that have no categories.

Run from project root:
  python backend/scripts/seed_categories.py   (uses DATABASE_URL from backend/.env)

If you use Docker Postgres and get "password authentication failed" from the host, run
inside the admin container instead (same network as Postgres):
  scripts/seed-categories-docker.ps1
  or: docker exec dou-admin python scripts/seed_categories.py
"""
import asyncio
import os
import sys
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend_dir))

# Load backend/.env so DATABASE_URL matches your local credentials
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
from services.admin.models import ExpenseCategory

import common.models  # noqa: F401
import services.admin.models  # noqa: F401

_raw = os.getenv("DATABASE_URL")
if not _raw:
    print("DATABASE_URL not set. Set it in backend/.env or the environment.")
    sys.exit(1)
DATABASE_URL = _raw.replace("postgresql://", "postgresql+asyncpg://", 1) if _raw.startswith("postgresql://") else _raw

# (display_name, code, description) – display_name shown in dropdowns
DEFAULT_CATEGORIES = [
    ("Meals", "meals", "Meals and food"),
    ("Travel", "travel", "Travel"),
    ("Accommodation", "accommodation", "Accommodation and lodging"),
    ("Transport", "transport", "Transport, taxi, fuel, parking"),
    ("Office", "office", "Office supplies and equipment"),
    ("Training", "training", "Training and education"),
    ("Client gifts", "client_gifts", "Client gifts and donations"),
    ("Communications", "communications", "Communications and telecom"),
    ("Professional", "professional", "Professional services"),
    ("Facilities", "facilities", "Facilities and maintenance"),
]


async def seed_categories():
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
                result = await db.execute(
                    select(ExpenseCategory).where(
                        ExpenseCategory.tenant_id == tenant.id,
                        ExpenseCategory.deleted_at.is_(None),
                    )
                )
                existing_cats = result.scalars().all()
                existing_codes = {c.code.lower() for c in existing_cats}
                code_to_display = {code: display_name for display_name, code, _ in DEFAULT_CATEGORIES}
                # Update display names for existing categories (e.g. "travel" -> "Travel")
                for cat in existing_cats:
                    display_name = code_to_display.get(cat.code.lower())
                    if display_name and cat.name != display_name:
                        cat.name = display_name
                        added += 1
                to_add = [(display_name, code, desc) for display_name, code, desc in DEFAULT_CATEGORIES if code.lower() not in existing_codes]
                for display_name, code, desc in to_add:
                    cat = ExpenseCategory(
                        tenant_id=tenant.id,
                        name=display_name,
                        code=code,
                        description=desc,
                        is_active=True,
                    )
                    db.add(cat)
                    added += 1
                if to_add or code_to_display:
                    print(f"Tenant {tenant.name} ({tenant.slug}): added {len(to_add)} categories, updated display names for existing.")

            await db.commit()
            print(f"\nDone. Added {added} categories total.")
        except Exception as e:
            await db.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_categories())
