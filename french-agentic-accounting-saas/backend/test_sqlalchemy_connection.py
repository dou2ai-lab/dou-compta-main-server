"""Test SQLAlchemy connection"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from common.models import User, Tenant

DATABASE_URL = "postgresql+asyncpg://dou_user:dou_password123@localhost:5432/dou_expense_audit"

async def test():
    try:
        print("Creating engine...")
        engine = create_async_engine(
            DATABASE_URL,
            echo=True,
            pool_pre_ping=True
        )
        
        print("Creating session...")
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with AsyncSessionLocal() as db:
            print("Testing simple query...")
            result = await db.execute(text("SELECT 1"))
            print(f"Simple query result: {result.scalar()}")
            
            print("Testing user query...")
            user_result = await db.execute(
                select(User).where(User.email == 'admin@example.com')
            )
            user = user_result.scalar_one_or_none()
            
            if user:
                print(f"User found: {user.email}")
                print(f"User status: {user.status}")
                print(f"User tenant_id: {user.tenant_id}")
            else:
                print("User not found")
            
            if user:
                print("Testing tenant query...")
                tenant_result = await db.execute(
                    select(Tenant).where(Tenant.id == user.tenant_id)
                )
                tenant = tenant_result.scalar_one_or_none()
                
                if tenant:
                    print(f"Tenant found: {tenant.name}")
                else:
                    print("Tenant not found")
        
        await engine.dispose()
        print("Success!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test())
