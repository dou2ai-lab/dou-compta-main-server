"""
Analysis Service - Business logic layer.
"""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date

from .models import FinancialSnapshot, Forecast, Scenario
from .sig_calculator import compute_sig
from .ratio_calculator import compute_ratios
from .scoring_engine import compute_score
from .cash_forecaster import forecast_cash

logger = structlog.get_logger()


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_snapshot(self, tenant_id: UUID, fiscal_year: int) -> FinancialSnapshot:
        sig = await compute_sig(self.db, tenant_id, fiscal_year)
        ratios = await compute_ratios(self.db, tenant_id, fiscal_year)
        scoring = compute_score(sig, ratios)

        snapshot = FinancialSnapshot(
            tenant_id=tenant_id,
            snapshot_date=date.today(),
            fiscal_year=fiscal_year,
            sig_data=sig,
            ratios=ratios,
            scoring=scoring,
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def get_latest_snapshot(self, tenant_id: UUID, fiscal_year: int):
        result = await self.db.execute(
            select(FinancialSnapshot).where(
                FinancialSnapshot.tenant_id == tenant_id,
                FinancialSnapshot.fiscal_year == fiscal_year,
            ).order_by(FinancialSnapshot.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def compute_forecast(self, tenant_id: UUID, horizon_days: int = 30) -> Forecast:
        data = await forecast_cash(self.db, tenant_id, horizon_days)
        forecast = Forecast(
            tenant_id=tenant_id,
            type=data["type"],
            horizon_days=horizon_days,
            forecast_date=date.today(),
            data_points=data["data_points"],
            confidence=data["confidence"],
            model_used=data["model_used"],
        )
        self.db.add(forecast)
        await self.db.flush()
        return forecast

    async def create_scenario(self, tenant_id: UUID, user_id: UUID, name: str, description: str, parameters: dict) -> Scenario:
        scenario = Scenario(
            tenant_id=tenant_id,
            name=name,
            description=description,
            parameters=parameters,
            results={},
            created_by=user_id,
        )
        self.db.add(scenario)
        await self.db.flush()
        return scenario

    async def list_scenarios(self, tenant_id: UUID) -> list[Scenario]:
        result = await self.db.execute(
            select(Scenario).where(Scenario.tenant_id == tenant_id)
            .order_by(Scenario.created_at.desc())
        )
        return list(result.scalars().all())
