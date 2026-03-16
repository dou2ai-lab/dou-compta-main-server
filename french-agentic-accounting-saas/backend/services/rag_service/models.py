# -----------------------------------------------------------------------------
# File: models.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: RAG service models
# -----------------------------------------------------------------------------

"""
RAG Service Models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from common.models import Base

class DocumentEmbedding(Base):
    """Document embedding storage"""
    __tablename__ = "document_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    
    # Document information
    document_type = Column(String(50), nullable=False)  # policy, urssaf, vat_rule, expense, report
    document_id = Column(String(255))  # Reference to original document
    document_title = Column(String(255), nullable=False)
    document_content = Column(Text, nullable=False)
    
    # Chunk information
    chunk_index = Column(Integer, default=0)  # For multi-chunk documents
    chunk_text = Column(Text, nullable=False)
    
    # Embedding
    embedding_model = Column(String(100), nullable=False)
    embedding_dimension = Column(Integer, nullable=False)
    # Note: embedding vector stored separately in pgvector column
    
    # Metadata
    metadata_json = Column("metadata", JSONB, default={})
    source_url = Column(String(500))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True))

class QASession(Base):
    """Q&A session tracking"""
    __tablename__ = "qa_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Query information
    query = Column(Text, nullable=False)
    query_type = Column(String(50))  # sql, rag, hybrid
    
    # Response
    answer = Column(Text)
    explanation = Column(Text)
    sql_query = Column(Text)  # If SQL was used
    sql_results = Column(JSONB)  # SQL query results
    
    # RAG context
    retrieved_documents = Column(JSONB)  # Retrieved document chunks
    confidence_score = Column(String(20))  # high, medium, low
    
    # Metadata
    metadata_json = Column("metadata", JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
