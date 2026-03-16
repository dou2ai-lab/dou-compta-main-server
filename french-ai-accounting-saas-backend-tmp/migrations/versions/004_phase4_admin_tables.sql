-- Phase 4 Schema Additions
-- Dou Expense & Audit AI – France Edition
-- Admin Module: Categories, GL Accounts, Policies
-- Created On: 30-11-2025

-- ============================================================================
-- EXPENSE CATEGORIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS expense_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    description TEXT,
    gl_account_id UUID,
    is_active BOOLEAN NOT NULL DEFAULT true,
    parent_id UUID REFERENCES expense_categories(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_tenant_category_code UNIQUE (tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_expense_categories_tenant_id ON expense_categories(tenant_id);
CREATE INDEX IF NOT EXISTS idx_expense_categories_code ON expense_categories(code);
CREATE INDEX IF NOT EXISTS idx_expense_categories_parent_id ON expense_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_expense_categories_is_active ON expense_categories(is_active);
CREATE INDEX IF NOT EXISTS idx_expense_categories_deleted_at ON expense_categories(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- GENERAL LEDGER ACCOUNTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS gl_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    parent_account_id UUID REFERENCES gl_accounts(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_tenant_account_code UNIQUE (tenant_id, account_code)
);

CREATE INDEX IF NOT EXISTS idx_gl_accounts_tenant_id ON gl_accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_gl_accounts_account_code ON gl_accounts(account_code);
CREATE INDEX IF NOT EXISTS idx_gl_accounts_account_type ON gl_accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_gl_accounts_parent_account_id ON gl_accounts(parent_account_id);
CREATE INDEX IF NOT EXISTS idx_gl_accounts_is_active ON gl_accounts(is_active);
CREATE INDEX IF NOT EXISTS idx_gl_accounts_deleted_at ON gl_accounts(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- EXPENSE POLICIES
-- ============================================================================

CREATE TABLE IF NOT EXISTS expense_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    policy_type VARCHAR(50) NOT NULL,
    policy_rules JSONB DEFAULT '{}'::jsonb,
    applies_to_roles JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    effective_from TIMESTAMP WITH TIME ZONE,
    effective_until TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_expense_policies_tenant_id ON expense_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_expense_policies_policy_type ON expense_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_expense_policies_is_active ON expense_policies(is_active);
CREATE INDEX IF NOT EXISTS idx_expense_policies_effective_from ON expense_policies(effective_from);
CREATE INDEX IF NOT EXISTS idx_expense_policies_effective_until ON expense_policies(effective_until);
CREATE INDEX IF NOT EXISTS idx_expense_policies_deleted_at ON expense_policies(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- UPDATE RECEIPT DOCUMENTS TABLE
-- ============================================================================

-- Add meta_data column if it doesn't exist (for storing extraction results)
-- Note: receipt_documents table should exist from Phase 2 migration
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'receipt_documents') THEN
        ALTER TABLE receipt_documents
        ADD COLUMN IF NOT EXISTS meta_data JSONB DEFAULT '{}'::jsonb;
        
        IF NOT EXISTS (SELECT FROM pg_indexes WHERE indexname = 'idx_receipt_documents_meta_data') THEN
            CREATE INDEX idx_receipt_documents_meta_data ON receipt_documents USING GIN (meta_data);
        END IF;
    END IF;
END $$;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger for expense_categories
CREATE OR REPLACE FUNCTION update_expense_categories_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_expense_categories_updated_at ON expense_categories;
CREATE TRIGGER trigger_update_expense_categories_updated_at
    BEFORE UPDATE ON expense_categories
    FOR EACH ROW
    EXECUTE FUNCTION update_expense_categories_updated_at();

-- Update timestamp trigger for gl_accounts
CREATE OR REPLACE FUNCTION update_gl_accounts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_gl_accounts_updated_at ON gl_accounts;
CREATE TRIGGER trigger_update_gl_accounts_updated_at
    BEFORE UPDATE ON gl_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_gl_accounts_updated_at();

-- Update timestamp trigger for expense_policies
CREATE OR REPLACE FUNCTION update_expense_policies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_expense_policies_updated_at ON expense_policies;
CREATE TRIGGER trigger_update_expense_policies_updated_at
    BEFORE UPDATE ON expense_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_expense_policies_updated_at();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE expense_categories IS 'Expense categories for organizing expenses (e.g., Meals, Travel, Office Supplies)';
COMMENT ON TABLE gl_accounts IS 'General Ledger accounts for accounting integration';
COMMENT ON TABLE expense_policies IS 'Expense policies for enforcing business rules (amount limits, approval requirements, etc.)';

COMMENT ON COLUMN expense_categories.code IS 'Unique category code within tenant (e.g., MEALS, TRAVEL)';
COMMENT ON COLUMN expense_categories.gl_account_id IS 'Linked GL account for accounting integration';
COMMENT ON COLUMN gl_accounts.account_code IS 'GL account code (e.g., 6001, 6002)';
COMMENT ON COLUMN gl_accounts.account_type IS 'Account type: expense, asset, liability, equity, revenue';
COMMENT ON COLUMN expense_policies.policy_type IS 'Policy type: amount_limit, category_restriction, approval_required, etc.';
COMMENT ON COLUMN expense_policies.policy_rules IS 'Flexible JSONB storage for policy-specific rules';
COMMENT ON COLUMN expense_policies.applies_to_roles IS 'Array of role IDs this policy applies to';

