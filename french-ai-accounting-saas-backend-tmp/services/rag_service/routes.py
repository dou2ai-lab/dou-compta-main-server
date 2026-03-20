# -----------------------------------------------------------------------------
# File: routes.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: RAG service routes
# -----------------------------------------------------------------------------

"""
RAG Service Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import structlog
import uuid

from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user, get_user_permissions, get_user_roles
from .qa_service import QAService
from .embeddings import EmbeddingsPipeline
from .agentic_copilot import AgenticCoPilot
from .schemas import (
    EmbedDocumentRequest,
    EmbedDocumentResponse,
    QARequest,
    QAResponse,
    SearchRequest,
    SearchResponse,
    CoPilotRequest,
    CoPilotResponse
)

logger = structlog.get_logger()
router = APIRouter()

async def require_audit_permission(current_user: User, db: AsyncSession):
    """Check if user has audit permissions (or Admin role)."""
    if getattr(current_user, "_dev_mock_no_db", False):
        return  # Skip permission check when using mock user (DB unreachable)
    permissions = await get_user_permissions(current_user, db)
    if "audit:read" in permissions:
        return
    # Allow Admin role even if permission row was missing
    roles = await get_user_roles(current_user, db)
    if roles and any(str(r).lower() == "admin" for r in roles):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized"
    )

@router.post("/embed", response_model=EmbedDocumentResponse)
async def embed_document(
    request: EmbedDocumentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Embed a document"""
    await require_audit_permission(current_user, db)
    
    try:
        pipeline = EmbeddingsPipeline(db, str(current_user.tenant_id))
        
        embeddings = await pipeline.embed_document(
            document_type=request.document_type,
            document_id=request.document_id,
            title=request.title,
            content=request.content,
            created_by=str(current_user.id),
            metadata=request.metadata
        )
        
        await db.commit()
        
        return EmbedDocumentResponse(
            success=True,
            document_type=request.document_type,
            document_id=request.document_id,
            chunks_created=len(embeddings),
            message=f"Document embedded successfully with {len(embeddings)} chunks"
        )
    except Exception as e:
        await db.rollback()
        logger.error("embed_document_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to embed document")

@router.post("/embed/policies", response_model=Dict[str, Any])
async def embed_all_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Embed all expense policies"""
    await require_audit_permission(current_user, db)
    
    try:
        pipeline = EmbeddingsPipeline(db, str(current_user.tenant_id))
        count = await pipeline.embed_policies(created_by=str(current_user.id))
        await db.commit()
        
        return {
            "success": True,
            "policies_embedded": count,
            "message": f"Embedded {count} policies"
        }
    except Exception as e:
        await db.rollback()
        logger.error("embed_policies_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to embed policies")

@router.post("/embed/vat-rules", response_model=Dict[str, Any])
async def embed_all_vat_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Embed all VAT rules"""
    await require_audit_permission(current_user, db)
    
    try:
        pipeline = EmbeddingsPipeline(db, str(current_user.tenant_id))
        count = await pipeline.embed_vat_rules(created_by=str(current_user.id))
        await db.commit()
        
        return {
            "success": True,
            "vat_rules_embedded": count,
            "message": f"Embedded {count} VAT rules"
        }
    except Exception as e:
        await db.rollback()
        logger.error("embed_vat_rules_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to embed VAT rules")


@router.post("/embed/receipts", response_model=Dict[str, Any])
async def embed_all_receipts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Embed all existing receipt_documents into RAG (backfill). Use when document_embeddings is empty but receipt_documents has rows."""
    await require_audit_permission(current_user, db)
    
    try:
        pipeline = EmbeddingsPipeline(db, str(current_user.tenant_id))
        count = await pipeline.embed_receipts(created_by=str(current_user.id))
        await db.commit()
        
        return {
            "success": True,
            "receipts_embedded": count,
            "message": f"Embedded {count} receipt(s) into RAG"
        }
    except Exception as e:
        await db.rollback()
        logger.error("embed_receipts_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to embed receipts")


@router.post("/qa", response_model=QAResponse)
async def ask_question(
    request: QARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Ask a question and get an answer"""
    await require_audit_permission(current_user, db)
    
    try:
        service = QAService(db, str(current_user.tenant_id))
        
        result = await service.answer_question(
            question=request.question,
            user_id=str(current_user.id),
            query_type=request.query_type
        )
        
        await db.commit()
        
        return QAResponse(**result)
    except Exception as e:
        await db.rollback()
        logger.error("ask_question_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to answer question")

@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search for similar documents"""
    await require_audit_permission(current_user, db)
    
    try:
        pipeline = EmbeddingsPipeline(db, str(current_user.tenant_id))
        
        results = await pipeline.search_similar(
            query=request.query,
            document_types=request.document_types,
            top_k=request.top_k
        )
        
        return SearchResponse(
            results=results,
            total=len(results)
        )
    except Exception as e:
        logger.error("search_documents_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to search documents")

# Phase 23 Routes

@router.post("/copilot", response_model=CoPilotResponse)
async def copilot_query(
    request: CoPilotRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Agentic Co-Pilot query with LLM orchestration and citations"""
    await require_audit_permission(current_user, db)
    
    try:
        copilot = AgenticCoPilot(db, str(current_user.tenant_id))
        
        result = await copilot.process_query(
            query=request.query,
            user_id=str(current_user.id),
            context=request.context
        )
        
        await db.commit()
        
        return CoPilotResponse(**result)
    except Exception as e:
        await db.rollback()
        err_msg = str(e)
        # Dev fallback: when DB unreachable from host, return helpful message
        if getattr(current_user, "_dev_mock_no_db", False) or "password" in err_msg.lower() or "connection" in err_msg.lower():
            logger.warning("copilot_db_unreachable", error=err_msg, message="Run RAG in Docker for full copilot: cd infrastructure && docker compose up -d rag")
            return CoPilotResponse(
                success=False,
                answer="Database connection is unavailable from local RAG. Run RAG in Docker for full functionality: `cd infrastructure && docker compose up -d rag`",
                citations=[],
                reasoning_steps=[],
                confidence_score="0",
                query_type="fallback",
                retrieved_documents=[],
                session_id=str(uuid.uuid4()),
                error="DB unreachable from host. Use Docker: docker compose up -d rag",
            )
        logger.error("copilot_query_error", error=err_msg)
        raise HTTPException(status_code=500, detail="Failed to process co-pilot query")
