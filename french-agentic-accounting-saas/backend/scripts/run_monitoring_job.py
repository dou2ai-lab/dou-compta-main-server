# -----------------------------------------------------------------------------
# run_monitoring_job.py – Run continuous monitoring job (5.2.1) without HTTP
# Usage: from backend folder: python scripts/run_monitoring_job.py [--limit 500] [--days 90]
# Or from repo root: python backend/scripts/run_monitoring_job.py
# -----------------------------------------------------------------------------

"""
Run anomaly + risk batch and persist to expenses and risk_scores.
No need for anomaly service to be running or for a JWT.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from dotenv import load_dotenv
load_dotenv(backend_root / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit",
)
if DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    from services.anomaly_service.service import AnomalyDetectionService

    parser = argparse.ArgumentParser(description="Run monitoring job (risk scores + anomaly persistence)")
    parser.add_argument("--limit", type=int, default=500, help="Max expenses to process")
    parser.add_argument("--days", type=int, default=90, help="Lookback days")
    args = parser.parse_args()

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        r = await session.execute(text("SELECT id FROM tenants WHERE deleted_at IS NULL LIMIT 1"))
        row = r.fetchone()
        if not row:
            print("No tenant found. Create a tenant first.")
            return
        tenant_id = str(row[0])
        print(f"Running monitoring job for tenant {tenant_id} (limit={args.limit}, lookback_days={args.days})...")
        service = AnomalyDetectionService(session, tenant_id)
        result = await service.run_batch_analysis_and_persist(limit=args.limit, lookback_days=args.days)
        await session.commit()
        print(f"Done: processed={result['processed']}, employees_updated={result['employees_updated']}, merchants_updated={result['merchants_updated']}")


if __name__ == "__main__":
    asyncio.run(main())
