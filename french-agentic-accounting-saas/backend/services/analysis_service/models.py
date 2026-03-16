"""
SQLAlchemy ORM models for the Analysis Service.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, DECIMAL, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.models import Base


class FinancialSnapshot(Base):
    __tablename__ = "financial_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    dossier_id = Column(UUID(as_uuid=True), ForeignKey("client_dossiers.id"))
    snapshot_date = Column(Date, nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    sig_data = Column(JSONB, default={})
    ratios = Column(JSONB, default={})
    scoring = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    type = Column(String(50), nullable=False)
    horizon_days = Column(Integer, nullable=False)
    forecast_date = Column(Date, nullable=False)
    data_points = Column(JSONB, default=[])
    confidence = Column(DECIMAL(5, 4), default=0)
    model_used = Column(String(50))
    parameters = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    parameters = Column(JSONB, nullable=False, default={})
    results = Column(JSONB, default={})
    base_snapshot_id = Column(UUID(as_uuid=True), ForeignKey("financial_snapshots.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
