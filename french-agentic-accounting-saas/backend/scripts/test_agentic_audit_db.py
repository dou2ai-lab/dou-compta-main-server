"""Quick DB checks for Agentic Audit: schema + knowledge_documents."""
import asyncio
import os
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
from dotenv import load_dotenv
load_dotenv(backend_root / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
if "asyncpg" not in DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text

    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.connect() as conn:
        # 1) expense columns
        r = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'expenses'
            AND column_name IN ('risk_score_line','is_anomaly','anomaly_reasons')
            ORDER BY column_name
        """))
        cols = [row[0] for row in r.fetchall()]
        print("1. expenses risk columns:", cols if cols else "MISSING")
        ok1 = len(cols) == 3

        # 2) new tables
        r = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('risk_scores','knowledge_documents','audit_report_narratives')
            ORDER BY table_name
        """))
        tables = [row[0] for row in r.fetchall()]
        print("2. new tables:", tables if tables else "MISSING")
        ok2 = len(tables) == 3

        # 3) knowledge_documents count
        r = await conn.execute(text("SELECT COUNT(*) FROM knowledge_documents WHERE deleted_at IS NULL"))
        n = r.scalar() or 0
        print("3. knowledge_documents count:", n)
        ok3 = n >= 1

        # 4) tenants
        r = await conn.execute(text("SELECT COUNT(*) FROM tenants WHERE deleted_at IS NULL"))
        tenants = r.scalar() or 0
        print("4. tenants:", tenants)

        # 5) expenses count
        r = await conn.execute(text("SELECT COUNT(*) FROM expenses WHERE deleted_at IS NULL"))
        exp_count = r.scalar() or 0
        print("5. expenses (in scope):", exp_count)

    print("\nSchema + ingest OK:" if (ok1 and ok2 and ok3) else "\nSome checks failed.")
    return 0 if (ok1 and ok2 and ok3) else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
