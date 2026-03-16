# -----------------------------------------------------------------------------
# Ensure gautamnancy324@gmail.com exists with password Nancy@2323 and Admin role.
# Run after seed_data when this user was not in the initial seed.
# Usage: docker compose -f infrastructure/docker-compose.yml run --rm -e DATABASE_URL=postgresql+asyncpg://dou_user:dou_password123@postgres:5432/dou_expense_audit auth python scripts/ensure_nancy_user.py
# -----------------------------------------------------------------------------
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from common.models import User, Tenant, Role, UserRole
from services.auth.utils import get_password_hash
import uuid

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv("SEED_DATABASE_URL", "postgresql+asyncpg://dou_user:dou_password123@postgres:5432/dou_expense_audit"),
)
if DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+asyncpg"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "gautamnancy324@gmail.com", User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if user:
            print("User gautamnancy324@gmail.com already exists. Login with password Nancy@2323")
            return

        # Get default tenant
        result = await db.execute(select(Tenant).where(Tenant.slug == "default", Tenant.deleted_at.is_(None)))
        tenant = result.scalar_one_or_none()
        if not tenant:
            print("No default tenant found. Run seed_data.py first.")
            return

        # Get admin role (lowercase to match PRD/seed_roles)
        result = await db.execute(select(Role).where(Role.tenant_id == tenant.id, Role.name == "admin", Role.deleted_at.is_(None)))
        admin_role = result.scalar_one_or_none()
        if not admin_role:
            print("Admin role not found. Run seed_roles.py first.")
            return

        new_user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email="gautamnancy324@gmail.com",
            first_name="Nancy",
            last_name="Gautam",
            password_hash=get_password_hash("Nancy@2323"),
            status="active",
        )
        db.add(new_user)
        await db.flush()
        db.add(UserRole(user_id=new_user.id, role_id=admin_role.id))
        await db.commit()
        print("Created user gautamnancy324@gmail.com with password Nancy@2323 (Admin role). You can sign in now.")


if __name__ == "__main__":
    asyncio.run(main())
