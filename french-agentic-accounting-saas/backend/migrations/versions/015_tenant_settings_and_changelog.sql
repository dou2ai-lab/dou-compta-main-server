-- Migration: Tenant Settings and Settings Changelog
-- Dou Expense & Audit AI – France Edition
-- Company settings per tenant and audit of changes

-- ============================================================================
-- TENANT SETTINGS (one row per tenant)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tenant_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    -- JSONB sections: general, users, security, notifications, billing
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tenant_settings_tenant UNIQUE (tenant_id)
);

CREATE INDEX IF NOT EXISTS idx_tenant_settings_tenant_id ON tenant_settings(tenant_id);

COMMENT ON TABLE tenant_settings IS 'Company-wide settings per tenant (general, users, security, notifications, billing)';

-- ============================================================================
-- SETTINGS CHANGELOG (audit of settings changes)
-- ============================================================================

CREATE TABLE IF NOT EXISTS settings_changelog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    changed_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    section VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL DEFAULT 'update',
    old_value JSONB,
    new_value JSONB
);

CREATE INDEX IF NOT EXISTS idx_settings_changelog_tenant_id ON settings_changelog(tenant_id);
CREATE INDEX IF NOT EXISTS idx_settings_changelog_changed_at ON settings_changelog(changed_at DESC);

COMMENT ON TABLE settings_changelog IS 'Audit log of company settings changes for Change Log view';
