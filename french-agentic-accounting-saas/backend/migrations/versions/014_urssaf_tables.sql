-- Migration: URSSAF Compliance Tables
-- Dou Expense & Audit AI – France Edition
-- URSSAF compliance service tables

-- ============================================================================
-- URSSAF RULES
-- ============================================================================

CREATE TABLE IF NOT EXISTS urssaf_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Rule definition
    rule_name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- exemption, contribution, exemption_threshold, classification
    description TEXT,
    
    -- Rule conditions
    expense_category VARCHAR(100),
    expense_type VARCHAR(100), -- benefit, reimbursement, etc.
    amount_threshold DECIMAL(12, 2), -- Threshold for exemptions
    employee_type VARCHAR(50), -- employee, contractor, intern
    
    -- Rule values
    contribution_rate DECIMAL(5, 2), -- Percentage rate
    exemption_applicable BOOLEAN NOT NULL DEFAULT false,
    is_mandatory BOOLEAN NOT NULL DEFAULT true,
    
    -- Effective dates
    effective_from DATE,
    effective_to DATE,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,
    meta_data JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_urssaf_rules_tenant_id ON urssaf_rules(tenant_id);
CREATE INDEX idx_urssaf_rules_rule_type ON urssaf_rules(rule_type);
CREATE INDEX idx_urssaf_rules_is_active ON urssaf_rules(is_active) WHERE is_active = true AND deleted_at IS NULL;
CREATE INDEX idx_urssaf_rules_effective_dates ON urssaf_rules(effective_from, effective_to);

-- ============================================================================
-- URSSAF COMPLIANCE CHECKS
-- ============================================================================

CREATE TABLE IF NOT EXISTS urssaf_compliance_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    expense_id UUID NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    
    -- Check result
    is_compliant BOOLEAN NOT NULL,
    compliance_status VARCHAR(50) NOT NULL, -- compliant, non_compliant, requires_review
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low', -- low, medium, high
    
    -- Classification
    expense_classification VARCHAR(50), -- benefit, reimbursement, exempt
    employee_classification VARCHAR(50), -- employee, contractor, intern
    
    -- Contribution calculation
    contribution_applicable BOOLEAN NOT NULL DEFAULT false,
    contribution_rate DECIMAL(5, 2),
    contribution_amount DECIMAL(12, 2),
    
    -- Exemption check
    exemption_applicable BOOLEAN NOT NULL DEFAULT false,
    exemption_reason TEXT,
    exemption_threshold_met BOOLEAN NOT NULL DEFAULT false,
    
    -- Rule applied
    rule_id UUID REFERENCES urssaf_rules(id),
    rule_name VARCHAR(255),
    
    -- Explanation
    explanation TEXT,
    recommendations JSONB DEFAULT '[]'::jsonb,
    
    -- Metadata
    checked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checked_by UUID REFERENCES users(id),
    meta_data JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_urssaf_compliance_tenant_id ON urssaf_compliance_checks(tenant_id);
CREATE INDEX idx_urssaf_compliance_expense_id ON urssaf_compliance_checks(expense_id);
CREATE INDEX idx_urssaf_compliance_status ON urssaf_compliance_checks(compliance_status);
CREATE INDEX idx_urssaf_compliance_risk_level ON urssaf_compliance_checks(risk_level);
CREATE INDEX idx_urssaf_compliance_checked_at ON urssaf_compliance_checks(checked_at DESC);
CREATE INDEX idx_urssaf_compliance_compliant ON urssaf_compliance_checks(is_compliant) WHERE is_compliant = false;

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

CREATE TRIGGER update_urssaf_rules_updated_at BEFORE UPDATE ON urssaf_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_urssaf_compliance_checks_updated_at BEFORE UPDATE ON urssaf_compliance_checks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

