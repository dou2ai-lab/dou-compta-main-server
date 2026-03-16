"""
Analysis Service API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
import structlog

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .service import AnalysisService
from .schemas import (
    SIGResponse, RatiosResponse, ScoringResponse,
    ForecastResponse, ScenarioCreate, ScenarioResponse, SnapshotResponse,
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/sig", response_model=SIGResponse)
async def get_sig(
    fiscal_year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AnalysisService(db)
    snapshot = await svc.get_latest_snapshot(current_user.tenant_id, fiscal_year)
    if not snapshot:
        snapshot = await svc.compute_snapshot(current_user.tenant_id, fiscal_year)
        await db.commit()
    return SIGResponse(**{k: v for k, v in snapshot.sig_data.items() if k != "fiscal_year"}, fiscal_year=fiscal_year)


@router.get("/ratios", response_model=RatiosResponse)
async def get_ratios(
    fiscal_year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AnalysisService(db)
    snapshot = await svc.get_latest_snapshot(current_user.tenant_id, fiscal_year)
    if not snapshot:
        snapshot = await svc.compute_snapshot(current_user.tenant_id, fiscal_year)
        await db.commit()
    return RatiosResponse(**{k: v for k, v in snapshot.ratios.items() if k != "fiscal_year"}, fiscal_year=fiscal_year)


@router.get("/scoring", response_model=ScoringResponse)
async def get_scoring(
    fiscal_year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AnalysisService(db)
    snapshot = await svc.get_latest_snapshot(current_user.tenant_id, fiscal_year)
    if not snapshot:
        snapshot = await svc.compute_snapshot(current_user.tenant_id, fiscal_year)
        await db.commit()
    return ScoringResponse(**snapshot.scoring)


@router.post("/snapshot", response_model=SnapshotResponse)
async def create_snapshot(
    fiscal_year: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AnalysisService(db)
    snapshot = await svc.compute_snapshot(current_user.tenant_id, fiscal_year)
    await db.commit()
    return SnapshotResponse(
        id=snapshot.id, snapshot_date=snapshot.snapshot_date,
        fiscal_year=snapshot.fiscal_year, sig_data=snapshot.sig_data,
        ratios=snapshot.ratios, scoring=snapshot.scoring,
        created_at=snapshot.created_at,
    )


@router.post("/forecast", response_model=ForecastResponse)
async def create_forecast(
    horizon_days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AnalysisService(db)
    forecast = await svc.compute_forecast(current_user.tenant_id, horizon_days)
    await db.commit()
    return ForecastResponse(
        id=forecast.id, type=forecast.type, horizon_days=forecast.horizon_days,
        forecast_date=forecast.forecast_date, data_points=forecast.data_points or [],
        confidence=forecast.confidence, model_used=forecast.model_used,
        created_at=forecast.created_at,
    )


@router.get("/scenarios", response_model=list[ScenarioResponse])
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AnalysisService(db)
    scenarios = await svc.list_scenarios(current_user.tenant_id)
    return [ScenarioResponse(
        id=s.id, name=s.name, description=s.description,
        parameters=s.parameters, results=s.results, created_at=s.created_at,
    ) for s in scenarios]


@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(
    payload: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = AnalysisService(db)
    scenario = await svc.create_scenario(
        current_user.tenant_id, current_user.id,
        payload.name, payload.description, payload.parameters,
    )
    await db.commit()
    return ScenarioResponse(
        id=scenario.id, name=scenario.name, description=scenario.description,
        parameters=scenario.parameters, results=scenario.results,
        created_at=scenario.created_at,
    )
