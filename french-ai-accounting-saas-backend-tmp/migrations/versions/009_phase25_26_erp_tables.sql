-- Migration: Phase 25 & 26 - ERP Integration and Reimbursement
-- Dou Expense & Audit AI – France Edition
-- ERP Integration, SEPA, and Card Payment Reconciliation

-- ============================================================================
-- ERP CONNECTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS erp_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Connection details
    provider VARCHAR(50) NOT NULL, -- sap, netsuite, odoo
    connection_type VARCHAR(20) NOT NULL, -- api, sftp
    is_active BOOLEAN NOT NULL DEFAULT true,
    
    -- Configuration (encrypted in production)
    configuration JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(50), -- success, failed, pending
    last_error TEXT,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_erp_connections_tenant_id ON erp_connections(tenant_id);
CREATE INDEX idx_erp_connections_provider ON erp_connections(provider);
CREATE INDEX idx_erp_connections_is_active ON erp_connections(is_active);
CREATE INDEX idx_erp_connections_deleted_at ON erp_connections(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- ACCOUNTING POSTINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS accounting_postings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    erp_connection_id UUID REFERENCES erp_connections(id),
    
    -- Expense reference
    expense_id UUID NOT NULL REFERENCES expenses(id),
    
    -- Posting details
    posting_date TIMESTAMP WITH TIME ZONE NOT NULL,
    posting_type VARCHAR(50) NOT NULL, -- expense, vat, reimbursement
    gl_account VARCHAR(100) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    
    -- VAT segmentation
    vat_rate DECIMAL(5, 2),
    vat_amount DECIMAL(12, 2),
    vat_account VARCHAR(100),
    vat_code VARCHAR(50), -- French VAT code
    
    -- ERP reference
    erp_document_id VARCHAR(255), -- Reference in ERP system
    erp_status VARCHAR(50), -- pending, posted, failed
    erp_error TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_accounting_postings_tenant_id ON accounting_postings(tenant_id);
CREATE INDEX idx_accounting_postings_expense_id ON accounting_postings(expense_id);
CREATE INDEX idx_accounting_postings_erp_connection_id ON accounting_postings(erp_connection_id);
CREATE INDEX idx_accounting_postings_posting_date ON accounting_postings(posting_date DESC);
CREATE INDEX idx_accounting_postings_erp_status ON accounting_postings(erp_status);

-- ============================================================================
-- SEPA TRANSACTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS sepa_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Transaction details
    transaction_id VARCHAR(100) UNIQUE NOT NULL, -- Unique SEPA transaction ID
    creditor_name VARCHAR(140) NOT NULL,
    creditor_iban VARCHAR(34) NOT NULL,
    creditor_bic VARCHAR(11),
    
    debtor_name VARCHAR(140) NOT NULL,
    debtor_iban VARCHAR(34) NOT NULL,
    debtor_bic VARCHAR(11),
    
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    execution_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Reference
    remittance_info VARCHAR(140), -- Payment reference
    expense_ids JSONB, -- Array of expense IDs
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, exported, executed, failed
    sepa_file_id UUID REFERENCES sepa_files(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sepa_transactions_tenant_id ON sepa_transactions(tenant_id);
CREATE INDEX idx_sepa_transactions_transaction_id ON sepa_transactions(transaction_id);
CREATE INDEX idx_sepa_transactions_sepa_file_id ON sepa_transactions(sepa_file_id);
CREATE INDEX idx_sepa_transactions_status ON sepa_transactions(status);
CREATE INDEX idx_sepa_transactions_execution_date ON sepa_transactions(execution_date);

-- ============================================================================
-- SEPA FILES
-- ============================================================================

CREATE TABLE IF NOT EXISTS sepa_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- File details
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    transaction_count INTEGER DEFAULT 0,
    total_amount DECIMAL(12, 2) DEFAULT 0,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, generated, exported, executed
    exported_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sepa_files_tenant_id ON sepa_files(tenant_id);
CREATE INDEX idx_sepa_files_status ON sepa_files(status);
CREATE INDEX idx_sepa_files_created_at ON sepa_files(created_at DESC);

-- ============================================================================
-- CARD PAYMENT RECONCILIATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS card_payment_reconciliations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Card payment details
    card_transaction_id VARCHAR(255) NOT NULL,
    card_last_four VARCHAR(4),
    merchant_name VARCHAR(255),
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    
    -- Reconciliation
    expense_id UUID REFERENCES expenses(id),
    receipt_id UUID REFERENCES receipts(id),
    
    -- Matching
    match_confidence DECIMAL(5, 2), -- 0-100
    match_method VARCHAR(50), -- automatic, manual, fuzzy
    match_score DECIMAL(5, 2),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, matched, unmatched, reviewed
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_card_payment_reconciliations_tenant_id ON card_payment_reconciliations(tenant_id);
CREATE INDEX idx_card_payment_reconciliations_card_transaction_id ON card_payment_reconciliations(card_transaction_id);
CREATE INDEX idx_card_payment_reconciliations_expense_id ON card_payment_reconciliations(expense_id);
CREATE INDEX idx_card_payment_reconciliations_status ON card_payment_reconciliations(status);
CREATE INDEX idx_card_payment_reconciliations_transaction_date ON card_payment_reconciliations(transaction_date DESC);




