"""Test database connection"""
import asyncio
import asyncpg
import sys

async def test_connection():
    try:
        print("Testing database connection...")
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='dou_user',
            password='dou_password123',
            database='dou_expense_audit'
        )
        print("✅ Connected successfully!")
        
        # Test query
        user = await conn.fetchrow(
            "SELECT email, password_hash, status FROM users WHERE email = $1",
            'admin@example.com'
        )
        
        if user:
            print(f"✅ User found: {user['email']}")
            print(f"   Status: {user['status']}")
            print(f"   Has password hash: {bool(user['password_hash'])}")
            print(f"   Hash length: {len(user['password_hash']) if user['password_hash'] else 0}")
        else:
            print("❌ User not found")
        
        await conn.close()
        print("✅ Connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_connection())
