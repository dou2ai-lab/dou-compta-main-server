-- ============================================================================
-- FIX: Add manager_id column to users table
-- ============================================================================
-- This migration adds the missing manager_id column to the users table
-- Run this SQL directly in your PostgreSQL database

-- Add manager_id to users table for approval hierarchy
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'manager_id'
    ) THEN
        ALTER TABLE users ADD COLUMN manager_id UUID REFERENCES users(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_users_manager_id ON users(manager_id);
        RAISE NOTICE 'Column manager_id added successfully';
    ELSE
        RAISE NOTICE 'Column manager_id already exists';
    END IF;
END $$;


























