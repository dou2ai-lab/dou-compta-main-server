"""
Pydantic schemas for the Analysis Service API.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class SIGResponse(BaseModel):
    fiscal_year: int
    chiffre_affaires: Decimal = Decimal("0")
    marge_commerciale: Decimal = Decimal("0")
    valeur_ajoutee: Decimal = Decimal("0")
    ebe: Decimal = Decimal("0")  # Excedent Brut d'Exploitation
    resultat_exploitation: Decimal = Decimal("0")
    resultat_financier: Decimal = Decimal("0")
    resultat_courant: Decimal = Decimal("0")
    resultat_exceptionnel: Decimal = Decimal("0")
    resultat_net: Decimal = Decimal("0")


class RatiosResponse(BaseModel):
    fiscal_year: int
    bfr: Optional[Decimal] = None  # Besoin en Fonds de Roulement
    tresorerie_nette: Optional[Decimal] = None
    ratio_endettement: Optional[Decimal] = None
    ratio_liquidite: Optional[Decimal] = None
    rotation_stocks: Optional[Decimal] = None
    delai_clients: Optional[int] = None  # days
    delai_fournisseurs: Optional[int] = None  # days
    marge_nette: Optional[Decimal] = None
    rentabilite_capitaux: Optional[Decimal] = None


class ScoringResponse(BaseModel):
    overall_score: int  # 0-100
    category: str  # excellent, good, average, weak, critical
    components: dict  # {profitability: 80, liquidity: 70, ...}
    recommendations: List[str]


class ForecastDataPoint(BaseModel):
    date: date
    value: Decimal
    lower_bound: Optional[Decimal] = None
    upper_bound: Optional[Decimal] = None


class ForecastResponse(BaseModel):
    id: UUID
    type: str
    horizon_days: int
    forecast_date: date
    data_points: List[ForecastDataPoint]
    confidence: Decimal
    model_used: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: dict


class ScenarioResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    parameters: dict
    results: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SnapshotResponse(BaseModel):
    id: UUID
    snapshot_date: date
    fiscal_year: int
    sig_data: Optional[dict] = None
    ratios: Optional[dict] = None
    scoring: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
