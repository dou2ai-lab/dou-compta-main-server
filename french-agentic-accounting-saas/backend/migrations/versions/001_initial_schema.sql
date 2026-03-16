-- Phase 1 Baseline Schema
-- Dou Expense & Audit AI – France Edition
-- PostgreSQL 14+ with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- pgvector extension is usually installed as "vector". Some environments may use "pgvector".
-- For local/dev convenience, we try to enable it but don't hard-fail if it's unavailable.
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION WHEN undefined_file THEN
    BEGIN
        CREATE EXTENSION IF NOT EXISTS "pgvector";
    EXCEPTION WHEN undefined_file THEN
        RAISE NOTICE 'pgvector extension not installed; skipping. RAG/embeddings features will be unavailable until installed.';
    END;
END $$;

-- ============================================================================
-- TENANT MANAGEMENT
-- ============================================================================

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    domain VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, suspended, inactive
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenants_deleted_at ON tenants(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- USER MANAGEMENT
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    password_hash VARCHAR(255), -- For non-SSO users (placeholder)
    sso_provider VARCHAR(50), -- saml, oidc, etc.
    sso_subject_id VARCHAR(255), -- SSO provider's user ID
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, inactive, suspended
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT unique_tenant_email UNIQUE (tenant_id, email),
    CONSTRAINT unique_sso_subject UNIQUE (tenant_id, sso_provider, sso_subject_id)
);

CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- ROLE-BASED ACCESS CONTROL (RBAC)
-- ============================================================================

CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system_role BOOLEAN NOT NULL DEFAULT false, -- System roles cannot be deleted
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_tenant_role_name UNIQUE (tenant_id, name)
);

CREATE INDEX idx_roles_tenant_id ON roles(tenant_id);
CREATE INDEX idx_roles_deleted_at ON roles(deleted_at) WHERE deleted_at IS NULL;

CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE, -- e.g., 'expense:create', 'expense:approve'
    description TEXT,
    resource VARCHAR(100) NOT NULL, -- expense, admin, audit, etc.
    action VARCHAR(50) NOT NULL, -- create, read, update, delete, approve, etc.
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_action ON permissions(action);

CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- ============================================================================
-- EXPENSE MANAGEMENT (Minimal Placeholder)
-- ============================================================================

CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    submitted_by UUID NOT NULL REFERENCES users(id),
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    expense_date DATE NOT NULL,
    category VARCHAR(100), -- Placeholder, will be AI-categorized later
    description TEXT,
    merchant_name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, submitted, approved, rejected, paid
    approval_status VARCHAR(50), -- pending, approved, rejected
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    vat_amount DECIMAL(12, 2), -- Calculated VAT
    vat_rate DECIMAL(5, 2), -- VAT rate percentage
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_expenses_tenant_id ON expenses(tenant_id);
CREATE INDEX idx_expenses_submitted_by ON expenses(submitted_by);
CREATE INDEX idx_expenses_status ON expenses(status);
CREATE INDEX idx_expenses_expense_date ON expenses(expense_date);
CREATE INDEX idx_expenses_deleted_at ON expenses(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_expenses_created_at ON expenses(created_at DESC);

-- ============================================================================
-- RECEIPT DOCUMENTS
-- ============================================================================

CREATE TABLE receipt_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_id UUID NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL, -- Size in bytes
    mime_type VARCHAR(100),
    storage_path VARCHAR(500) NOT NULL, -- Path in object storage
    storage_provider VARCHAR(50) NOT NULL DEFAULT 's3', -- s3, gcs, azure
    ocr_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    ocr_extracted_data JSONB, -- OCR results (placeholder)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_receipt_documents_expense_id ON receipt_documents(expense_id);
CREATE INDEX idx_receipt_documents_tenant_id ON receipt_documents(tenant_id);
CREATE INDEX idx_receipt_documents_ocr_status ON receipt_documents(ocr_status);
CREATE INDEX idx_receipt_documents_deleted_at ON receipt_documents(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- APPROVAL WORKFLOW
-- ============================================================================

CREATE TABLE expense_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_id UUID NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    approver_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(50) NOT NULL, -- pending, approved, rejected
    comments TEXT,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_expense_approvals_expense_id ON expense_approvals(expense_id);
CREATE INDEX idx_expense_approvals_approver_id ON expense_approvals(approver_id);
CREATE INDEX idx_expense_approvals_status ON expense_approvals(status);

-- ============================================================================
-- AUDIT LOGGING
-- ============================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- create, update, delete, approve, etc.
    resource_type VARCHAR(100) NOT NULL, -- expense, user, policy, etc.
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100), -- For request correlation
    changes JSONB, -- Before/after changes
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_tenant_id ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id);

-- ============================================================================
-- ADMIN: POLICIES (Placeholder Structure)
-- ============================================================================

CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    policy_type VARCHAR(100) NOT NULL, -- expense_limit, category_restriction, approval_required, etc.
    rules JSONB NOT NULL, -- Policy rules as JSON (placeholder for future policy engine)
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_policies_tenant_id ON policies(tenant_id);
CREATE INDEX idx_policies_policy_type ON policies(policy_type);
CREATE INDEX idx_policies_is_active ON policies(is_active);
CREATE INDEX idx_policies_deleted_at ON policies(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- ADMIN: VAT RULES (Placeholder Structure)
-- ============================================================================

CREATE TABLE vat_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    category VARCHAR(100),
    merchant_pattern VARCHAR(255), -- Pattern matching for merchant names
    vat_rate DECIMAL(5, 2) NOT NULL,
    vat_code VARCHAR(50), -- French VAT code
    is_default BOOLEAN NOT NULL DEFAULT false,
    effective_from DATE,
    effective_to DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_vat_rules_tenant_id ON vat_rules(tenant_id);
CREATE INDEX idx_vat_rules_category ON vat_rules(category);
CREATE INDEX idx_vat_rules_is_default ON vat_rules(is_default);
CREATE INDEX idx_vat_rules_deleted_at ON vat_rules(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- ADMIN: TENANT CONFIGURATIONS
-- ============================================================================

CREATE TABLE tenant_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    config_key VARCHAR(100) NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_tenant_config_key UNIQUE (tenant_id, config_key)
);

CREATE INDEX idx_tenant_configurations_tenant_id ON tenant_configurations(tenant_id);
CREATE INDEX idx_tenant_configurations_config_key ON tenant_configurations(config_key);

-- ============================================================================
-- RISK DETECTION (Placeholder)
-- ============================================================================

CREATE TABLE risk_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    risk_type VARCHAR(100) NOT NULL, -- duplicate_expense, policy_violation, anomaly, etc.
    severity VARCHAR(50) NOT NULL, -- low, medium, high, critical
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    description TEXT,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    status VARCHAR(50) NOT NULL DEFAULT 'open', -- open, investigating, resolved, false_positive
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_risk_items_tenant_id ON risk_items(tenant_id);
CREATE INDEX idx_risk_items_risk_type ON risk_items(risk_type);
CREATE INDEX idx_risk_items_severity ON risk_items(severity);
CREATE INDEX idx_risk_items_status ON risk_items(status);
CREATE INDEX idx_risk_items_resource ON risk_items(resource_type, resource_id);
CREATE INDEX idx_risk_items_detected_at ON risk_items(detected_at DESC);

-- ============================================================================
-- COMPLIANCE CHECKS (Placeholder)
-- ============================================================================

CREATE TABLE compliance_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    check_type VARCHAR(100) NOT NULL, -- vat_compliance, urssaf_compliance, gdpr_compliance, etc.
    status VARCHAR(50) NOT NULL, -- pass, fail, warning
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details JSONB,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_compliance_checks_tenant_id ON compliance_checks(tenant_id);
CREATE INDEX idx_compliance_checks_check_type ON compliance_checks(check_type);
CREATE INDEX idx_compliance_checks_status ON compliance_checks(status);
CREATE INDEX idx_compliance_checks_checked_at ON compliance_checks(checked_at DESC);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_expenses_updated_at BEFORE UPDATE ON expenses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_receipt_documents_updated_at BEFORE UPDATE ON receipt_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_expense_approvals_updated_at BEFORE UPDATE ON expense_approvals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vat_rules_updated_at BEFORE UPDATE ON vat_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tenant_configurations_updated_at BEFORE UPDATE ON tenant_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA (Development Only)
-- ============================================================================

-- Insert default permissions
INSERT INTO permissions (name, description, resource, action) VALUES
    ('expense:create', 'Create expenses', 'expense', 'create'),
    ('expense:read', 'Read expenses', 'expense', 'read'),
    ('expense:update', 'Update expenses', 'expense', 'update'),
    ('expense:delete', 'Delete expenses', 'expense', 'delete'),
    ('expense:approve', 'Approve expenses', 'expense', 'approve'),
    ('admin:read', 'Read admin settings', 'admin', 'read'),
    ('admin:write', 'Write admin settings', 'admin', 'write'),
    ('audit:read', 'Read audit logs', 'audit', 'read'),
    ('audit:write', 'Write audit logs', 'audit', 'write'),
    ('user:read', 'Read users', 'user', 'read'),
    ('user:write', 'Write users', 'user', 'write')
ON CONFLICT (name) DO NOTHING;














