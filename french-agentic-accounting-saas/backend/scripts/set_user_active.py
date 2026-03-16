#!/usr/bin/env python3
"""Set a user's status to active by email. Usage: python scripts/set_user_active.py admin@example.com"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from common.models import User

_raw = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
if _raw.startswith("postgresql://") and "+asyncpg" not in _raw:
    DATABASE_URL = _raw.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = _raw


async def main():
    email = (sys.argv[1] or "").strip()
    if not email:
        print("Usage: python scripts/set_user_active.py <email>")
        print("Example: python scripts/set_user_active.py admin@example.com")
        sys.exit(1)

    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if not user:
            print(f"User not found: {email}")
            sys.exit(1)
        if user.status == "active":
            print(f"User {email} is already active.")
            return
        user.status = "active"
        await session.commit()
        print(f"✅ Set {email} to active.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
