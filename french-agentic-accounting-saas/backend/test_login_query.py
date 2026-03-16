"""Test the exact login query"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from common.models import User, Tenant

DATABASE_URL = "postgresql+asyncpg://dou_user:dou_password123@localhost:5432/dou_expense_audit"

async def test_login_query():
    try:
        engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with AsyncSessionLocal() as db:
            # Test the exact query from login route
            print("Testing user query...")
            user_result = await db.execute(
                select(User)
                .where(User.email == 'admin@example.com', User.deleted_at.is_(None))
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                print("ERROR: User not found!")
                return
            
            print(f"User found: {user.email}, status: {user.status}, tenant_id: {user.tenant_id}")
            
            # Test tenant query
            print("Testing tenant query...")
            tenant_result = await db.execute(
                select(Tenant)
                .where(Tenant.id == user.tenant_id, Tenant.deleted_at.is_(None))
            )
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                print("ERROR: Tenant not found!")
                return
            
            print(f"Tenant found: {tenant.name}, status: {tenant.status}")
            print("SUCCESS: All queries work!")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_login_query())
