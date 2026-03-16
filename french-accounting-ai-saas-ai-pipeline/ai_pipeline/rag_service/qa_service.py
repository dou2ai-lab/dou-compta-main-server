# -----------------------------------------------------------------------------
# File: qa_service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Audit Q&A Service
# -----------------------------------------------------------------------------

"""
Audit Q&A Service
Provides Q&A functionality with SQL querying and LLM explanations
"""
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func, and_
import structlog
import json
import uuid

from .config import settings
from .embeddings import EmbeddingsPipeline
from .models import QASession, DocumentEmbedding
from common.models import Expense, PolicyViolation, User
from sqlalchemy import text

logger = structlog.get_logger()


def _make_json_serializable(obj: Any) -> Any:
    """Convert SQL/ORM results to JSON-serializable types (avoid 'Failed to answer question' on response)."""
    if obj is None:
        return None
    if isinstance(obj, (Decimal,)):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_make_json_serializable(v) for v in obj]
    return obj


class QAService:
    """Audit Q&A Service"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.embeddings_pipeline = EmbeddingsPipeline(db, tenant_id)
        self.llm_client = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client for explanations"""
        try:
            if settings.LLM_PROVIDER == "gemini":
                import google.generativeai as genai
                if settings.GEMINI_API_KEY:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    self.llm_client = genai.GenerativeModel(getattr(settings, 'GEMINI_MODEL', 'models/gemini-2.0-flash'))
                    logger.info("llm_client_initialized", provider="gemini")
            elif settings.LLM_PROVIDER == "openai":
                import openai
                if settings.OPENAI_API_KEY:
                    self.llm_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                    logger.info("llm_client_initialized", provider="openai")
            # Add other providers as needed
        except Exception as e:
            logger.error("llm_initialization_error", error=str(e))
            self.llm_client = None
    
    async def answer_question(
        self,
        question: str,
        user_id: str,
        query_type: str = "hybrid"  # sql, rag, hybrid
    ) -> Dict[str, Any]:
        """Answer a question using SQL, RAG, or hybrid approach"""
        try:
            answer = None
            explanation = None
            sql_query = None
            sql_results = None
            retrieved_documents = []
            confidence_score = "medium"
            
            # Determine query type
            if query_type == "hybrid":
                # Try SQL first, then RAG
                sql_result = await self._try_sql_query(question)
                if sql_result["success"]:
                    answer = sql_result["answer"]
                    sql_query = sql_result["sql_query"]
                    sql_results = _make_json_serializable(sql_result.get("results") or [])
                    confidence_score = "high"
                    
                    # Enhance with RAG context
                    rag_results = await self.embeddings_pipeline.search_similar(question)
                    retrieved_documents = rag_results[:3]  # Top 3 for context
                else:
                    # Fallback to RAG
                    query_type = "rag"
            
            if query_type == "sql":
                sql_result = await self._try_sql_query(question)
                if sql_result["success"]:
                    answer = sql_result["answer"]
                    sql_query = sql_result["sql_query"]
                    sql_results = _make_json_serializable(sql_result.get("results") or [])
                    confidence_score = "high"
                else:
                    answer = "I couldn't generate a SQL query for this question. Please try rephrasing."
                    confidence_score = "low"
            
            elif query_type == "rag":
                # Restrict to document type when question clearly asks about policy, VAT, or receipts
                doc_types = self._rag_document_types_for_question(question)
                rag_results = await self.embeddings_pipeline.search_similar(
                    question, document_types=doc_types, top_k=5
                )
                if rag_results:
                    retrieved_documents = rag_results
                    # Generate answer from retrieved documents
                    answer = await self._generate_answer_from_rag(question, rag_results)
                    confidence_score = "high" if rag_results[0]["similarity"] > 0.8 else "medium"
                else:
                    answer = "I couldn't find relevant information to answer this question."
                    confidence_score = "low"
            
            # Generate LLM explanation
            if answer:
                explanation = await self._generate_explanation(question, answer, sql_results, retrieved_documents)
            
            # Save Q&A session
            session = QASession(
                tenant_id=self.tenant_id,
                user_id=user_id,
                query=question,
                query_type=query_type,
                answer=answer,
                explanation=explanation,
                sql_query=sql_query,
                sql_results=sql_results,
                retrieved_documents=retrieved_documents,
                confidence_score=confidence_score
            )
            
            self.db.add(session)
            await self.db.flush()
            
            return {
                "success": True,
                "answer": answer,
                "explanation": explanation,
                "query_type": query_type,
                "sql_query": sql_query,
                "sql_results": sql_results,
                "retrieved_documents": retrieved_documents,
                "confidence_score": confidence_score,
                "session_id": str(session.id)
            }
            
        except Exception as e:
            logger.error("answer_question_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "answer": "I encountered an error while processing your question."
            }
    
    def _extract_merchant_name_from_question(self, question: str) -> Optional[str]:
        """Extract merchant/restaurant name from phrases like 'details for restaurant name \"Ristorante\"'."""
        if not question or not question.strip():
            return None
        # Quoted name: 'Ristorante', "Ristorante", "restaurant name 'Ristorante'"
        quoted = re.search(r"[\'\"]([^\'\"]+)[\'\"]", question)
        if quoted:
            return quoted.group(1).strip()
        # "restaurant name X" or "merchant name X" (X = single word or phrase)
        for prefix in ("restaurant name ", "merchant name ", "for restaurant ", "for merchant "):
            if prefix in question.lower():
                idx = question.lower().index(prefix) + len(prefix)
                rest = question[idx:].strip()
                # Take until next comma, period, or ?
                end = len(rest)
                for sep in (",", ".", "?", "\n"):
                    if sep in rest:
                        end = min(end, rest.index(sep))
                name = rest[:end].strip()
                if name and len(name) < 200:
                    return name
        return None

    def _rag_document_types_for_question(self, question: str) -> Optional[List[str]]:
        """Return document_types to restrict RAG search when the question is clearly about policy, VAT, or receipts."""
        if not question or not question.strip():
            return None
        q = question.lower().strip()
        if any(w in q for w in ("policy", "policies", "reimbursement", "meal limit", "expense policy", "french expense", "french policy", "hotel cap", "mileage")):
            return ["policy"]
        if any(w in q for w in ("vat", "tax rate", "tva")):
            return ["vat_rule"]
        if any(w in q for w in ("receipt", "receipts", "merchant", "invoice")):
            return ["receipt"]
        return None

    async def _try_sql_query(self, question: str) -> Dict[str, Any]:
        """Try to generate and execute SQL query from question"""
        try:
            # Simple keyword-based SQL generation
            # In production, use LLM to generate SQL
            question_lower = question.lower()

            # Receipt-specific queries by receipt UUID (from receipt_documents / expenses)
            # Example: "details for receipt f5f23f59-603f-43b3-95e4-1281273bc4ed"
            import re as _re

            uuid_match = _re.search(
                r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                question,
            )
            if "receipt" in question_lower and uuid_match:
                receipt_id = uuid_match.group(0)
                sql = """
                    SELECT 
                        rd.id AS receipt_id,
                        rd.file_name,
                        rd.meta_data,
                        e.id AS expense_id,
                        e.merchant_name,
                        e.expense_date,
                        e.amount,
                        e.currency,
                        e.vat_amount,
                        e.vat_rate,
                        e.category,
                        e.description
                    FROM receipt_documents rd
                    LEFT JOIN expenses e ON rd.expense_id = e.id
                    WHERE rd.id = :receipt_id
                    AND rd.tenant_id = :tenant_id
                    AND rd.deleted_at IS NULL
                """
                result = await self.db.execute(
                    text(sql),
                    {"receipt_id": receipt_id, "tenant_id": self.tenant_id},
                )
                rows = result.fetchall()
                if rows:
                    row = rows[0]
                    date_str = (
                        row.expense_date.isoformat()[:10] if getattr(row, "expense_date", None) else "—"
                    )
                    amount = row.amount or 0
                    parts = [
                        f"Details for receipt {receipt_id}:",
                        f"- File name: {getattr(row, 'file_name', 'N/A')}",
                        f"- Merchant: {getattr(row, 'merchant_name', 'Unknown')}",
                        f"- Date: {date_str}",
                        f"- Amount: €{amount:.2f} {row.currency or 'EUR'}",
                    ]
                    if getattr(row, "vat_amount", None) is not None and getattr(row, "vat_rate", None) is not None:
                        parts.append(f"- VAT: €{row.vat_amount:.2f} at {row.vat_rate}%")
                    if getattr(row, "category", None):
                        parts.append(f"- Category: {row.category}")
                    if getattr(row, "description", None):
                        parts.append(f"- Description: {row.description}")

                    answer = "\n".join(parts)
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": sql,
                        "results": [dict(row._mapping) for row in rows],
                    }
            
            # Expense-related queries
            if "total" in question_lower and "expense" in question_lower:
                if "month" in question_lower or "period" in question_lower:
                    sql = """
                        SELECT 
                            DATE_TRUNC('month', expense_date) as month,
                            COUNT(*) as count,
                            SUM(amount) as total_amount
                        FROM expenses
                        WHERE tenant_id = :tenant_id
                        AND deleted_at IS NULL
                        GROUP BY DATE_TRUNC('month', expense_date)
                        ORDER BY month DESC
                        LIMIT 12
                    """
                else:
                    sql = """
                        SELECT 
                            COUNT(*) as total_count,
                            SUM(amount) as total_amount,
                            AVG(amount) as average_amount
                        FROM expenses
                        WHERE tenant_id = :tenant_id
                        AND deleted_at IS NULL
                    """
                
                result = await self.db.execute(text(sql), {"tenant_id": self.tenant_id})
                rows = result.fetchall()
                
                if "month" in question_lower:
                    if rows:
                        answer = f"Expense totals by month:\n"
                        for row in rows:
                            total_amount = row.total_amount or 0
                            answer += f"- {row.month}: {row.count} expenses, €{total_amount:.2f}\n"
                    else:
                        answer = "Expense totals by month: no expenses found."
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": sql,
                        "results": [dict(row._mapping) for row in rows]
                    }
                else:
                    if rows:
                        row = rows[0]
                        total_amount = row.total_amount or 0
                        average_amount = row.average_amount or 0
                        answer = (
                            "Total expenses: "
                            f"{row.total_count} expenses, €{total_amount:.2f} total, "
                            f"€{average_amount:.2f} average"
                        )
                    else:
                        answer = "Total expenses: 0 expenses, €0.00 total, €0.00 average"
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": sql,
                        "results": [dict(row._mapping) for row in rows] if rows else []
                    }
            
            # Policy violations
            elif "violation" in question_lower or "policy" in question_lower:
                sql = """
                    SELECT 
                        violation_type,
                        violation_severity,
                        COUNT(*) as count
                    FROM policy_violations
                    JOIN expenses ON policy_violations.expense_id = expenses.id
                    WHERE expenses.tenant_id = :tenant_id
                    GROUP BY violation_type, violation_severity
                    ORDER BY count DESC
                """
                
                result = await self.db.execute(text(sql), {"tenant_id": self.tenant_id})
                rows = result.fetchall()
                
                if rows:
                    answer = "Policy violations summary:\n"
                    for row in rows:
                        answer += f"- {row.violation_type} ({row.violation_severity}): {row.count} violations\n"
                    
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": sql,
                        "results": [dict(row._mapping) for row in rows]
                    }
            
            # Merchant / restaurant name: "details for restaurant name X", "expenses for Ristorante"
            merchant_name = self._extract_merchant_name_from_question(question)
            if merchant_name:
                sql = """
                    SELECT 
                        id,
                        merchant_name,
                        expense_date,
                        amount,
                        currency,
                        vat_amount,
                        vat_rate,
                        category,
                        description,
                        status,
                        created_at
                    FROM expenses
                    WHERE tenant_id = :tenant_id
                    AND deleted_at IS NULL
                    AND merchant_name ILIKE :merchant_pattern
                    ORDER BY expense_date DESC
                    LIMIT 50
                """
                pattern = f"%{merchant_name}%"
                result = await self.db.execute(
                    text(sql),
                    {"tenant_id": self.tenant_id, "merchant_pattern": pattern},
                )
                rows = result.fetchall()
                if rows:
                    answer = f"Expenses for merchant/restaurant **{merchant_name}** ({len(rows)} record(s)):\n\n"
                    for row in rows:
                        amt = row.amount or 0
                        date_str = row.expense_date.isoformat()[:10] if row.expense_date else "—"
                        answer += f"- {date_str}: €{amt:.2f} ({row.currency or 'EUR'})"
                        if row.category:
                            answer += f", category: {row.category}"
                        if row.description:
                            answer += f", {row.description[:60]}{'...' if len(str(row.description or '')) > 60 else ''}"
                        answer += "\n"
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": sql,
                        "results": [dict(row._mapping) for row in rows],
                    }
                else:
                    # Suggest actual merchant names from the DB so the user can ask for one that exists
                    hint_sql = text("""
                        SELECT DISTINCT merchant_name FROM expenses
                        WHERE tenant_id = :tenant_id AND deleted_at IS NULL AND merchant_name IS NOT NULL AND merchant_name != ''
                        ORDER BY merchant_name
                        LIMIT 10
                    """)
                    hint_result = await self.db.execute(hint_sql, {"tenant_id": self.tenant_id})
                    hint_rows = hint_result.fetchall()
                    example_names = [str(r.merchant_name).strip() for r in hint_rows if r.merchant_name]
                    if example_names:
                        answer = (
                            f"No expenses found for merchant/restaurant name matching \"{merchant_name}\".\n\n"
                            f"Merchant names in your data you can ask for: **{', '.join(example_names)}**"
                        )
                    else:
                        answer = (
                            f"No expenses found for merchant/restaurant name matching \"{merchant_name}\".\n\n"
                            "You have no expenses with a merchant name yet (or ask: \"What is the total expense?\" to confirm data)."
                        )
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": sql,
                        "results": [],
                    }

            # VAT queries
            elif "vat" in question_lower:
                sql = """
                    SELECT 
                        vat_rate,
                        COUNT(*) as count,
                        SUM(vat_amount) as total_vat,
                        SUM(amount) as total_amount
                    FROM expenses
                    WHERE tenant_id = :tenant_id
                    AND deleted_at IS NULL
                    AND vat_rate IS NOT NULL
                    GROUP BY vat_rate
                    ORDER BY vat_rate DESC
                """
                
                result = await self.db.execute(text(sql), {"tenant_id": self.tenant_id})
                rows = result.fetchall()
                
                if rows:
                    answer = "VAT summary:\n"
                    for row in rows:
                        total_vat = row.total_vat or 0
                        total_amount = row.total_amount or 0
                        answer += (
                            f"- {row.vat_rate}%: {row.count} expenses, "
                            f"€{total_vat:.2f} VAT on €{total_amount:.2f}\n"
                        )
                    
                    return {
                        "success": True,
                        "answer": answer,
                        "sql_query": sql,
                        "results": [dict(row._mapping) for row in rows]
                    }
            
            return {"success": False, "error": "Could not generate SQL query"}
            
        except Exception as e:
            logger.error("try_sql_query_error", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _generate_answer_from_rag(
        self,
        question: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> str:
        """Generate answer from retrieved RAG documents"""
        try:
            # Combine retrieved documents
            context = "\n\n".join([
                f"Document: {doc['document_title']}\n{doc['chunk_text']}"
                for doc in retrieved_docs
            ])
            
            # Simple answer generation (can be enhanced with LLM)
            if retrieved_docs:
                top_doc = retrieved_docs[0]
                return f"Based on {top_doc['document_title']}: {top_doc['chunk_text'][:200]}..."
            
            return "I found some relevant information but couldn't generate a complete answer."
            
        except Exception as e:
            logger.error("generate_answer_from_rag_error", error=str(e))
            return "Error generating answer from retrieved documents."
    
    async def _generate_explanation(
        self,
        question: str,
        answer: str,
        sql_results: Optional[List[Dict[str, Any]]] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate LLM explanation for the answer"""
        try:
            if not self.llm_client:
                return "Explanation generation is not available."
            
            # Build explanation prompt
            prompt = f"""
            Question: {question}
            
            Answer: {answer}
            """
            
            if sql_results:
                prompt += f"\n\nSQL Results: {json.dumps(sql_results, indent=2)}"
            
            if retrieved_docs:
                prompt += f"\n\nRelevant Documents: {len(retrieved_docs)} documents retrieved"
            
            prompt += "\n\nPlease provide a clear, concise explanation of this answer in the context of French accounting and expense auditing."
            
            # Generate explanation
            if settings.LLM_PROVIDER == "gemini":
                response = await self.llm_client.generate_content_async(prompt)
                return response.text
            elif settings.LLM_PROVIDER == "openai":
                response = await self.llm_client.chat.completions.create(
                    model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                return response.choices[0].message.content
            
            return "Explanation generation completed."
            
        except Exception as e:
            logger.error("generate_explanation_error", error=str(e))
            return f"Explanation: {answer}"
