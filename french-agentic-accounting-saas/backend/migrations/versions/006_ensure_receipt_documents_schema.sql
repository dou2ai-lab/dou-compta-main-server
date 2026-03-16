-- Migration: Ensure receipt_documents table has correct schema for file upload
-- This migration ensures all required columns exist and have correct constraints

-- First, ensure the table exists (create if it doesn't)
CREATE TABLE IF NOT EXISTS receipt_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    expense_id UUID REFERENCES expenses(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    storage_path VARCHAR(500) NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 's3',
    ocr_status VARCHAR(50) DEFAULT 'pending',
    ocr_extracted_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Add missing columns if they don't exist
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS file_id UUID;

ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS encryption_key_id VARCHAR(255);

ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS upload_status VARCHAR(50) DEFAULT 'pending';

ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS ocr_job_id UUID;

ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS ocr_completed_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS meta_data JSONB DEFAULT '{}'::jsonb;

-- Fix expense_id constraint: make it nullable if it's currently NOT NULL
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'receipt_documents' 
        AND column_name = 'expense_id' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE receipt_documents ALTER COLUMN expense_id DROP NOT NULL;
    END IF;
END $$;

-- Update existing rows to have file_id (use id as file_id for existing records)
UPDATE receipt_documents 
SET file_id = id 
WHERE file_id IS NULL;

-- Now make file_id NOT NULL after populating it (only if column exists and has data)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'receipt_documents' 
        AND column_name = 'file_id'
    ) THEN
        -- Check if all rows have file_id
        IF NOT EXISTS (SELECT 1 FROM receipt_documents WHERE file_id IS NULL) THEN
            ALTER TABLE receipt_documents ALTER COLUMN file_id SET NOT NULL;
        END IF;
    END IF;
END $$;

-- Update existing rows to have upload_status
UPDATE receipt_documents 
SET upload_status = 'completed' 
WHERE upload_status IS NULL;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_receipt_documents_expense_id ON receipt_documents(expense_id);
CREATE INDEX IF NOT EXISTS idx_receipt_documents_tenant_id ON receipt_documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_receipt_documents_ocr_status ON receipt_documents(ocr_status);
CREATE INDEX IF NOT EXISTS idx_receipt_documents_deleted_at ON receipt_documents(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_receipt_documents_file_id ON receipt_documents(file_id);
CREATE INDEX IF NOT EXISTS idx_receipt_documents_upload_status ON receipt_documents(upload_status);
