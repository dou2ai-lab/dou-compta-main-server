# -----------------------------------------------------------------------------
# File: run_migration.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 30-11-2025
# Description: Script to run SQL migrations directly
# -----------------------------------------------------------------------------

"""
Script to run SQL migrations
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://dou_user:dou_password@postgres:5432/dou_expense_audit")

async def run_migration(migration_file: str):
    """Run a SQL migration file"""
    # Parse database URL
    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
    else:
        db_url = DATABASE_URL
    
    # Extract connection details
    import urllib.parse
    parsed = urllib.parse.urlparse(db_url)
    
    conn = await asyncpg.connect(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        user=parsed.username or "dou_user",
        password=parsed.password or "dou_password",
        database=parsed.path[1:] if parsed.path else "dou_expense_audit"
    )
    
    try:
        # Read migration file
        migration_path = Path(__file__).parent.parent / "migrations" / "versions" / migration_file
        if not migration_path.exists():
            print(f"❌ Migration file not found: {migration_path}")
            return False
        
        print(f"📄 Reading migration file: {migration_file}")
        sql_content = migration_path.read_text(encoding='utf-8')
        
        # Execute migration
        print(f"🚀 Running migration: {migration_file}")
        await conn.execute(sql_content)
        
        print(f"✅ Migration completed successfully: {migration_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        print("Example: python run_migration.py 004_phase4_admin_tables.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    success = asyncio.run(run_migration(migration_file))
    sys.exit(0 if success else 1)




























