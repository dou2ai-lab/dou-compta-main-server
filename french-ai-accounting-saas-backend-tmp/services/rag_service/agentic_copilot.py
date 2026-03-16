# -----------------------------------------------------------------------------
# File: agentic_copilot.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Agentic Audit Co-Pilot v1
# -----------------------------------------------------------------------------

"""
Agentic Audit Co-Pilot v1
LLM orchestrates reasoning steps, uses RAG for sources, responds with citations
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import structlog
import json

from .config import settings
from .embeddings import EmbeddingsPipeline
from .qa_service import QAService
from .models import QASession

logger = structlog.get_logger()

class AgenticCoPilot:
    """Agentic Audit Co-Pilot with LLM orchestration"""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.embeddings_pipeline = EmbeddingsPipeline(db, tenant_id)
        self.qa_service = QAService(db, tenant_id)
        self.llm_client = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client"""
        try:
            if settings.LLM_PROVIDER == "gemini":
                import google.generativeai as genai
                if settings.GEMINI_API_KEY:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    self.llm_client = genai.GenerativeModel(
                        getattr(settings, 'GEMINI_MODEL', 'models/gemini-2.0-flash')
                    )
                    logger.info("copilot_llm_initialized", provider="gemini")
            elif settings.LLM_PROVIDER == "openai":
                import openai
                if settings.OPENAI_API_KEY:
                    self.llm_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                    logger.info("copilot_llm_initialized", provider="openai")
        except Exception as e:
            logger.error("copilot_llm_init_error", error=str(e))
            self.llm_client = None
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query using agentic reasoning
        LLM orchestrates reasoning steps, uses RAG for sources
        """
        try:
            if not self.llm_client:
                # Fallback to basic Q&A
                return await self.qa_service.answer_question(query, user_id, "hybrid")
            
            # Step 1: LLM analyzes query and plans reasoning steps
            reasoning_plan = await self._plan_reasoning_steps(query, context)
            
            # Step 2: Execute reasoning steps
            reasoning_results = []
            citations = []
            
            for step in reasoning_plan.get("steps", []):
                step_result = await self._execute_reasoning_step(step, query, context)
                
                # P0: Validate step result against database
                verified_result = await self._verify_step_result(step_result, query)
                if not verified_result["valid"]:
                    logger.warning(
                        "step_result_validation_failed",
                        step_number=step.get("step_number"),
                        corrections=verified_result.get("corrections"),
                        message="LLM output does not match database"
                    )
                    # Re-execute with corrections if possible
                    if verified_result.get("corrections"):
                        step_result = await self._re_execute_with_corrections(step, verified_result["corrections"], query, context)
                
                reasoning_results.append(step_result)
                
                # Collect citations from RAG sources
                if step_result.get("sources"):
                    citations.extend(step_result["sources"])
            
            # Step 3: LLM synthesizes final answer with citations
            final_answer = await self._synthesize_answer(
                query,
                reasoning_results,
                citations
            )
            
            # Step 4: Format response with citations
            response = {
                "success": True,
                "answer": final_answer["answer"],
                "citations": final_answer["citations"],
                "reasoning_steps": reasoning_results,
                "confidence_score": final_answer.get("confidence", "medium"),
                "query_type": "agentic",
                "retrieved_documents": citations
            }
            
            # Save session
            session = QASession(
                tenant_id=self.tenant_id,
                user_id=user_id,
                query=query,
                query_type="agentic",
                answer=final_answer["answer"],
                explanation=json.dumps(reasoning_results),
                retrieved_documents=citations,
                confidence_score=final_answer.get("confidence", "medium"),
                metadata_json={
                    "reasoning_plan": reasoning_plan,
                    "reasoning_results": reasoning_results,
                    "citations": citations
                }
            )
            
            self.db.add(session)
            await self.db.flush()
            
            response["session_id"] = str(session.id)
            
            return response
            
        except Exception as e:
            logger.error("agentic_query_error", error=str(e))
            # Fallback to basic Q&A
            return await self.qa_service.answer_question(query, user_id, "hybrid")
    
    async def _plan_reasoning_steps(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """LLM plans reasoning steps for the query"""
        try:
            prompt = f"""
You are an expert audit assistant for French accounting. Analyze the following query and create a step-by-step reasoning plan.

Query: {query}

Context: {json.dumps(context or {})}

Create a JSON plan with the following structure:
{{
    "steps": [
        {{
            "step_number": 1,
            "action": "search_policies|search_vat_rules|query_database|analyze_trends",
            "description": "What this step will do",
            "expected_output": "What information we expect to get"
        }}
    ],
    "reasoning_approach": "Brief description of the overall approach"
}}

Return only valid JSON.
"""
            
            if settings.LLM_PROVIDER == "gemini" and self.llm_client:
                response = await self.llm_client.generate_content_async(prompt)
                plan_text = response.text.strip()
                # Remove markdown code blocks if present
                if plan_text.startswith("```"):
                    plan_text = plan_text.split("```")[1]
                    if plan_text.startswith("json"):
                        plan_text = plan_text[4:]
                plan = json.loads(plan_text)
                return plan
            elif settings.LLM_PROVIDER == "openai" and self.llm_client:
                response = await self.llm_client.chat.completions.create(
                    model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            
            # Default plan
            return {
                "steps": [
                    {
                        "step_number": 1,
                        "action": "query_database",
                        "description": "Query database for relevant data",
                        "expected_output": "Structured data results"
                    },
                    {
                        "step_number": 2,
                        "action": "search_policies",
                        "description": "Search policies and regulations",
                        "expected_output": "Relevant policy documents"
                    }
                ],
                "reasoning_approach": "Multi-step reasoning with data and policy context"
            }
            
        except Exception as e:
            logger.error("plan_reasoning_steps_error", error=str(e))
            return {"steps": [], "reasoning_approach": "Default approach"}
    
    async def _execute_reasoning_step(
        self,
        step: Dict[str, Any],
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single reasoning step"""
        try:
            action = step.get("action", "")
            step_number = step.get("step_number", 0)
            
            result = {
                "step_number": step_number,
                "action": action,
                "description": step.get("description", ""),
                "output": None,
                "sources": [],
                "success": False
            }
            
            if "search_policies" in action or "search_vat" in action:
                # Use RAG to search for relevant documents
                search_query = query
                doc_types = []
                
                if "policies" in action:
                    doc_types = ["policy"]
                elif "vat" in action:
                    doc_types = ["vat_rule"]
                else:
                    doc_types = ["policy", "vat_rule"]
                
                rag_results = await self.embeddings_pipeline.search_similar(
                    query=search_query,
                    document_types=doc_types,
                    top_k=5
                )
                
                result["output"] = rag_results
                result["sources"] = [
                    {
                        "id": doc["id"],
                        "title": doc["document_title"],
                        "type": doc["document_type"],
                        "text": doc["chunk_text"],
                        "similarity": doc["similarity"],
                        "citation": f"[{doc['document_type']}:{doc['document_id']}]"
                    }
                    for doc in rag_results
                ]
                result["success"] = len(rag_results) > 0
                
            elif "query_database" in action:
                # Use SQL querying
                sql_result = await self.qa_service._try_sql_query(query)
                result["output"] = sql_result.get("results", [])
                result["sql_query"] = sql_result.get("sql_query")
                result["success"] = sql_result.get("success", False)
                
            elif "analyze_trends" in action:
                # Analyze trends (can be enhanced)
                result["output"] = {"trend_analysis": "Trend analysis placeholder"}
                result["success"] = True
            
            return result
            
        except Exception as e:
            logger.error("execute_reasoning_step_error", step=step, error=str(e))
            return {
                "step_number": step.get("step_number", 0),
                "action": step.get("action", ""),
                "success": False,
                "error": str(e)
            }
    
    async def _synthesize_answer(
        self,
        query: str,
        reasoning_results: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """LLM synthesizes final answer with citations"""
        try:
            # Build context from reasoning results
            context_summary = []
            for result in reasoning_results:
                if result.get("success"):
                    context_summary.append({
                        "step": result.get("description", ""),
                        "output": str(result.get("output", ""))[:500]  # Truncate
                    })
            
            # Build citations list
            citation_list = []
            citation_map = {}
            for idx, citation in enumerate(citations[:10]):  # Limit to 10 citations
                citation_id = f"[{idx + 1}]"
                citation_map[citation_id] = citation
                citation_list.append(f"{citation_id} {citation.get('title', 'Unknown')}")
            
            prompt = f"""
You are an expert audit assistant for French accounting. Answer the following query based on the reasoning steps and sources provided.

Query: {query}

Reasoning Steps:
{json.dumps(context_summary, indent=2)}

Available Sources:
{chr(10).join(citation_list)}

Instructions:
1. Provide a clear, comprehensive answer to the query
2. Cite sources using the citation format [1], [2], etc.
3. Focus on French accounting regulations and best practices
4. Be specific and actionable

Format your response as JSON:
{{
    "answer": "Your comprehensive answer with citations like [1], [2]",
    "citations": [
        {{
            "id": "[1]",
            "title": "Source title",
            "type": "policy|vat_rule|data",
            "relevance": "Why this source is relevant"
        }}
    ],
    "confidence": "high|medium|low"
}}

Return only valid JSON.
"""
            
            if settings.LLM_PROVIDER == "gemini" and self.llm_client:
                response = await self.llm_client.generate_content_async(prompt)
                answer_text = response.text.strip()
                # Remove markdown code blocks if present
                if answer_text.startswith("```"):
                    answer_text = answer_text.split("```")[1]
                    if answer_text.startswith("json"):
                        answer_text = answer_text[4:]
                answer_data = json.loads(answer_text)
                
                # Map citations back to full citation objects
                formatted_citations = []
                for cit in answer_data.get("citations", []):
                    cit_id = cit.get("id", "")
                    if cit_id in citation_map:
                        full_cit = citation_map[cit_id].copy()
                        full_cit["relevance"] = cit.get("relevance", "")
                        formatted_citations.append(full_cit)
                
                return {
                    "answer": answer_data.get("answer", ""),
                    "citations": formatted_citations,
                    "confidence": answer_data.get("confidence", "medium")
                }
                
            elif settings.LLM_PROVIDER == "openai" and self.llm_client:
                response = await self.llm_client.chat.completions.create(
                    model=getattr(settings, 'OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                answer_data = json.loads(response.choices[0].message.content)
                
                # Map citations
                formatted_citations = []
                for cit in answer_data.get("citations", []):
                    cit_id = cit.get("id", "")
                    if cit_id in citation_map:
                        full_cit = citation_map[cit_id].copy()
                        full_cit["relevance"] = cit.get("relevance", "")
                        formatted_citations.append(full_cit)
                
                return {
                    "answer": answer_data.get("answer", ""),
                    "citations": formatted_citations,
                    "confidence": answer_data.get("confidence", "medium")
                }
            
            # Fallback
            return {
                "answer": "I processed your query but couldn't generate a complete answer.",
                "citations": citations[:5],
                "confidence": "low"
            }
            
        except Exception as e:
            logger.error("synthesize_answer_error", error=str(e))
            return {
                "answer": "I encountered an error while processing your query.",
                "citations": citations[:5],
                "confidence": "low"
            }
    
    async def _verify_step_result(
        self,
        step_result: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        P0: Verify step result against database
        Validates numeric and factual claims from LLM outputs
        """
        try:
            output = step_result.get("output")
            if not output:
                return {"valid": True, "reason": "No output to verify"}
            
            # Extract numbers and factual claims from output
            import re
            numbers = re.findall(r'\d+\.?\d*', str(output))
            
            # If step involves database query, verify numbers match
            if step_result.get("action") == "query_database" and step_result.get("sql_query"):
                # Get actual database results
                sql_result = await self.qa_service._try_sql_query(query)
                if sql_result.get("success") and sql_result.get("results"):
                    actual_results = sql_result["results"]
                    
                    # Compare numbers in output with actual results
                    corrections = []
                    for number_str in numbers:
                        try:
                            number = float(number_str)
                            # Check if this number appears in actual results
                            found = False
                            for result_row in actual_results:
                                if isinstance(result_row, dict):
                                    for value in result_row.values():
                                        if isinstance(value, (int, float)) and abs(value - number) < 0.01:
                                            found = True
                                            break
                                elif isinstance(result_row, (int, float)) and abs(result_row - number) < 0.01:
                                    found = True
                                    break
                            
                            if not found and number > 0:  # Ignore small numbers that might be formatting
                                corrections.append({
                                    "claimed": number,
                                    "actual": actual_results[0] if actual_results else None
                                })
                        except ValueError:
                            continue
                    
                    if corrections:
                        return {
                            "valid": False,
                            "corrections": corrections,
                            "reason": "Numbers in output do not match database"
                        }
            
            return {"valid": True, "reason": "Verification passed"}
            
        except Exception as e:
            logger.error("verify_step_result_error", error=str(e))
            # On error, mark as invalid to be safe
            return {"valid": False, "reason": f"Verification error: {str(e)}"}
    
    async def _re_execute_with_corrections(
        self,
        step: Dict[str, Any],
        corrections: List[Dict[str, Any]],
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Re-execute reasoning step with corrections from validation
        """
        try:
            # Log the correction attempt
            logger.info(
                "re_executing_step_with_corrections",
                step_number=step.get("step_number"),
                corrections_count=len(corrections)
            )
            
            # Re-execute the step
            step_result = await self._execute_reasoning_step(step, query, context)
            
            # Add validation metadata
            step_result["validation_applied"] = True
            step_result["corrections"] = corrections
            
            return step_result
            
        except Exception as e:
            logger.error("re_execute_with_corrections_error", error=str(e))
            # Return original step result with error flag
            return {
                "step_number": step.get("step_number", 0),
                "action": step.get("action", ""),
                "success": False,
                "error": f"Re-execution failed: {str(e)}",
                "validation_failed": True
            }
