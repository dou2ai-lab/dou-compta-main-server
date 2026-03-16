-- Migration: Phase 29 & 30 - Performance Indexes and Security Enhancements
-- Dou Expense & Audit AI – France Edition
-- Performance optimization and security hardening

-- ============================================================================
-- PERFORMANCE INDEXES (Phase 29)
-- ============================================================================

-- Expenses table indexes
CREATE INDEX IF NOT EXISTS idx_expenses_tenant_status ON expenses(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_expenses_tenant_date ON expenses(tenant_id, expense_date DESC);
CREATE INDEX IF NOT EXISTS idx_expenses_submitted_by_status ON expenses(submitted_by, status);
CREATE INDEX IF NOT EXISTS idx_expenses_approval_status ON expenses(approval_status) WHERE approval_status = 'pending';
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_merchant ON expenses(merchant_name);
CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_expenses_amount ON expenses(amount) WHERE amount > 0;

-- Receipts table indexes
CREATE INDEX IF NOT EXISTS idx_receipts_tenant_status ON receipts(tenant_id, ocr_status);
CREATE INDEX IF NOT EXISTS idx_receipts_uploaded_by ON receipts(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_receipts_created_at ON receipts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_receipts_file_hash ON receipts(file_hash) WHERE file_hash IS NOT NULL;

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id) WHERE manager_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login_at DESC) WHERE last_login_at IS NOT NULL;

-- Policy violations table indexes
CREATE INDEX IF NOT EXISTS idx_policy_violations_expense ON policy_violations(expense_id);
CREATE INDEX IF NOT EXISTS idx_policy_violations_severity ON policy_violations(violation_severity);
CREATE INDEX IF NOT EXISTS idx_policy_violations_created_at ON policy_violations(created_at DESC);

-- Audit trails table indexes (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_trails') THEN
        CREATE INDEX IF NOT EXISTS idx_audit_trails_entity_composite ON audit_trails(tenant_id, entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_trails_action_at ON audit_trails(action_at DESC);
    END IF;
END $$;

-- Privacy logs table indexes (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'privacy_logs') THEN
        CREATE INDEX IF NOT EXISTS idx_privacy_logs_accessed_by_date ON privacy_logs(accessed_by, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_privacy_logs_entity_composite ON privacy_logs(tenant_id, entity_type, entity_id);
    END IF;
END $$;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_expenses_tenant_date_status ON expenses(tenant_id, expense_date DESC, status);
CREATE INDEX IF NOT EXISTS idx_expenses_submitted_date ON expenses(submitted_by, expense_date DESC);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_expenses_active ON expenses(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_receipts_active ON receipts(tenant_id, ocr_status) WHERE deleted_at IS NULL;

-- ============================================================================
-- SECURITY ENHANCEMENTS (Phase 30)
-- ============================================================================

-- Add security audit log table
CREATE TABLE IF NOT EXISTS security_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Event details
    event_type VARCHAR(100) NOT NULL, -- login, logout, permission_denied, data_access, data_modification, etc.
    event_category VARCHAR(50) NOT NULL, -- authentication, authorization, data_access, configuration, etc.
    severity VARCHAR(20) NOT NULL DEFAULT 'info', -- info, warning, error, critical
    
    -- Request details
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_path VARCHAR(500),
    request_method VARCHAR(10),
    
    -- Event details
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Result
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_security_audit_logs_tenant_id ON security_audit_logs(tenant_id);
CREATE INDEX idx_security_audit_logs_user_id ON security_audit_logs(user_id);
CREATE INDEX idx_security_audit_logs_event_type ON security_audit_logs(event_type);
CREATE INDEX idx_security_audit_logs_severity ON security_audit_logs(severity) WHERE severity IN ('error', 'critical');
CREATE INDEX idx_security_audit_logs_created_at ON security_audit_logs(created_at DESC);
CREATE INDEX idx_security_audit_logs_composite ON security_audit_logs(tenant_id, event_type, created_at DESC);

-- Add session tracking table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Session details
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    
    -- Device and location
    ip_address VARCHAR(45),
    user_agent TEXT,
    device_type VARCHAR(50),
    device_id VARCHAR(255),
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_activity_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Security
    login_method VARCHAR(50) DEFAULT 'password', -- password, sso, mfa
    mfa_verified BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_user_sessions_tenant_user ON user_sessions(tenant_id, user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token) WHERE is_active = true;
CREATE INDEX idx_user_sessions_active ON user_sessions(user_id, is_active) WHERE is_active = true;
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at) WHERE is_active = true;

-- Add failed login attempts tracking
CREATE TABLE IF NOT EXISTS failed_login_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    last_attempt_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_failed_login_attempts_email ON failed_login_attempts(email, last_attempt_at DESC);
CREATE INDEX idx_failed_login_attempts_ip ON failed_login_attempts(ip_address, last_attempt_at DESC);
CREATE INDEX idx_failed_login_attempts_locked ON failed_login_attempts(locked_until) WHERE locked_until > CURRENT_TIMESTAMP;

-- Add role permissions audit table
CREATE TABLE IF NOT EXISTS role_permissions_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    
    -- Change details
    action VARCHAR(50) NOT NULL, -- granted, revoked, modified
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_role_permissions_audit_role ON role_permissions_audit(role_id, changed_at DESC);
CREATE INDEX idx_role_permissions_audit_tenant ON role_permissions_audit(tenant_id, changed_at DESC);

-- ============================================================================
-- ANALYZE TABLES FOR QUERY OPTIMIZATION
-- ============================================================================

ANALYZE expenses;
ANALYZE receipts;
ANALYZE users;
ANALYZE policy_violations;
ANALYZE audit_trails;
ANALYZE privacy_logs;




