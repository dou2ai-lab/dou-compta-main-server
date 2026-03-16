-- Migration 019: Banking & Reconciliation
-- DouCompta V4.0 - Phase 3 (BANKA Agent)

-- =============================================================================
-- Bank Accounts
-- =============================================================================

CREATE TABLE IF NOT EXISTS bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    account_name VARCHAR(255) NOT NULL,
    iban VARCHAR(34),
    bic VARCHAR(11),
    bank_name VARCHAR(255),
    currency VARCHAR(3) DEFAULT 'EUR',
    balance DECIMAL(15,2) DEFAULT 0,
    balance_date DATE,
    pcg_account_code VARCHAR(10) DEFAULT '512000',
    connection_type VARCHAR(20) DEFAULT 'manual' CHECK (connection_type IN ('api', 'manual', 'import')),
    is_active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMPTZ,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Bank Statements
-- =============================================================================

CREATE TABLE IF NOT EXISTS bank_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    statement_date DATE NOT NULL,
    period_start DATE,
    period_end DATE,
    opening_balance DECIMAL(15,2),
    closing_balance DECIMAL(15,2),
    transaction_count INTEGER DEFAULT 0,
    file_path VARCHAR(500),
    file_format VARCHAR(20), -- pdf, camt053, csv, ofx
    import_status VARCHAR(20) DEFAULT 'pending' CHECK (import_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    imported_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Bank Transactions
-- =============================================================================

CREATE TABLE IF NOT EXISTS bank_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_account_id UUID NOT NULL REFERENCES bank_accounts(id) ON DELETE CASCADE,
    statement_id UUID REFERENCES bank_statements(id),
    transaction_date DATE NOT NULL,
    value_date DATE,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    label TEXT NOT NULL,
    reference VARCHAR(100),
    counterparty_name VARCHAR(255),
    counterparty_iban VARCHAR(34),
    transaction_type VARCHAR(50), -- debit, credit, transfer, fee, interest
    category VARCHAR(100),
    reconciliation_status VARCHAR(20) DEFAULT 'unmatched' CHECK (reconciliation_status IN ('unmatched', 'matched', 'partially_matched', 'ignored')),
    matched_entry_id UUID REFERENCES journal_entries(id),
    match_confidence DECIMAL(5,4),
    matched_at TIMESTAMPTZ,
    matched_by VARCHAR(20), -- auto, manual
    raw_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Reconciliation Rules
-- =============================================================================

CREATE TABLE IF NOT EXISTS reconciliation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    match_criteria JSONB NOT NULL DEFAULT '{}',
    target_account_code VARCHAR(10),
    target_journal_code VARCHAR(5) DEFAULT 'BNQ',
    auto_apply BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Indexes
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_bank_accounts_tenant ON bank_accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bank_statements_account ON bank_statements(bank_account_id);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_account ON bank_transactions(bank_account_id);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_date ON bank_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_status ON bank_transactions(reconciliation_status);
CREATE INDEX IF NOT EXISTS idx_bank_transactions_matched ON bank_transactions(matched_entry_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_rules_tenant ON reconciliation_rules(tenant_id);
