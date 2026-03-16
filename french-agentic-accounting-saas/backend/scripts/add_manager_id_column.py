"""
Add manager_id column to users table if it doesn't exist
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

async def add_manager_id_column():
    """Add manager_id column to users table"""
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
        
        print("[INFO] Checking if manager_id column exists...")
        
        # Check if column exists
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'manager_id'
            )
        """)
        
        if column_exists:
            print("[INFO] manager_id column already exists. Skipping.")
        else:
            print("[INFO] Adding manager_id column to users table...")
            await conn.execute("""
                ALTER TABLE users 
                ADD COLUMN manager_id UUID REFERENCES users(id) ON DELETE SET NULL;
            """)
            print("[SUCCESS] manager_id column added successfully!")
            
            # Create index
            print("[INFO] Creating index on manager_id...")
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id);
            """)
            print("[SUCCESS] Index created successfully!")
        
        await conn.close()
        print("\n[SUCCESS] Operation completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Operation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(add_manager_id_column())
