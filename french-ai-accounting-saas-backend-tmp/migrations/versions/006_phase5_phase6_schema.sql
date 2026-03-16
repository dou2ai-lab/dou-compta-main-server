-- -----------------------------------------------------------------------------
-- File: 006_phase5_phase6_schema.sql
-- Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
-- Created On: 01-12-2025
-- Description: Phase 5 (Policy Engine) and Phase 6 (Expense Reports & Approval Workflow) database schema
-- -----------------------------------------------------------------------------

-- Phase 5: Policy Engine v1
-- Phase 6: Expense Reports and Approval Workflow

-- ============================================================================
-- POLICY VIOLATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS policy_violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_id UUID NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    policy_id UUID NOT NULL REFERENCES expense_policies(id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL, -- amount_exceeded, category_restricted, missing_required_field, etc.
    violation_severity VARCHAR(20) NOT NULL DEFAULT 'warning', -- warning, error, info
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

-- ============================================================================
-- EXPENSE REPORTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS expense_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_number VARCHAR(50) NOT NULL, -- Auto-generated report number
    report_type VARCHAR(50) NOT NULL DEFAULT 'period', -- period, trip
    title VARCHAR(255),
    description TEXT,
    
    -- Period-based grouping
    period_start_date DATE,
    period_end_date DATE,
    period_type VARCHAR(20), -- monthly, weekly, custom
    
    -- Trip-based grouping
    trip_name VARCHAR(255),
    trip_start_date DATE,
    trip_end_date DATE,
    trip_destination VARCHAR(255),
    
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    expense_count INTEGER NOT NULL DEFAULT 0,
    
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, submitted, pending_approval, approved, rejected, paid
    approval_status VARCHAR(50), -- pending, approved, rejected
    submitted_at TIMESTAMP WITH TIME ZONE,
    
    -- Approval workflow
    approver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    approval_notes TEXT,
    
    meta_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_report_number_tenant UNIQUE (tenant_id, report_number)
);

CREATE INDEX IF NOT EXISTS idx_expense_reports_tenant_id ON expense_reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_expense_reports_submitted_by ON expense_reports(submitted_by);
CREATE INDEX IF NOT EXISTS idx_expense_reports_report_number ON expense_reports(report_number);
CREATE INDEX IF NOT EXISTS idx_expense_reports_status ON expense_reports(status);
CREATE INDEX IF NOT EXISTS idx_expense_reports_approval_status ON expense_reports(approval_status);
CREATE INDEX IF NOT EXISTS idx_expense_reports_approver_id ON expense_reports(approver_id);
CREATE INDEX IF NOT EXISTS idx_expense_reports_period_start ON expense_reports(period_start_date);
CREATE INDEX IF NOT EXISTS idx_expense_reports_period_end ON expense_reports(period_end_date);
CREATE INDEX IF NOT EXISTS idx_expense_reports_deleted_at ON expense_reports(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- EXPENSE REPORT ITEMS (Junction table for expenses in reports)
-- ============================================================================

CREATE TABLE IF NOT EXISTS expense_report_items (
    expense_report_id UUID NOT NULL REFERENCES expense_reports(id) ON DELETE CASCADE,
    expense_id UUID NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    added_by UUID REFERENCES users(id) ON DELETE SET NULL,
    PRIMARY KEY (expense_report_id, expense_id)
);

CREATE INDEX IF NOT EXISTS idx_expense_report_items_expense_id ON expense_report_items(expense_id);
CREATE INDEX IF NOT EXISTS idx_expense_report_items_report_id ON expense_report_items(expense_report_id);

-- ============================================================================
-- APPROVAL WORKFLOW
-- ============================================================================

CREATE TABLE IF NOT EXISTS approval_workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL, -- expense, expense_report
    entity_id UUID NOT NULL,
    workflow_type VARCHAR(50) NOT NULL DEFAULT 'single_step', -- single_step, multi_step
    current_step INTEGER NOT NULL DEFAULT 1,
    total_steps INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, approved, rejected, cancelled
    initiated_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    initiated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    meta_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_workflows_tenant_id ON approval_workflows(tenant_id);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_entity ON approval_workflows(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_status ON approval_workflows(status);
CREATE INDEX IF NOT EXISTS idx_approval_workflows_initiated_by ON approval_workflows(initiated_by);

CREATE TABLE IF NOT EXISTS approval_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES approval_workflows(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    approver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, approved, rejected, skipped
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,
    rejection_reason TEXT,
    notified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_workflow_step UNIQUE (workflow_id, step_number)
);

CREATE INDEX IF NOT EXISTS idx_approval_steps_workflow_id ON approval_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_approval_steps_approver_id ON approval_steps(approver_id);
CREATE INDEX IF NOT EXISTS idx_approval_steps_status ON approval_steps(status);

-- ============================================================================
-- EMAIL NOTIFICATIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS email_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- approval_request, approval_approved, approval_rejected, expense_submitted, etc.
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    entity_type VARCHAR(50), -- expense, expense_report, approval_workflow
    entity_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, sent, failed, delivered
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    meta_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_notifications_tenant_id ON email_notifications(tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_notifications_recipient_id ON email_notifications(recipient_id);
CREATE INDEX IF NOT EXISTS idx_email_notifications_status ON email_notifications(status);
CREATE INDEX IF NOT EXISTS idx_email_notifications_notification_type ON email_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_email_notifications_entity ON email_notifications(entity_type, entity_id);

-- ============================================================================
-- UPDATE EXPENSES TABLE
-- ============================================================================

-- Add expense_report_id to expenses table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'expenses' AND column_name = 'expense_report_id'
    ) THEN
        ALTER TABLE expenses ADD COLUMN expense_report_id UUID REFERENCES expense_reports(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_expenses_expense_report_id ON expenses(expense_report_id);
    END IF;
END $$;

-- Add policy_violation_count to expenses table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'expenses' AND column_name = 'policy_violation_count'
    ) THEN
        ALTER TABLE expenses ADD COLUMN policy_violation_count INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- Add has_policy_violations flag
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'expenses' AND column_name = 'has_policy_violations'
    ) THEN
        ALTER TABLE expenses ADD COLUMN has_policy_violations BOOLEAN NOT NULL DEFAULT false;
    END IF;
END $$;

-- ============================================================================
-- UPDATE USERS TABLE FOR MANAGER RELATIONSHIP
-- ============================================================================

-- Add manager_id to users table for approval hierarchy
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'manager_id'
    ) THEN
        ALTER TABLE users ADD COLUMN manager_id UUID REFERENCES users(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id);
    END IF;
END $$;



























