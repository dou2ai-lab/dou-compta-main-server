-- Migration 018: Client Dossiers & Enhanced Notifications
-- DouCompta V4.0 - Phase 2

-- =============================================================================
-- Client Dossiers (PRD 5.14)
-- =============================================================================

CREATE TABLE IF NOT EXISTS client_dossiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    client_name VARCHAR(255) NOT NULL,
    siren VARCHAR(9),
    siret VARCHAR(14),
    legal_form VARCHAR(50), -- SARL, SAS, SA, EI, EURL, SCI, etc.
    naf_code VARCHAR(10),
    fiscal_year_start DATE,
    fiscal_year_end DATE,
    regime_tva VARCHAR(20) DEFAULT 'reel_normal' CHECK (regime_tva IN ('reel_normal', 'reel_simplifie', 'mini_reel', 'franchise')),
    regime_is VARCHAR(20) DEFAULT 'is_normal' CHECK (regime_is IN ('is_normal', 'is_pme', 'ir', 'micro')),
    accountant_id UUID REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'suspended')),
    settings JSONB DEFAULT '{}',
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    postal_code VARCHAR(10),
    city VARCHAR(100),
    country VARCHAR(2) DEFAULT 'FR',
    phone VARCHAR(20),
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dossier_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES client_dossiers(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL, -- kbis, statuts, rib, declaration, bilan, etc.
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dossier_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES client_dossiers(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- created, updated, document_added, declaration_filed, etc.
    title VARCHAR(255) NOT NULL,
    description TEXT,
    performed_by UUID REFERENCES users(id),
    entity_type VARCHAR(50),
    entity_id UUID,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Enhanced Notifications (PRD 5.15)
-- =============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(50) NOT NULL, -- expense_approved, declaration_due, anomaly_detected, document_received, etc.
    title VARCHAR(255) NOT NULL,
    body TEXT,
    channel VARCHAR(20) DEFAULT 'in_app' CHECK (channel IN ('in_app', 'email', 'both')),
    status VARCHAR(20) DEFAULT 'unread' CHECK (status IN ('unread', 'read', 'archived', 'dismissed')),
    priority VARCHAR(10) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    entity_type VARCHAR(50),
    entity_id UUID,
    action_url VARCHAR(500),
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    event_type VARCHAR(50) NOT NULL, -- expense.approved, declaration.due, anomaly.detected, etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    condition JSONB DEFAULT '{}', -- conditions to evaluate before triggering
    channels JSONB DEFAULT '["in_app"]', -- channels to deliver through
    template VARCHAR(100), -- notification template key
    is_active BOOLEAN DEFAULT TRUE,
    escalation_config JSONB, -- {"delay_minutes": 60, "escalate_to": "manager", "max_escalations": 3}
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Domain Events Log (for event bus audit trail)
-- =============================================================================

CREATE TABLE IF NOT EXISTS domain_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    event_type VARCHAR(100) NOT NULL,
    aggregate_type VARCHAR(50), -- expense, journal_entry, declaration, dossier
    aggregate_id UUID,
    payload JSONB NOT NULL DEFAULT '{}',
    published_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'processed', 'failed')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- =============================================================================
-- Indexes
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_client_dossiers_tenant ON client_dossiers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_client_dossiers_siren ON client_dossiers(siren);
CREATE INDEX IF NOT EXISTS idx_client_dossiers_accountant ON client_dossiers(accountant_id);
CREATE INDEX IF NOT EXISTS idx_dossier_documents_dossier ON dossier_documents(dossier_id);
CREATE INDEX IF NOT EXISTS idx_dossier_timeline_dossier ON dossier_timeline(dossier_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_notifications_tenant ON notifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_rules_tenant ON notification_rules(tenant_id, event_type);
CREATE INDEX IF NOT EXISTS idx_domain_events_type ON domain_events(event_type, status);
CREATE INDEX IF NOT EXISTS idx_domain_events_aggregate ON domain_events(aggregate_type, aggregate_id);
