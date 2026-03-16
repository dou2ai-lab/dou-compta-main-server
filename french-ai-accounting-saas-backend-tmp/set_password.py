"""
One-off script to set or reset password for a user (e.g. gautamnancy324@gmail.com).
Run from backend dir: python set_password.py
Uses DATABASE_URL from env or default postgresql+asyncpg://dou_user:dou_password@localhost:5432/dou_expense_audit
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from common.models import User, Tenant
from services.auth.utils import get_password_hash

# Default: local Postgres (use 5433 if using infrastructure/docker-compose)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dou_user:dou_password@localhost:5432/dou_expense_audit",
)

EMAIL = "gautamnancy324@gmail.com"
NEW_PASSWORD = "Nancy@123"


async def set_password():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            result = await session.execute(
                select(User).where(User.email == EMAIL, User.deleted_at.is_(None))
            )
            user = result.scalar_one_or_none()

            if not user:
                # Get default tenant and create user
                tenant_result = await session.execute(
                    select(Tenant).where(Tenant.slug == "default", Tenant.deleted_at.is_(None))
                )
                tenant = tenant_result.scalar_one_or_none()
                if not tenant:
                    print("No default tenant found. Run seed_data.py first.")
                    return
                import uuid
                user = User(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    email=EMAIL,
                    first_name="Nancy",
                    last_name="User",
                    password_hash=get_password_hash(NEW_PASSWORD),
                    status="active",
                )
                session.add(user)
                await session.flush()
                await session.commit()
                print(f"Created user {EMAIL} with password '{NEW_PASSWORD}'.")
                return
            else:
                user.password_hash = get_password_hash(NEW_PASSWORD)
                await session.commit()
                print(f"Password updated for {EMAIL}. You can now log in with '{NEW_PASSWORD}'.")
        except Exception as e:
            await session.rollback()
            print(f"Error: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(set_password())
