-- Migration 021: Financial Analysis & Forecasting
-- DouCompta V4.0 - Phase 5 (FINA + FORECASTA Agents)

CREATE TABLE IF NOT EXISTS financial_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dossier_id UUID REFERENCES client_dossiers(id),
    snapshot_date DATE NOT NULL,
    fiscal_year INTEGER NOT NULL,
    sig_data JSONB DEFAULT '{}',
    ratios JSONB DEFAULT '{}',
    scoring JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    type VARCHAR(50) NOT NULL, -- cash_position, revenue, expenses
    horizon_days INTEGER NOT NULL, -- 7, 30, 90
    forecast_date DATE NOT NULL,
    data_points JSONB DEFAULT '[]',
    confidence DECIMAL(5,4) DEFAULT 0,
    model_used VARCHAR(50), -- linear, arima, prophet
    parameters JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    parameters JSONB NOT NULL DEFAULT '{}',
    results JSONB DEFAULT '{}',
    base_snapshot_id UUID REFERENCES financial_snapshots(id),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_financial_snapshots_tenant ON financial_snapshots(tenant_id, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_forecasts_tenant ON forecasts(tenant_id, type);
CREATE INDEX IF NOT EXISTS idx_scenarios_tenant ON scenarios(tenant_id);
