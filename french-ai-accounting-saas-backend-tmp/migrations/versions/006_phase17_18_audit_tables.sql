-- Migration: Phase 17 & 18 - Audit Report Tables
-- Dou Expense & Audit AI – France Edition
-- Audit Module Foundation, Evidence Collection

-- ============================================================================
-- AUDIT REPORTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id),
    
    -- Report identification
    report_number VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Period-based scope
    audit_period_start DATE NOT NULL,
    audit_period_end DATE NOT NULL,
    period_type VARCHAR(50), -- monthly, quarterly, annual, custom
    
    -- Report structure
    report_type VARCHAR(50) NOT NULL DEFAULT 'technical', -- technical, narrative, combined
    template_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    
    -- Status and workflow
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, in_progress, completed, published
    completed_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    technical_data JSONB DEFAULT '{}'::jsonb, -- Structured technical findings
    narrative_sections JSONB DEFAULT '{}'::jsonb, -- Narrative text sections
    
    -- Sample information
    sample_size INTEGER DEFAULT 0,
    total_expenses_in_scope INTEGER DEFAULT 0,
    total_amount_in_scope DECIMAL(12, 2) DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_audit_reports_tenant_id ON audit_reports(tenant_id);
CREATE INDEX idx_audit_reports_created_by ON audit_reports(created_by);
CREATE INDEX idx_audit_reports_status ON audit_reports(status);
CREATE INDEX idx_audit_reports_period ON audit_reports(audit_period_start, audit_period_end);
CREATE INDEX idx_audit_reports_report_number ON audit_reports(report_number);
CREATE INDEX idx_audit_reports_deleted_at ON audit_reports(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_audit_reports_created_at ON audit_reports(created_at DESC);

-- ============================================================================
-- AUDIT METADATA
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_report_id UUID NOT NULL REFERENCES audit_reports(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Metadata fields
    key VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    data_type VARCHAR(50), -- string, number, date, json, array
    
    -- Tracking
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_metadata_report_id ON audit_metadata(audit_report_id);
CREATE INDEX idx_audit_metadata_tenant_id ON audit_metadata(tenant_id);
CREATE INDEX idx_audit_metadata_key ON audit_metadata(key);

-- ============================================================================
-- AUDIT EVIDENCE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_report_id UUID NOT NULL REFERENCES audit_reports(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Linked entities
    expense_id UUID REFERENCES expenses(id),
    receipt_id UUID, -- Reference to receipt_documents
    approval_step_id UUID, -- Reference to approval_steps
    
    -- Evidence details
    evidence_type VARCHAR(50) NOT NULL, -- receipt, approval_chain, expense_data, policy_violation
    evidence_category VARCHAR(50), -- primary, supporting, reference
    description TEXT,
    
    -- File information
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    storage_provider VARCHAR(50), -- s3, gcs, azure, local
    storage_key VARCHAR(500),
    
    -- Evidence metadata
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    collected_by UUID NOT NULL REFERENCES users(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT fk_audit_evidence_collected_by FOREIGN KEY (collected_by) REFERENCES users(id)
);

CREATE INDEX idx_audit_evidence_report_id ON audit_evidence(audit_report_id);
CREATE INDEX idx_audit_evidence_tenant_id ON audit_evidence(tenant_id);
CREATE INDEX idx_audit_evidence_expense_id ON audit_evidence(expense_id);
CREATE INDEX idx_audit_evidence_receipt_id ON audit_evidence(receipt_id);
CREATE INDEX idx_audit_evidence_type ON audit_evidence(evidence_type);
CREATE INDEX idx_audit_evidence_collected_at ON audit_evidence(collected_at DESC);

-- ============================================================================
-- AUDIT SCOPE
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_scopes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_report_id UUID NOT NULL REFERENCES audit_reports(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Scope criteria
    scope_type VARCHAR(50) NOT NULL, -- period, department, employee, merchant, category
    scope_value VARCHAR(255), -- Value for the scope type
    scope_criteria JSONB DEFAULT '{}'::jsonb, -- Complex criteria
    
    -- Inclusion/exclusion
    is_included BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER DEFAULT 0, -- Higher priority = more important
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_scopes_report_id ON audit_scopes(audit_report_id);
CREATE INDEX idx_audit_scopes_tenant_id ON audit_scopes(tenant_id);
CREATE INDEX idx_audit_scopes_type ON audit_scopes(scope_type);




