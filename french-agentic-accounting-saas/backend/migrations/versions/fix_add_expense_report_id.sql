-- ============================================================================
-- FIX: Add expense_report_id and related columns to expenses table
-- ============================================================================
-- This migration adds the missing columns to the expenses table
-- Run this SQL directly in your PostgreSQL database

-- Add expense_report_id to expenses table if it doesn't exist
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


























