# -----------------------------------------------------------------------------
# File: embeddings.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Document embeddings pipeline
# -----------------------------------------------------------------------------

"""
Document Embeddings Pipeline
Generates embeddings for policies, URSSAF guidelines, VAT rules, etc.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
import structlog
import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings
from .models import DocumentEmbedding

logger = structlog.get_logger()

class EmbeddingsPipeline:
    """Pipeline for generating and storing document embeddings"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load embedding model"""
        try:
            self.model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device=settings.EMBEDDING_DEVICE
            )
            logger.info("embedding_model_loaded", model=settings.EMBEDDING_MODEL)
        except Exception as e:
            logger.error("embedding_model_load_error", error=str(e))
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            if not self.model:
                raise ValueError("Embedding model not loaded")
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error("generate_embedding_error", error=str(e))
            raise
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into chunks"""
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    async def embed_document(
        self,
        document_type: str,
        document_id: str,
        title: str,
        content: str,
        created_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentEmbedding]:
        """Embed a document (may create multiple chunks)"""
        try:
            # Chunk the content
            chunks = self.chunk_text(content)
            
            embeddings = []
            
            for idx, chunk in enumerate(chunks):
                # Generate embedding
                embedding_vector = self.generate_embedding(chunk)
                
                # Create document embedding record
                doc_embedding = DocumentEmbedding(
                    tenant_id=self.tenant_id,
                    document_type=document_type,
                    document_id=document_id,
                    document_title=title,
                    document_content=content,
                    chunk_index=idx,
                    chunk_text=chunk,
                    embedding_model=settings.EMBEDDING_MODEL,
                    embedding_dimension=len(embedding_vector),
                    metadata_json=metadata or {},
                    created_by=created_by
                )
                
                self.db.add(doc_embedding)
                await self.db.flush()
                
                # Store embedding vector in pgvector column
                # Note: This requires pgvector extension and vector column type
                await self._store_embedding_vector(doc_embedding.id, embedding_vector)
                
                embeddings.append(doc_embedding)
            
            await self.db.commit()
            logger.info("document_embedded", document_type=document_type, document_id=document_id, chunks=len(chunks))
            
            return embeddings
            
        except Exception as e:
            await self.db.rollback()
            logger.error("embed_document_error", error=str(e))
            raise
    
    async def _store_embedding_vector(self, embedding_id: str, vector: List[float]):
        """Store embedding vector in pgvector column"""
        try:
            # Convert to PostgreSQL vector format
            vector_str = '[' + ','.join(map(str, vector)) + ']'
            
            # Update the embedding vector column (CAST avoids :vector::vector parsing as two params with asyncpg)
            await self.db.execute(
                text("""
                    UPDATE document_embeddings
                    SET embedding = CAST(:vector AS vector)
                    WHERE id = :embedding_id
                """),
                {"vector": vector_str, "embedding_id": embedding_id}
            )
            
        except Exception as e:
            logger.error("store_embedding_vector_error", error=str(e))
            # If pgvector is not available, we can store as JSONB as fallback
            pass
    
    async def embed_policies(self, created_by: Optional[str] = None) -> int:
        """Embed all expense policies"""
        try:
            # Query policies from expense_policies table
            result = await self.db.execute(
                text("""
                    SELECT id, name, description, policy_rules as rules
                    FROM expense_policies
                    WHERE tenant_id = :tenant_id
                    AND deleted_at IS NULL
                """),
                {"tenant_id": self.tenant_id}
            )
            policies = result.fetchall()
            
            count = 0
            for policy in policies:
                # Check if already embedded
                existing = await self.db.execute(
                    select(DocumentEmbedding).where(
                        and_(
                            DocumentEmbedding.tenant_id == self.tenant_id,
                            DocumentEmbedding.document_type == "policy",
                            DocumentEmbedding.document_id == str(policy.id),
                            DocumentEmbedding.deleted_at.is_(None)
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue
                
                # Create content from policy
                content = f"""
                Policy: {policy.name or 'Unnamed Policy'}
                Description: {policy.description or ''}
                Rules: {policy.rules or {}}
                """
                
                await self.embed_document(
                    document_type="policy",
                    document_id=str(policy.id),
                    title=policy.name or "Policy",
                    content=content,
                    created_by=created_by,
                    metadata={"policy_id": str(policy.id)}
                )
                count += 1
            
            logger.info("policies_embedded", count=count)
            return count
            
        except Exception as e:
            logger.error("embed_policies_error", error=str(e))
            return 0
    
    async def embed_vat_rules(self, created_by: Optional[str] = None) -> int:
        """Embed all VAT rules"""
        try:
            # Query VAT rules from vat_rules table (columns: vat_rate, category, merchant_pattern, vat_code)
            result = await self.db.execute(
                text("""
                    SELECT id, category, vat_rate, merchant_pattern, vat_code
                    FROM vat_rules
                    WHERE tenant_id = :tenant_id
                    AND deleted_at IS NULL
                """),
                {"tenant_id": self.tenant_id}
            )
            rules = result.fetchall()
            
            count = 0
            for rule in rules:
                # Check if already embedded
                existing = await self.db.execute(
                    select(DocumentEmbedding).where(
                        and_(
                            DocumentEmbedding.tenant_id == self.tenant_id,
                            DocumentEmbedding.document_type == "vat_rule",
                            DocumentEmbedding.document_id == str(rule.id),
                            DocumentEmbedding.deleted_at.is_(None)
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue
                rate_val = float(rule.vat_rate) if rule.vat_rate is not None else None
                content = (
                    f"VAT Rule: {rule.category or 'Uncategorized'}\n"
                    f"Rate: {rate_val}%\n"
                    f"Merchant pattern: {rule.merchant_pattern or ''}\n"
                    f"VAT code: {rule.vat_code or ''}"
                )
                await self.embed_document(
                    document_type="vat_rule",
                    document_id=str(rule.id),
                    title=f"VAT Rule: {rule.category or 'Uncategorized'}",
                    content=content,
                    created_by=created_by,
                    metadata={"vat_rule_id": str(rule.id), "rate": rate_val}
                )
                count += 1
            
            logger.info("vat_rules_embedded", count=count)
            return count
            
        except Exception as e:
            logger.error("embed_vat_rules_error", error=str(e))
            return 0

    async def embed_receipts(self, created_by: Optional[str] = None) -> int:
        """Embed all receipt_documents (existing receipts) into document_embeddings for RAG."""
        try:
            result = await self.db.execute(
                text("""
                    SELECT id, tenant_id, file_id, file_name, meta_data
                    FROM receipt_documents
                    WHERE tenant_id = :tenant_id
                    AND deleted_at IS NULL
                """),
                {"tenant_id": self.tenant_id}
            )
            rows = result.fetchall()
            count = 0
            for row in rows:
                receipt_id = str(row.id)
                # Skip if already embedded
                existing = await self.db.execute(
                    select(DocumentEmbedding).where(
                        and_(
                            DocumentEmbedding.tenant_id == self.tenant_id,
                            DocumentEmbedding.document_type == "receipt",
                            DocumentEmbedding.document_id == receipt_id,
                            DocumentEmbedding.deleted_at.is_(None)
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    continue
                meta = row.meta_data or {}
                ocr = meta.get("ocr") or {}
                extraction = meta.get("extraction") or {}
                ocr_text = ocr.get("text") or ocr.get("ocr_text") or ""
                merchant = extraction.get("merchant_name") or ocr.get("merchant_name")
                expense_date = extraction.get("expense_date") or ocr.get("date")
                total = extraction.get("total_amount") or ocr.get("total_amount")
                currency = extraction.get("currency") or ocr.get("currency") or "EUR"
                title_parts = ["Receipt"]
                if merchant:
                    title_parts.append(str(merchant))
                if expense_date:
                    title_parts.append(str(expense_date))
                title = " - ".join(title_parts)
                content_lines = [
                    f"Receipt ID: {receipt_id}",
                    f"File name: {getattr(row, 'file_name', '') or 'receipt'}",
                    f"Tenant ID: {self.tenant_id}",
                    f"Merchant: {merchant or 'Unknown'}",
                    f"Date: {expense_date or ''}",
                    f"Total amount: {total} {currency}".strip(),
                    "",
                    "OCR Text:",
                    ocr_text or "",
                ]
                content = "\n".join(content_lines)
                metadata = {
                    "receipt_id": receipt_id,
                    "tenant_id": self.tenant_id,
                    "file_id": str(row.file_id) if row.file_id else None,
                    "merchant_name": merchant,
                    "expense_date": str(expense_date) if expense_date else None,
                    "total_amount": float(total) if total is not None else None,
                }
                await self.embed_document(
                    document_type="receipt",
                    document_id=receipt_id,
                    title=title,
                    content=content,
                    created_by=created_by,
                    metadata=metadata,
                )
                count += 1
            logger.info("receipts_embedded", count=count)
            return count
        except Exception as e:
            logger.error("embed_receipts_error", error=str(e))
            return 0

    async def search_similar(
        self,
        query: str,
        document_types: Optional[List[str]] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity"""
        try:
            top_k = top_k or settings.TOP_K_RESULTS
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            query_vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Build query
            query_sql = """
                SELECT 
                    id,
                    document_type,
                    document_id,
                    document_title,
                    chunk_text,
                    metadata,
                    1 - (embedding <=> CAST(:query_vector AS vector)) as similarity
                FROM document_embeddings
                WHERE tenant_id = :tenant_id
                AND deleted_at IS NULL
                AND embedding IS NOT NULL
            """
            
            params = {
                "query_vector": query_vector_str,
                "tenant_id": self.tenant_id
            }
            
            if document_types:
                query_sql += " AND document_type = ANY(:document_types)"
                params["document_types"] = document_types
            
            query_sql += """
                ORDER BY embedding <=> CAST(:query_vector AS vector)
                LIMIT :top_k
            """
            params["top_k"] = top_k
            
            result = await self.db.execute(text(query_sql), params)
            rows = result.fetchall()
            
            results = []
            for row in rows:
                if row.similarity >= settings.SIMILARITY_THRESHOLD:
                    results.append({
                        "id": str(row.id),
                        "document_type": row.document_type,
                        "document_id": row.document_id,
                        "document_title": row.document_title,
                        "chunk_text": row.chunk_text,
                        "similarity": float(row.similarity),
                        "metadata": row.metadata or {}
                    })
            
            return results
            
        except Exception as e:
            logger.error("search_similar_error", error=str(e))
            # Ensure failed transaction is cleared before fallback query
            await self.db.rollback()
            # Fallback to text search if vector search fails
            return await self._fallback_text_search(query, document_types, top_k)
    
    async def _fallback_text_search(
        self,
        query: str,
        document_types: Optional[List[str]] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """Fallback text search if vector search is unavailable"""
        try:
            top_k = top_k or settings.TOP_K_RESULTS
            
            query_builder = select(DocumentEmbedding).where(
                and_(
                    DocumentEmbedding.tenant_id == self.tenant_id,
                    DocumentEmbedding.deleted_at.is_(None),
                    DocumentEmbedding.chunk_text.ilike(f"%{query}%")
                )
            )
            
            if document_types:
                query_builder = query_builder.where(
                    DocumentEmbedding.document_type.in_(document_types)
                )
            
            query_builder = query_builder.limit(top_k)
            
            result = await self.db.execute(query_builder)
            embeddings = result.scalars().all()
            
            return [
                {
                    "id": str(e.id),
                    "document_type": e.document_type,
                    "document_id": e.document_id,
                    "document_title": e.document_title,
                    "chunk_text": e.chunk_text,
                    "similarity": 0.8,  # Default similarity for text search
                    "metadata": e.metadata_json or {}
                }
                for e in embeddings
            ]
            
        except Exception as e:
            logger.error("fallback_text_search_error", error=str(e))
            return []
