-- Migration 017: Accounting Entries (Phase 1 - DouCompta Accounting Engine)

-- PCG 2025 Chart of Accounts
CREATE TABLE IF NOT EXISTS pcg_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    account_code VARCHAR(10) NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_class INTEGER NOT NULL, -- 1-8
    account_type VARCHAR(50) NOT NULL, -- asset, liability, equity, revenue, expense
    parent_code VARCHAR(10),
    is_system BOOLEAN DEFAULT TRUE, -- seeded PCG accounts
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, account_code)
);

-- Third Parties (suppliers, customers, employees)
CREATE TABLE IF NOT EXISTS third_parties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('supplier', 'customer', 'employee')),
    name VARCHAR(255) NOT NULL,
    siren VARCHAR(9),
    siret VARCHAR(14),
    vat_number VARCHAR(20),
    default_account_code VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fiscal Periods
CREATE TABLE IF NOT EXISTS fiscal_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    fiscal_year INTEGER NOT NULL,
    period_number INTEGER NOT NULL, -- 1-12 or 0 for opening, 13 for closing
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'locked')),
    closed_at TIMESTAMPTZ,
    closed_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, fiscal_year, period_number)
);

-- Journal Entries
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    entry_number VARCHAR(50) NOT NULL,
    journal_code VARCHAR(5) NOT NULL CHECK (journal_code IN ('ACH', 'VTE', 'BNQ', 'OD', 'SAL', 'AN')),
    entry_date DATE NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'validated', 'posted')),
    source_type VARCHAR(50), -- expense, invoice, bank, manual
    source_id UUID,
    fiscal_year INTEGER NOT NULL,
    fiscal_period INTEGER NOT NULL,
    total_debit DECIMAL(15,2) DEFAULT 0,
    total_credit DECIMAL(15,2) DEFAULT 0,
    is_balanced BOOLEAN DEFAULT FALSE,
    validated_by UUID REFERENCES users(id),
    validated_at TIMESTAMPTZ,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, entry_number)
);

-- Journal Entry Lines
CREATE TABLE IF NOT EXISTS journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    account_code VARCHAR(10) NOT NULL,
    account_name VARCHAR(255),
    debit DECIMAL(15,2) DEFAULT 0,
    credit DECIMAL(15,2) DEFAULT 0,
    label TEXT,
    vat_rate DECIMAL(5,2),
    vat_amount DECIMAL(15,2),
    third_party_id UUID REFERENCES third_parties(id),
    lettering_code VARCHAR(10),
    lettered_at TIMESTAMPTZ,
    currency VARCHAR(3) DEFAULT 'EUR',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_journal_entries_tenant ON journal_entries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_entries_journal ON journal_entries(journal_code);
CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_entry ON journal_entry_lines(entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_account ON journal_entry_lines(account_code);
CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_lettering ON journal_entry_lines(lettering_code);
CREATE INDEX IF NOT EXISTS idx_pcg_accounts_tenant ON pcg_accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_third_parties_tenant ON third_parties(tenant_id);
CREATE INDEX IF NOT EXISTS idx_fiscal_periods_tenant ON fiscal_periods(tenant_id, fiscal_year);
