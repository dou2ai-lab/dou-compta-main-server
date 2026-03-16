"""
Quick test script to verify database connection and check tables
"""
import asyncio
import asyncpg
import os
from pathlib import Path

# Load .env file if it exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
    except ImportError:
        # python-dotenv not installed, manually parse .env file
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip().strip('"').strip("'")
                    os.environ[key.strip()] = value

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")

async def test_connection():
    """Test database connection and list tables"""
    # Parse URL for asyncpg
    url = DATABASE_URL.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
    if '@' in url:
        auth, rest = url.split('@', 1)
        if ':' in auth:
            user, password = auth.split(':', 1)
        else:
            user = auth
            password = ""
        if '/' in rest:
            host_port, database = rest.split('/', 1)
        else:
            host_port = rest
            database = "dou_expense_audit"
        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 5433
    else:
        user = "dou_user"
        password = "dou_password123"
        host = "localhost"
        port = 5433
        database = "dou_expense_audit"
    
    print(f"[INFO] Connecting to: {host}:{port}, user: {user}, database: {database}")
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl=False
        )
        
        print("[SUCCESS] Database connection successful!")
        
        # List all tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        print(f"\n[INFO] Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Check if critical tables exist
        critical_tables = ['users', 'tenants', 'roles', 'user_roles']
        existing_tables = {t['table_name'] for t in tables}
        
        print(f"\n[INFO] Checking critical tables:")
        for table in critical_tables:
            if table in existing_tables:
                # Count rows
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"   [OK] {table}: {count} rows")
            else:
                print(f"   [MISSING] {table}: NOT FOUND")
        
        # Check for default tenant
        tenant_count = await conn.fetchval("SELECT COUNT(*) FROM tenants WHERE slug = 'default'")
        print(f"\n[INFO] Default tenant exists: {'Yes' if tenant_count > 0 else 'No'}")
        
        # Check for PRD employee role (lowercase)
        role_count = await conn.fetchval("SELECT COUNT(*) FROM roles WHERE name = 'employee'")
        print(f"[INFO] Employee role exists: {'Yes' if role_count > 0 else 'No'}")
        
        await conn.close()
        print("\n[SUCCESS] Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
