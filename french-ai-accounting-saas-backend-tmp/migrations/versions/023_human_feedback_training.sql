-- Phase 33 — Human-in-the-loop feedback + training dataset + extraction cache

CREATE TABLE IF NOT EXISTS receipt_field_corrections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receipt_id UUID NOT NULL REFERENCES receipt_documents(id),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  user_id UUID NOT NULL REFERENCES users(id),
  field_name VARCHAR(100) NOT NULL,
  predicted_value JSONB,
  corrected_value JSONB,
  predicted_snapshot JSONB,
  ocr_snapshot JSONB,
  llm_snapshot JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_receipt_field_corrections_receipt_id ON receipt_field_corrections(receipt_id);
CREATE INDEX IF NOT EXISTS idx_receipt_field_corrections_tenant_id ON receipt_field_corrections(tenant_id);

CREATE TABLE IF NOT EXISTS receipt_training_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  receipt_id UUID NOT NULL REFERENCES receipt_documents(id),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  user_id UUID REFERENCES users(id),
  file_hash VARCHAR(64),
  document_type VARCHAR(50),
  ocr_output JSONB,
  llm_output JSONB,
  extraction_output JSONB,
  corrected_output JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_receipt_training_snapshots_receipt_id ON receipt_training_snapshots(receipt_id);
CREATE INDEX IF NOT EXISTS idx_receipt_training_snapshots_file_hash ON receipt_training_snapshots(file_hash);

CREATE TABLE IF NOT EXISTS receipt_extraction_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_hash VARCHAR(64) NOT NULL,
  document_type VARCHAR(50) NOT NULL,
  extraction_output JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_receipt_extraction_cache_filehash_doctype UNIQUE (file_hash, document_type)
);

CREATE INDEX IF NOT EXISTS idx_receipt_extraction_cache_file_hash ON receipt_extraction_cache(file_hash);

