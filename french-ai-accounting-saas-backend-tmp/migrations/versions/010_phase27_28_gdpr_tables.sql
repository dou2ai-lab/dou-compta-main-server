-- Migration: Phase 27 & 28 - GDPR Compliance and Mobile App Support
-- Dou Expense & Audit AI – France Edition
-- GDPR Compliance, Retention Rules, Privacy Logging, Offline Support

-- ============================================================================
-- DATA SUBJECT REQUESTS (GDPR Article 15, 16, 17, 20)
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_subject_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Request details
    request_type VARCHAR(50) NOT NULL, -- access, rectification, erasure, portability
    subject_email VARCHAR(255) NOT NULL,
    subject_name VARCHAR(255),
    subject_id UUID REFERENCES users(id),
    
    -- Request status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, rejected
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Response
    response_data JSONB, -- Exported data
    response_file_path VARCHAR(500), -- Path to exported file
    
    -- Verification
    verification_token VARCHAR(100) UNIQUE,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Processing
    processed_by UUID REFERENCES users(id),
    rejection_reason TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_data_subject_requests_tenant_id ON data_subject_requests(tenant_id);
CREATE INDEX idx_data_subject_requests_subject_email ON data_subject_requests(subject_email);
CREATE INDEX idx_data_subject_requests_subject_id ON data_subject_requests(subject_id);
CREATE INDEX idx_data_subject_requests_status ON data_subject_requests(status);
CREATE INDEX idx_data_subject_requests_verification_token ON data_subject_requests(verification_token);
CREATE INDEX idx_data_subject_requests_requested_at ON data_subject_requests(requested_at DESC);

-- ============================================================================
-- RETENTION RULES
-- ============================================================================

CREATE TABLE IF NOT EXISTS retention_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Rule details
    entity_type VARCHAR(100) NOT NULL, -- expense, receipt, user, log, etc.
    retention_years INTEGER NOT NULL,
    retention_days INTEGER, -- Additional days if needed
    
    -- Action
    action_on_expiry VARCHAR(50) NOT NULL DEFAULT 'archive', -- archive, delete, anonymize
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_retention_rules_tenant_id ON retention_rules(tenant_id);
CREATE INDEX idx_retention_rules_entity_type ON retention_rules(entity_type);
CREATE INDEX idx_retention_rules_is_active ON retention_rules(is_active);
CREATE INDEX idx_retention_rules_next_run_at ON retention_rules(next_run_at);

-- ============================================================================
-- PRIVACY LOGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS privacy_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Access details
    accessed_by UUID NOT NULL REFERENCES users(id),
    entity_type VARCHAR(100) NOT NULL, -- expense, receipt, user, etc.
    entity_id UUID NOT NULL,
    
    -- Access type
    access_type VARCHAR(50) NOT NULL, -- read, update, delete, export
    contains_pii BOOLEAN NOT NULL DEFAULT false,
    
    -- Context
    ip_address VARCHAR(45), -- IPv4 or IPv6
    user_agent TEXT,
    request_path VARCHAR(500),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_privacy_logs_tenant_id ON privacy_logs(tenant_id);
CREATE INDEX idx_privacy_logs_accessed_by ON privacy_logs(accessed_by);
CREATE INDEX idx_privacy_logs_entity ON privacy_logs(entity_type, entity_id);
CREATE INDEX idx_privacy_logs_created_at ON privacy_logs(created_at DESC);
CREATE INDEX idx_privacy_logs_contains_pii ON privacy_logs(contains_pii) WHERE contains_pii = true;

-- ============================================================================
-- DATA MINIMIZATION JOBS
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_minimization_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Job details
    entity_type VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL, -- anonymize, delete, archive
    records_processed INTEGER DEFAULT 0,
    records_affected INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Error handling
    error_message TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_minimization_jobs_tenant_id ON data_minimization_jobs(tenant_id);
CREATE INDEX idx_data_minimization_jobs_status ON data_minimization_jobs(status);
CREATE INDEX idx_data_minimization_jobs_created_at ON data_minimization_jobs(created_at DESC);




