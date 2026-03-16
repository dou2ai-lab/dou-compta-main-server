-- Migration: Fix receipt_documents table schema to match model
-- Add missing columns required by ReceiptDocument model

-- Add file_id column (required)
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS file_id UUID;

-- Make expense_id nullable (it's nullable in the model)
ALTER TABLE receipt_documents 
ALTER COLUMN expense_id DROP NOT NULL;

-- Add encryption_key_id column
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS encryption_key_id VARCHAR(255);

-- Add file_hash column
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

-- Add upload_status column
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS upload_status VARCHAR(50) DEFAULT 'pending';

-- Add ocr_job_id column
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS ocr_job_id UUID;

-- Add ocr_completed_at column
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS ocr_completed_at TIMESTAMP WITH TIME ZONE;

-- Add meta_data column (rename ocr_extracted_data to meta_data if needed, or keep both)
ALTER TABLE receipt_documents 
ADD COLUMN IF NOT EXISTS meta_data JSONB DEFAULT '{}'::jsonb;

-- Update existing rows to have file_id (use id as file_id for existing records)
UPDATE receipt_documents 
SET file_id = id 
WHERE file_id IS NULL;

-- Now make file_id NOT NULL after populating it
ALTER TABLE receipt_documents 
ALTER COLUMN file_id SET NOT NULL;

-- Update existing rows to have upload_status
UPDATE receipt_documents 
SET upload_status = 'completed' 
WHERE upload_status IS NULL;

-- Create index on file_id
CREATE INDEX IF NOT EXISTS idx_receipt_documents_file_id ON receipt_documents(file_id);

-- Create index on upload_status
CREATE INDEX IF NOT EXISTS idx_receipt_documents_upload_status ON receipt_documents(upload_status);



























