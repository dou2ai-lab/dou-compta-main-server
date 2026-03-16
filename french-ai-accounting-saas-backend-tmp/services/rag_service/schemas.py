# -----------------------------------------------------------------------------
# File: schemas.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Pydantic schemas for RAG service
# -----------------------------------------------------------------------------

"""
Pydantic schemas for RAG Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EmbedDocumentRequest(BaseModel):
    """Request to embed a document"""
    document_type: str = Field(..., pattern="^(policy|urssaf|vat_rule|expense|report)$")
    document_id: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class EmbedDocumentResponse(BaseModel):
    """Response after embedding document"""
    success: bool
    document_type: str
    document_id: str
    chunks_created: int
    message: Optional[str] = None

class QARequest(BaseModel):
    """Q&A request"""
    question: str = Field(..., min_length=1)
    query_type: str = Field(default="hybrid", pattern="^(sql|rag|hybrid)$")

class QAResponse(BaseModel):
    """Q&A response"""
    success: bool
    answer: str
    explanation: Optional[str] = None
    query_type: str
    sql_query: Optional[str] = None
    sql_results: Optional[List[Dict[str, Any]]] = None
    retrieved_documents: Optional[List[Dict[str, Any]]] = None
    confidence_score: str
    session_id: str
    error: Optional[str] = None

class SearchRequest(BaseModel):
    """Document search request"""
    query: str = Field(..., min_length=1)
    document_types: Optional[List[str]] = None
    top_k: int = Field(default=5, ge=1, le=20)

class SearchResponse(BaseModel):
    """Document search response"""
    results: List[Dict[str, Any]]
    total: int

# Phase 23 Schemas

class CoPilotRequest(BaseModel):
    """Co-pilot query request"""
    query: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None

class CoPilotResponse(BaseModel):
    """Co-pilot response"""
    success: bool
    answer: str
    citations: List[Dict[str, Any]]
    reasoning_steps: List[Dict[str, Any]]
    confidence_score: str
    query_type: str
    retrieved_documents: List[Dict[str, Any]]
    session_id: str
    error: Optional[str] = None

