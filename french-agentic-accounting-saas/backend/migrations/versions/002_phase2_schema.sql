-- Phase 2 Schema Additions
-- Dou Expense & Audit AI – France Edition
-- Receipt Upload, OCR Processing, Event-Driven Architecture

-- ============================================================================
-- RECEIPT DOCUMENTS (Enhanced from Phase 1)
-- ============================================================================

-- Add OCR-related columns to receipt_documents if not already present
ALTER TABLE receipt_documents
ADD COLUMN IF NOT EXISTS ocr_job_id UUID,
ADD COLUMN IF NOT EXISTS ocr_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS ocr_completed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS encryption_key_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64), -- SHA-256 hash for deduplication
ADD COLUMN IF NOT EXISTS upload_status VARCHAR(50) DEFAULT 'pending';

-- Update indexes
CREATE INDEX IF NOT EXISTS idx_receipt_documents_ocr_status ON receipt_documents(ocr_status);
CREATE INDEX IF NOT EXISTS idx_receipt_documents_ocr_job_id ON receipt_documents(ocr_job_id);
CREATE INDEX IF NOT EXISTS idx_receipt_documents_upload_status ON receipt_documents(upload_status);
CREATE INDEX IF NOT EXISTS idx_receipt_documents_file_hash ON receipt_documents(file_hash);

-- ============================================================================
-- OCR JOBS
-- ============================================================================

CREATE TABLE ocr_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipt_documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL, -- 'google_document_ai', 'azure_form_recognizer'
    provider_job_id VARCHAR(255), -- External job ID from OCR provider
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed, retrying
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_code VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    idempotency_key VARCHAR(255) UNIQUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ocr_jobs_receipt_id ON ocr_jobs(receipt_id);
CREATE INDEX idx_ocr_jobs_tenant_id ON ocr_jobs(tenant_id);
CREATE INDEX idx_ocr_jobs_status ON ocr_jobs(status);
CREATE INDEX idx_ocr_jobs_provider ON ocr_jobs(provider);
CREATE INDEX idx_ocr_jobs_idempotency_key ON ocr_jobs(idempotency_key);
CREATE INDEX idx_ocr_jobs_created_at ON ocr_jobs(created_at DESC);
CREATE INDEX idx_ocr_jobs_deleted_at ON ocr_jobs(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- OCR RESULTS
-- ============================================================================

CREATE TABLE ocr_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES ocr_jobs(id) ON DELETE CASCADE,
    receipt_id UUID NOT NULL REFERENCES receipt_documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Extracted Data (Normalized)
    merchant_name VARCHAR(255),
    expense_date DATE,
    total_amount DECIMAL(12, 2),
    vat_amount DECIMAL(12, 2),
    vat_rate DECIMAL(5, 2),
    currency VARCHAR(3) DEFAULT 'EUR',
    line_items JSONB, -- Array of line items if available
    
    -- Confidence Scores
    confidence_scores JSONB, -- {merchant_name: 0.95, date: 0.98, ...}
    overall_confidence DECIMAL(5, 4), -- Average confidence score
    
    -- Raw OCR Response (Encrypted or Sanitized)
    raw_response JSONB, -- Full response from OCR provider
    
    -- Normalization Metadata
    normalized_at TIMESTAMP WITH TIME ZONE,
    normalization_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Provider Information
    provider VARCHAR(50) NOT NULL,
    provider_response_id VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ocr_results_job_id ON ocr_results(job_id);
CREATE INDEX idx_ocr_results_receipt_id ON ocr_results(receipt_id);
CREATE INDEX idx_ocr_results_tenant_id ON ocr_results(tenant_id);
CREATE INDEX idx_ocr_results_provider ON ocr_results(provider);
CREATE INDEX idx_ocr_results_expense_date ON ocr_results(expense_date);
CREATE INDEX idx_ocr_results_deleted_at ON ocr_results(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- EVENT LOGS
-- ============================================================================

CREATE TABLE event_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL, -- receipt.uploaded, receipt.ocr.completed, etc.
    event_id VARCHAR(255) UNIQUE NOT NULL, -- Unique event ID for idempotency
    receipt_id UUID REFERENCES receipt_documents(id) ON DELETE SET NULL,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Event Payload
    payload JSONB NOT NULL,
    
    -- Event Metadata
    source_service VARCHAR(100) NOT NULL, -- file-service, ocr-service, etc.
    correlation_id VARCHAR(255), -- For request tracing
    idempotency_key VARCHAR(255),
    
    -- Processing Status (for consumed events)
    consumed BOOLEAN DEFAULT false,
    consumed_at TIMESTAMP WITH TIME ZONE,
    consumer_service VARCHAR(100),
    processing_error TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_logs_event_type ON event_logs(event_type);
CREATE INDEX idx_event_logs_event_id ON event_logs(event_id);
CREATE INDEX idx_event_logs_receipt_id ON event_logs(receipt_id);
CREATE INDEX idx_event_logs_tenant_id ON event_logs(tenant_id);
CREATE INDEX idx_event_logs_created_at ON event_logs(created_at DESC);
CREATE INDEX idx_event_logs_consumed ON event_logs(consumed, created_at);
CREATE INDEX idx_event_logs_correlation_id ON event_logs(correlation_id);
CREATE INDEX idx_event_logs_idempotency_key ON event_logs(idempotency_key);

-- ============================================================================
-- ENCRYPTION KEYS (For File Encryption)
-- ============================================================================

CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_id VARCHAR(255) UNIQUE NOT NULL, -- External key ID (from KMS)
    key_type VARCHAR(50) NOT NULL DEFAULT 'aes-256', -- aes-256, etc.
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rotated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_encryption_keys_key_id ON encryption_keys(key_id);
CREATE INDEX idx_encryption_keys_tenant_id ON encryption_keys(tenant_id);
CREATE INDEX idx_encryption_keys_is_active ON encryption_keys(is_active);

-- ============================================================================
-- UPDATED_AT TRIGGERS
-- ============================================================================

CREATE TRIGGER update_ocr_jobs_updated_at BEFORE UPDATE ON ocr_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ocr_results_updated_at BEFORE UPDATE ON ocr_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_receipt_documents_updated_at BEFORE UPDATE ON receipt_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FUNCTIONS FOR OCR STATUS UPDATES
-- ============================================================================

-- Function to update receipt OCR status when OCR job completes
CREATE OR REPLACE FUNCTION update_receipt_ocr_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE receipt_documents
        SET ocr_status = 'completed',
            ocr_completed_at = NEW.completed_at
        WHERE id = NEW.receipt_id;
    ELSIF NEW.status = 'failed' AND OLD.status != 'failed' THEN
        UPDATE receipt_documents
        SET ocr_status = 'failed'
        WHERE id = NEW.receipt_id;
    ELSIF NEW.status = 'processing' AND OLD.status != 'processing' THEN
        UPDATE receipt_documents
        SET ocr_status = 'processing'
        WHERE id = NEW.receipt_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_receipt_ocr_status
    AFTER UPDATE OF status ON ocr_jobs
    FOR EACH ROW
    WHEN (NEW.status IS DISTINCT FROM OLD.status)
    EXECUTE FUNCTION update_receipt_ocr_status();

-- ============================================================================
-- VIEWS FOR MONITORING
-- ============================================================================

-- View for OCR processing statistics
CREATE OR REPLACE VIEW ocr_processing_stats AS
SELECT
    DATE_TRUNC('hour', created_at) AS hour,
    provider,
    status,
    COUNT(*) AS job_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) AS avg_processing_time_seconds,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_count,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count
FROM ocr_jobs
WHERE deleted_at IS NULL
GROUP BY DATE_TRUNC('hour', created_at), provider, status;

-- View for upload statistics
CREATE OR REPLACE VIEW upload_stats AS
SELECT
    DATE_TRUNC('hour', created_at) AS hour,
    upload_status,
    mime_type,
    COUNT(*) AS upload_count,
    SUM(file_size) AS total_size_bytes,
    AVG(file_size) AS avg_size_bytes
FROM receipt_documents
WHERE deleted_at IS NULL
GROUP BY DATE_TRUNC('hour', created_at), upload_status, mime_type;

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Ensure OCR job status is valid
ALTER TABLE ocr_jobs
ADD CONSTRAINT check_ocr_job_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retrying'));

-- Ensure OCR status is valid
ALTER TABLE receipt_documents
ADD CONSTRAINT check_ocr_status CHECK (ocr_status IN ('pending', 'processing', 'completed', 'failed'));

-- Ensure upload status is valid
ALTER TABLE receipt_documents
ADD CONSTRAINT check_upload_status CHECK (upload_status IN ('pending', 'uploading', 'completed', 'failed'));

-- Ensure retry count doesn't exceed max
ALTER TABLE ocr_jobs
ADD CONSTRAINT check_retry_count CHECK (retry_count <= max_retries);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE ocr_jobs IS 'Tracks OCR processing jobs for receipt documents';
COMMENT ON TABLE ocr_results IS 'Stores normalized OCR extraction results';
COMMENT ON TABLE event_logs IS 'Audit log for all events in the system';
COMMENT ON TABLE encryption_keys IS 'Manages encryption keys for file encryption';

COMMENT ON COLUMN ocr_jobs.idempotency_key IS 'Prevents duplicate processing of the same event';
COMMENT ON COLUMN ocr_results.confidence_scores IS 'JSON object with confidence scores for each extracted field';
COMMENT ON COLUMN ocr_results.raw_response IS 'Full OCR provider response for debugging and reprocessing';
COMMENT ON COLUMN event_logs.consumed IS 'Tracks whether event has been consumed by a service';














