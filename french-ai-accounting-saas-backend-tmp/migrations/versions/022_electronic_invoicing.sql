-- Migration 022: Electronic Invoicing
-- DouCompta V4.0 - Phase 6 (Factur-X / PPF)

CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dossier_id UUID REFERENCES client_dossiers(id),
    invoice_number VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('sent', 'received')),
    format VARCHAR(20) DEFAULT 'facturx' CHECK (format IN ('facturx', 'ubl', 'cii', 'pdf')),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'validated', 'sent', 'received', 'accepted', 'rejected', 'paid')),
    issuer_name VARCHAR(255),
    issuer_siren VARCHAR(9),
    issuer_vat_number VARCHAR(20),
    recipient_name VARCHAR(255),
    recipient_siren VARCHAR(9),
    recipient_vat_number VARCHAR(20),
    issue_date DATE NOT NULL,
    due_date DATE,
    total_ht DECIMAL(15,2) DEFAULT 0,
    total_vat DECIMAL(15,2) DEFAULT 0,
    total_ttc DECIMAL(15,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'EUR',
    xml_payload TEXT,
    pdf_path VARCHAR(500),
    ppf_transmission_id VARCHAR(100),
    ppf_status VARCHAR(50),
    journal_entry_id UUID REFERENCES journal_entries(id),
    notes TEXT,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(12,4) DEFAULT 1,
    unit_price DECIMAL(15,4) NOT NULL,
    vat_rate DECIMAL(5,2) DEFAULT 20,
    line_total_ht DECIMAL(15,2) NOT NULL,
    line_total_vat DECIMAL(15,2) DEFAULT 0,
    account_code VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX IF NOT EXISTS idx_invoices_type ON invoices(type, status);
CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_invoice_lines_invoice ON invoice_lines(invoice_id);
