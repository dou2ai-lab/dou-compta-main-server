-- ============================================================================
-- FIX: Create policy_violations table
-- ============================================================================

CREATE TABLE IF NOT EXISTS policy_violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_id UUID NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    policy_id UUID NOT NULL REFERENCES expense_policies(id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL,
    violation_severity VARCHAR(20) NOT NULL DEFAULT 'warning',
    violation_message TEXT NOT NULL,
    policy_rule JSONB DEFAULT '{}'::jsonb,
    requires_comment BOOLEAN NOT NULL DEFAULT false,
    comment_provided TEXT,
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_policy_violations_expense_id ON policy_violations(expense_id);
CREATE INDEX IF NOT EXISTS idx_policy_violations_policy_id ON policy_violations(policy_id);
CREATE INDEX IF NOT EXISTS idx_policy_violations_is_resolved ON policy_violations(is_resolved);
CREATE INDEX IF NOT EXISTS idx_policy_violations_violation_type ON policy_violations(violation_type);


























