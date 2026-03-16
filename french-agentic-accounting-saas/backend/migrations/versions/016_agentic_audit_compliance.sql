-- Migration: 016 - Agentic Audit & Compliance Module
-- Risk scoring on expenses, employee/merchant risk, knowledge documents for RAG

-- ============================================================================
-- EXPENSES: risk and anomaly fields (5.2.2)
-- ============================================================================

ALTER TABLE expenses
  ADD COLUMN IF NOT EXISTS risk_score_line DECIMAL(5, 4),  -- 0.0000 to 1.0000
  ADD COLUMN IF NOT EXISTS is_anomaly BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS anomaly_reasons JSONB DEFAULT '[]'::jsonb;  -- e.g. ["ML_OUTLIER","MISSING_VAT","NEAR_APPROVAL_LIMIT"]

CREATE INDEX IF NOT EXISTS idx_expenses_risk_score_line ON expenses(risk_score_line DESC) WHERE risk_score_line IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_expenses_is_anomaly ON expenses(is_anomaly) WHERE is_anomaly = TRUE;

-- ============================================================================
-- RISK SCORES: per employee, per merchant (5.2.1 / 5.2.2)
-- ============================================================================

CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,  -- 'employee', 'merchant', 'expense_line'
    entity_id VARCHAR(255) NOT NULL,  -- user_id, merchant_name, or expense_id
    risk_score DECIMAL(5, 4) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,  -- e.g. expense_count, total_amount
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, entity_type, entity_id)
);

CREATE INDEX idx_risk_scores_tenant_entity ON risk_scores(tenant_id, entity_type);
CREATE INDEX idx_risk_scores_updated_at ON risk_scores(updated_at DESC);

-- ============================================================================
-- KNOWLEDGE DOCUMENTS: raw ingested content for RAG (5.2.5)
-- ============================================================================

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    source_url VARCHAR(1000),
    type VARCHAR(50) NOT NULL,  -- policy, VAT, URSSAF, GDPR, expense_rule
    language VARCHAR(10) DEFAULT 'fr',
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_knowledge_documents_tenant_id ON knowledge_documents(tenant_id);
CREATE INDEX idx_knowledge_documents_type ON knowledge_documents(type);
CREATE INDEX idx_knowledge_documents_deleted_at ON knowledge_documents(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- AUDIT REPORT NARRATIVES: stored narratives FR/EN (optional; 5.2.3)
-- audit_reports.narrative_sections JSONB already exists; this table for versioning/log
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_report_narratives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_report_id UUID NOT NULL REFERENCES audit_reports(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    section_key VARCHAR(100) NOT NULL,  -- executive_summary, introduction, etc.
    language VARCHAR(10) NOT NULL,  -- fr, en
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_report_narratives_report_id ON audit_report_narratives(audit_report_id);
CREATE INDEX idx_audit_report_narratives_tenant ON audit_report_narratives(tenant_id);

-- ============================================================================
-- CO-PILOT / AUDIT LOG: query and response audit trail (5.2.5 security)
-- qa_sessions already exists; optional extra logging table
-- ============================================================================

-- qa_sessions already stores query, answer, etc. No new table required.
-- Ensure we log in application layer for Co-Pilot queries.
