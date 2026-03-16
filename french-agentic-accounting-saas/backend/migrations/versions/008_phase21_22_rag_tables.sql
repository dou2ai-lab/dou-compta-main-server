-- Migration: Phase 21 & 22 - RAG Service Tables
-- Dou Expense & Audit AI – France Edition
-- Vector Database and Q&A Service

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- DOCUMENT EMBEDDINGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Document information
    document_type VARCHAR(50) NOT NULL, -- policy, urssaf, vat_rule, expense, report
    document_id VARCHAR(255), -- Reference to original document
    document_title VARCHAR(255) NOT NULL,
    document_content TEXT NOT NULL,
    
    -- Chunk information
    chunk_index INTEGER DEFAULT 0, -- For multi-chunk documents
    chunk_text TEXT NOT NULL,
    
    -- Embedding
    embedding_model VARCHAR(100) NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    embedding vector(384), -- Vector column for pgvector (384 for all-MiniLM-L6-v2)
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    source_url VARCHAR(500),
    created_by UUID REFERENCES users(id),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_document_embeddings_tenant_id ON document_embeddings(tenant_id);
CREATE INDEX idx_document_embeddings_type ON document_embeddings(document_type);
CREATE INDEX idx_document_embeddings_document_id ON document_embeddings(document_id);
CREATE INDEX idx_document_embeddings_deleted_at ON document_embeddings(deleted_at) WHERE deleted_at IS NULL;

-- Vector similarity index (HNSW for fast approximate nearest neighbor search)
CREATE INDEX IF NOT EXISTS idx_document_embeddings_vector 
ON document_embeddings 
USING hnsw (embedding vector_cosine_ops);

-- ============================================================================
-- Q&A SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS qa_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Query information
    query TEXT NOT NULL,
    query_type VARCHAR(50), -- sql, rag, hybrid
    
    -- Response
    answer TEXT,
    explanation TEXT,
    sql_query TEXT, -- If SQL was used
    sql_results JSONB, -- SQL query results
    
    -- RAG context
    retrieved_documents JSONB, -- Retrieved document chunks
    confidence_score VARCHAR(20), -- high, medium, low
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_qa_sessions_tenant_id ON qa_sessions(tenant_id);
CREATE INDEX idx_qa_sessions_user_id ON qa_sessions(user_id);
CREATE INDEX idx_qa_sessions_created_at ON qa_sessions(created_at DESC);
CREATE INDEX idx_qa_sessions_query_type ON qa_sessions(query_type);




