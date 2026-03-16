"""Create database tables"""
import asyncio
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from common.models import Base

# Import all SQLAlchemy models so they register with Base.metadata (required for FK refs)
import common.models  # noqa: F401
import services.admin.models  # noqa: F401 - ExpensePolicy, expense_categories, gl_accounts, vat_rules
import services.file_service.models  # noqa: F401 - ReceiptDocument (receipt_documents)
import services.audit.models  # noqa: F401 - AuditReport, audit_metadata, audit_evidence, etc.
import services.file_service.models  # noqa: F401 - ReceiptDocument (receipt_documents)

# Use DATABASE_URL from env (Docker: postgres:5432) or fallback for local
_raw = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
if _raw.startswith("postgresql://") and "+asyncpg" not in _raw:
    DATABASE_URL = _raw.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = _raw

async def _ensure_activity_table(conn):
    """Create user_management_activities if missing (fallback when model was added after image build)."""
    from sqlalchemy import text
    result = await conn.execute(text(
        "SELECT to_regclass('public.user_management_activities')"
    ))
    if result.scalar() is not None:
        return
    await conn.execute(text("""
        CREATE TABLE user_management_activities (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            performed_by_id UUID NOT NULL REFERENCES users(id),
            action VARCHAR(80) NOT NULL,
            target_user_id UUID REFERENCES users(id),
            target_role_id UUID REFERENCES roles(id),
            details JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
    """))
    print("Created table: user_management_activities")


async def _ensure_settings_tables(conn):
    """Create tenant_settings and settings_changelog if missing (Settings page backend)."""
    from sqlalchemy import text
    for table in ("tenant_settings", "settings_changelog"):
        result = await conn.execute(text(f"SELECT to_regclass('public.{table}')"))
        if result.scalar() is not None:
            continue
        if table == "tenant_settings":
            await conn.execute(text("""
                CREATE TABLE tenant_settings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    CONSTRAINT unique_tenant_settings_tenant UNIQUE (tenant_id)
                )
            """))
        else:
            await conn.execute(text("""
                CREATE TABLE settings_changelog (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    changed_by UUID NOT NULL REFERENCES users(id),
                    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    section VARCHAR(50) NOT NULL,
                    action VARCHAR(20) NOT NULL DEFAULT 'update',
                    old_value JSONB,
                    new_value JSONB
                )
            """))
        print(f"Created table: {table}")


async def create_tables():
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await _ensure_activity_table(conn)
            await _ensure_settings_tables(conn)
        print("Tables created successfully!")
        await engine.dispose()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(create_tables())
