-- Migration: Phase 19 & 20 - Audit Trail and Report Generation
-- Dou Expense & Audit AI – France Edition
-- Audit Trail Tracking and Basic Report Generator

-- ============================================================================
-- AUDIT TRAILS
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_trails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Entity tracking
    entity_type VARCHAR(50) NOT NULL, -- receipt, expense, approval, etc.
    entity_id VARCHAR(255) NOT NULL, -- UUID as string for flexibility
    
    -- Action tracking
    action VARCHAR(50) NOT NULL, -- added, modified, approved, extracted, deleted
    performed_by UUID NOT NULL REFERENCES users(id),
    performed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_audit_trails_tenant_id ON audit_trails(tenant_id);
CREATE INDEX idx_audit_trails_entity ON audit_trails(entity_type, entity_id);
CREATE INDEX idx_audit_trails_action ON audit_trails(action);
CREATE INDEX idx_audit_trails_performed_by ON audit_trails(performed_by);
CREATE INDEX idx_audit_trails_performed_at ON audit_trails(performed_at DESC);

-- ============================================================================
-- AUDIT SNAPSHOTS (Immutable Storage)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Entity reference
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    audit_trail_id UUID NOT NULL REFERENCES audit_trails(id) ON DELETE CASCADE,
    
    -- Snapshot data
    action VARCHAR(50) NOT NULL,
    snapshot_data JSONB NOT NULL, -- Immutable snapshot of entity state
    snapshot_hash VARCHAR(64) NOT NULL, -- SHA-256 hash for integrity verification
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_snapshots_tenant_id ON audit_snapshots(tenant_id);
CREATE INDEX idx_audit_snapshots_entity ON audit_snapshots(entity_type, entity_id);
CREATE INDEX idx_audit_snapshots_trail_id ON audit_snapshots(audit_trail_id);
CREATE INDEX idx_audit_snapshots_hash ON audit_snapshots(snapshot_hash);
CREATE INDEX idx_audit_snapshots_created_at ON audit_snapshots(created_at DESC);

-- Add unique constraint on hash to prevent tampering
CREATE UNIQUE INDEX IF NOT EXISTS idx_audit_snapshots_unique_hash ON audit_snapshots(snapshot_hash);




