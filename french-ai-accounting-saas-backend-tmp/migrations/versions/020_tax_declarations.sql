-- Migration 020: Tax Declarations
-- DouCompta V4.0 - Phase 4 (FISCA Agent)

-- =============================================================================
-- Tax Declarations
-- =============================================================================

CREATE TABLE IF NOT EXISTS tax_declarations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dossier_id UUID REFERENCES client_dossiers(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('CA3', 'CA12', 'IS', 'CVAE', 'CFE', 'DAS2')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'computed', 'validated', 'submitted', 'accepted', 'rejected')),
    computed_data JSONB DEFAULT '{}',
    total_amount DECIMAL(15,2) DEFAULT 0,
    edi_file_path VARCHAR(500),
    edi_transmission_id VARCHAR(100),
    submitted_at TIMESTAMPTZ,
    submitted_by UUID REFERENCES users(id),
    validated_by UUID REFERENCES users(id),
    validated_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Tax Calendar
-- =============================================================================

CREATE TABLE IF NOT EXISTS tax_calendar (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dossier_id UUID REFERENCES client_dossiers(id),
    declaration_type VARCHAR(20) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'due', 'overdue', 'completed', 'skipped')),
    declaration_id UUID REFERENCES tax_declarations(id),
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Indexes
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_tax_declarations_tenant ON tax_declarations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tax_declarations_type ON tax_declarations(type, status);
CREATE INDEX IF NOT EXISTS idx_tax_declarations_period ON tax_declarations(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_tax_declarations_dossier ON tax_declarations(dossier_id);
CREATE INDEX IF NOT EXISTS idx_tax_calendar_tenant ON tax_calendar(tenant_id, due_date);
CREATE INDEX IF NOT EXISTS idx_tax_calendar_status ON tax_calendar(status, due_date);
CREATE INDEX IF NOT EXISTS idx_tax_calendar_dossier ON tax_calendar(dossier_id);
