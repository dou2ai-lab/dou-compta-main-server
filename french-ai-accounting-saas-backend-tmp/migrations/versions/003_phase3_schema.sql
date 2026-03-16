-- Phase 3 Schema Additions
-- Dou Expense & Audit AI – France Edition
-- LLM Post-Processing, Validation, Auto Expense Creation

-- ============================================================================
-- NORMALIZED EXTRACTIONS
-- ============================================================================

CREATE TABLE normalized_extractions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipt_documents(id) ON DELETE CASCADE,
    ocr_result_id UUID REFERENCES ocr_results(id) ON DELETE SET NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Extracted Data (JSONB with confidence scores)
    merchant_name VARCHAR(255),
    merchant_name_confidence DECIMAL(5, 4),
    merchant_address TEXT,
    merchant_address_confidence DECIMAL(5, 4),
    expense_date DATE NOT NULL,
    expense_date_confidence DECIMAL(5, 4),
    expense_time TIME,
    expense_time_confidence DECIMAL(5, 4),
    total_amount DECIMAL(12, 2) NOT NULL,
    total_amount_confidence DECIMAL(5, 4),
    net_amount DECIMAL(12, 2),
    net_amount_confidence DECIMAL(5, 4),
    vat_rate DECIMAL(5, 2) NOT NULL,
    vat_rate_confidence DECIMAL(5, 4),
    vat_amount DECIMAL(12, 2) NOT NULL,
    vat_amount_confidence DECIMAL(5, 4),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    currency_confidence DECIMAL(5, 4),
    
    -- Overall Confidence
    overall_confidence DECIMAL(5, 4) NOT NULL,
    
    -- Full Extraction Data (JSONB for flexibility)
    extraction_data JSONB NOT NULL,
    
    -- Validation Status
    validation_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, passed, failed
    validation_errors JSONB, -- Array of validation errors
    validation_warnings JSONB, -- Array of validation warnings
    
    -- LLM Processing Metadata
    llm_job_id UUID,
    llm_provider VARCHAR(50), -- openai, anthropic, local
    llm_model VARCHAR(100), -- gpt-4, claude-3-opus, etc.
    llm_tokens_used INTEGER,
    llm_cost_estimate DECIMAL(10, 4),
    
    -- Processing Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_normalized_extractions_receipt_id ON normalized_extractions(receipt_id);
CREATE INDEX idx_normalized_extractions_tenant_id ON normalized_extractions(tenant_id);
CREATE INDEX idx_normalized_extractions_user_id ON normalized_extractions(user_id);
CREATE INDEX idx_normalized_extractions_status ON normalized_extractions(status);
CREATE INDEX idx_normalized_extractions_validation_status ON normalized_extractions(validation_status);
CREATE INDEX idx_normalized_extractions_expense_date ON normalized_extractions(expense_date);
CREATE INDEX idx_normalized_extractions_created_at ON normalized_extractions(created_at DESC);
CREATE INDEX idx_normalized_extractions_deleted_at ON normalized_extractions(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_normalized_extractions_llm_job_id ON normalized_extractions(llm_job_id);

-- ============================================================================
-- EXPENSE LINES
-- ============================================================================

CREATE TABLE expense_lines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_id UUID NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Line Item Details
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(10, 3),
    unit_price DECIMAL(12, 2),
    amount DECIMAL(12, 2) NOT NULL,
    vat_rate DECIMAL(5, 2),
    vat_amount DECIMAL(12, 2),
    
    -- Metadata
    category VARCHAR(100), -- Optional categorization
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_expense_line_number UNIQUE (expense_id, line_number)
);

CREATE INDEX idx_expense_lines_expense_id ON expense_lines(expense_id);
CREATE INDEX idx_expense_lines_tenant_id ON expense_lines(tenant_id);
CREATE INDEX idx_expense_lines_deleted_at ON expense_lines(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- WORKER JOBS
-- ============================================================================

CREATE TABLE worker_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(255) UNIQUE NOT NULL, -- Celery task ID
    job_type VARCHAR(100) NOT NULL, -- llm_processing, validation, expense_creation
    receipt_id UUID REFERENCES receipt_documents(id) ON DELETE SET NULL,
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Job Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed, retrying
    priority INTEGER NOT NULL DEFAULT 5, -- 1 (high) to 10 (low)
    
    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_seconds INTEGER,
    
    -- Retry Information
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Error Information
    error_code VARCHAR(100),
    error_message TEXT,
    error_traceback TEXT,
    
    -- Job Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    result JSONB, -- Job result (if applicable)
    
    -- Idempotency
    idempotency_key VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_worker_jobs_job_id ON worker_jobs(job_id);
CREATE INDEX idx_worker_jobs_job_type ON worker_jobs(job_type);
CREATE INDEX idx_worker_jobs_receipt_id ON worker_jobs(receipt_id);
CREATE INDEX idx_worker_jobs_tenant_id ON worker_jobs(tenant_id);
CREATE INDEX idx_worker_jobs_status ON worker_jobs(status);
CREATE INDEX idx_worker_jobs_priority ON worker_jobs(priority);
CREATE INDEX idx_worker_jobs_queued_at ON worker_jobs(queued_at DESC);
CREATE INDEX idx_worker_jobs_idempotency_key ON worker_jobs(idempotency_key);
CREATE INDEX idx_worker_jobs_deleted_at ON worker_jobs(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- EXTRACTION STATUS TRACKING
-- ============================================================================

CREATE TABLE extraction_statuses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL UNIQUE REFERENCES receipt_documents(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Stage Statuses
    ocr_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    ocr_job_id UUID,
    ocr_completed_at TIMESTAMP WITH TIME ZONE,
    
    llm_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    llm_job_id UUID,
    llm_completed_at TIMESTAMP WITH TIME ZONE,
    
    validation_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    validation_job_id UUID,
    validation_completed_at TIMESTAMP WITH TIME ZONE,
    
    expense_creation_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    expense_creation_job_id UUID,
    expense_creation_completed_at TIMESTAMP WITH TIME ZONE,
    expense_id UUID REFERENCES expenses(id) ON DELETE SET NULL,
    
    -- Overall Status
    overall_status VARCHAR(50) NOT NULL DEFAULT 'ocr_pending', -- ocr_pending, llm_processing, validation, expense_creation, expense_created, failed
    progress INTEGER NOT NULL DEFAULT 0, -- 0-100
    current_stage VARCHAR(50),
    
    -- Error Information
    error_stage VARCHAR(50), -- Which stage failed
    error_message TEXT,
    error_code VARCHAR(100),
    
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_extraction_statuses_receipt_id ON extraction_statuses(receipt_id);
CREATE INDEX idx_extraction_statuses_tenant_id ON extraction_statuses(tenant_id);
CREATE INDEX idx_extraction_statuses_overall_status ON extraction_statuses(overall_status);
CREATE INDEX idx_extraction_statuses_expense_id ON extraction_statuses(expense_id);
CREATE INDEX idx_extraction_statuses_last_updated ON extraction_statuses(last_updated DESC);

-- ============================================================================
-- UPDATE EXPENSES TABLE
-- ============================================================================

-- Add link to normalized extraction
ALTER TABLE expenses
ADD COLUMN IF NOT EXISTS normalized_extraction_id UUID REFERENCES normalized_extractions(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_expenses_normalized_extraction_id ON expenses(normalized_extraction_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER update_normalized_extractions_updated_at BEFORE UPDATE ON normalized_extractions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_expense_lines_updated_at BEFORE UPDATE ON expense_lines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_worker_jobs_updated_at BEFORE UPDATE ON worker_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_extraction_statuses_updated_at BEFORE UPDATE ON extraction_statuses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to update extraction status when stage completes
CREATE OR REPLACE FUNCTION update_extraction_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update extraction_statuses based on job completion
    IF TG_TABLE_NAME = 'normalized_extractions' THEN
        UPDATE extraction_statuses
        SET llm_status = NEW.status,
            llm_job_id = NEW.llm_job_id,
            llm_completed_at = NEW.processing_completed_at,
            overall_status = CASE
                WHEN NEW.status = 'completed' THEN 'validation'
                WHEN NEW.status = 'failed' THEN 'failed'
                ELSE overall_status
            END,
            current_stage = CASE
                WHEN NEW.status = 'completed' THEN 'validation'
                WHEN NEW.status = 'failed' THEN 'llm_processing'
                ELSE current_stage
            END,
            progress = CASE
                WHEN NEW.status = 'completed' THEN 50
                WHEN NEW.status = 'failed' THEN 25
                ELSE progress
            END,
            error_stage = CASE
                WHEN NEW.status = 'failed' THEN 'llm_processing'
                ELSE error_stage
            END,
            error_message = CASE
                WHEN NEW.status = 'failed' THEN 'LLM processing failed'
                ELSE error_message
            END,
            last_updated = CURRENT_TIMESTAMP
        WHERE receipt_id = NEW.receipt_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_extraction_status_llm
    AFTER UPDATE OF status ON normalized_extractions
    FOR EACH ROW
    WHEN (NEW.status IS DISTINCT FROM OLD.status)
    EXECUTE FUNCTION update_extraction_status();

-- ============================================================================
-- VIEWS FOR MONITORING
-- ============================================================================

-- View for LLM processing statistics
CREATE OR REPLACE VIEW llm_processing_stats AS
SELECT
    DATE_TRUNC('hour', created_at) AS hour,
    llm_provider,
    llm_model,
    status,
    COUNT(*) AS job_count,
    AVG(processing_time_seconds) AS avg_processing_time_seconds,
    AVG(overall_confidence) AS avg_confidence,
    SUM(llm_tokens_used) AS total_tokens,
    SUM(llm_cost_estimate) AS total_cost,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_count,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count
FROM normalized_extractions
WHERE deleted_at IS NULL
GROUP BY DATE_TRUNC('hour', created_at), llm_provider, llm_model, status;

-- View for worker job statistics
CREATE OR REPLACE VIEW worker_job_stats AS
SELECT
    DATE_TRUNC('hour', queued_at) AS hour,
    job_type,
    status,
    COUNT(*) AS job_count,
    AVG(processing_time_seconds) AS avg_processing_time_seconds,
    AVG(retry_count) AS avg_retry_count,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_count,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count
FROM worker_jobs
WHERE deleted_at IS NULL
GROUP BY DATE_TRUNC('hour', queued_at), job_type, status;

-- View for extraction pipeline statistics
CREATE OR REPLACE VIEW extraction_pipeline_stats AS
SELECT
    DATE_TRUNC('hour', created_at) AS hour,
    overall_status,
    COUNT(*) AS receipt_count,
    AVG(progress) AS avg_progress,
    COUNT(*) FILTER (WHERE overall_status = 'expense_created') AS success_count,
    COUNT(*) FILTER (WHERE overall_status = 'failed') AS failed_count
FROM extraction_statuses
GROUP BY DATE_TRUNC('hour', created_at), overall_status;

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Ensure validation status is valid
ALTER TABLE normalized_extractions
ADD CONSTRAINT check_validation_status CHECK (validation_status IN ('pending', 'passed', 'failed'));

-- Ensure status is valid
ALTER TABLE normalized_extractions
ADD CONSTRAINT check_normalized_extraction_status CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

-- Ensure worker job status is valid
ALTER TABLE worker_jobs
ADD CONSTRAINT check_worker_job_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retrying'));

-- Ensure extraction status values are valid
ALTER TABLE extraction_statuses
ADD CONSTRAINT check_extraction_statuses CHECK (
    ocr_status IN ('pending', 'processing', 'completed', 'failed') AND
    llm_status IN ('pending', 'processing', 'completed', 'failed') AND
    validation_status IN ('pending', 'processing', 'completed', 'failed') AND
    expense_creation_status IN ('pending', 'processing', 'completed', 'failed') AND
    overall_status IN ('ocr_pending', 'llm_processing', 'validation', 'expense_creation', 'expense_created', 'failed')
);

-- Ensure confidence scores are in valid range
ALTER TABLE normalized_extractions
ADD CONSTRAINT check_confidence_scores CHECK (
    merchant_name_confidence >= 0 AND merchant_name_confidence <= 1 AND
    expense_date_confidence >= 0 AND expense_date_confidence <= 1 AND
    total_amount_confidence >= 0 AND total_amount_confidence <= 1 AND
    vat_rate_confidence >= 0 AND vat_rate_confidence <= 1 AND
    vat_amount_confidence >= 0 AND vat_amount_confidence <= 1 AND
    overall_confidence >= 0 AND overall_confidence <= 1
);

-- Ensure retry count doesn't exceed max
ALTER TABLE worker_jobs
ADD CONSTRAINT check_worker_job_retries CHECK (retry_count <= max_retries);

-- Ensure progress is in valid range
ALTER TABLE extraction_statuses
ADD CONSTRAINT check_progress_range CHECK (progress >= 0 AND progress <= 100);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE normalized_extractions IS 'Stores LLM-processed and normalized receipt extraction data';
COMMENT ON TABLE expense_lines IS 'Line items for expenses (from receipts with line items)';
COMMENT ON TABLE worker_jobs IS 'Tracks background job processing (Celery tasks)';
COMMENT ON TABLE extraction_statuses IS 'Tracks end-to-end extraction pipeline status';

COMMENT ON COLUMN normalized_extractions.extraction_data IS 'Full extraction data with confidence scores in JSONB format';
COMMENT ON COLUMN normalized_extractions.overall_confidence IS 'Weighted average of all field confidence scores';
COMMENT ON COLUMN worker_jobs.job_id IS 'Celery task ID for tracking';
COMMENT ON COLUMN extraction_statuses.progress IS 'Overall pipeline progress (0-100)';














