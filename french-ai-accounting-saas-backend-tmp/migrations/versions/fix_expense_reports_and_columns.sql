-- ============================================================================
-- FIX: Create expense_reports table and add missing columns to expenses
-- ============================================================================

-- First, create the expense_reports table if it doesn't exist
CREATE TABLE IF NOT EXISTS expense_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    submitted_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    report_number VARCHAR(50) NOT NULL,
    report_type VARCHAR(50) NOT NULL DEFAULT 'period',
    title VARCHAR(255),
    description TEXT,
    
    -- Period-based grouping
    period_start_date DATE,
    period_end_date DATE,
    period_type VARCHAR(20),
    
    -- Trip-based grouping
    trip_name VARCHAR(255),
    trip_start_date DATE,
    trip_end_date DATE,
    trip_destination VARCHAR(255),
    
    total_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    expense_count INTEGER NOT NULL DEFAULT 0,
    
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    approval_status VARCHAR(50),
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

-- Create indexes for expense_reports
CREATE INDEX IF NOT EXISTS idx_expense_reports_tenant_id ON expense_reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_expense_reports_submitted_by ON expense_reports(submitted_by);
CREATE INDEX IF NOT EXISTS idx_expense_reports_report_number ON expense_reports(report_number);
CREATE INDEX IF NOT EXISTS idx_expense_reports_status ON expense_reports(status);
CREATE INDEX IF NOT EXISTS idx_expense_reports_deleted_at ON expense_reports(deleted_at) WHERE deleted_at IS NULL;

-- Now add expense_report_id to expenses table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'expenses' AND column_name = 'expense_report_id'
    ) THEN
        ALTER TABLE expenses ADD COLUMN expense_report_id UUID REFERENCES expense_reports(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_expenses_expense_report_id ON expenses(expense_report_id);
        RAISE NOTICE 'Column expense_report_id added successfully';
    ELSE
        RAISE NOTICE 'Column expense_report_id already exists';
    END IF;
END $$;

-- Add policy_violation_count to expenses table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'expenses' AND column_name = 'policy_violation_count'
    ) THEN
        ALTER TABLE expenses ADD COLUMN policy_violation_count INTEGER NOT NULL DEFAULT 0;
        RAISE NOTICE 'Column policy_violation_count added successfully';
    ELSE
        RAISE NOTICE 'Column policy_violation_count already exists';
    END IF;
END $$;

-- Add has_policy_violations flag if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'expenses' AND column_name = 'has_policy_violations'
    ) THEN
        ALTER TABLE expenses ADD COLUMN has_policy_violations BOOLEAN NOT NULL DEFAULT false;
        RAISE NOTICE 'Column has_policy_violations added successfully';
    ELSE
        RAISE NOTICE 'Column has_policy_violations already exists';
    END IF;
END $$;


























