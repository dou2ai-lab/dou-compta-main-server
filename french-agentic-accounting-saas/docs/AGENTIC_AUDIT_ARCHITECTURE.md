# Agentic Audit & Compliance Module – Architecture

## Repo Summary

| Aspect | Stack |
|--------|--------|
| **Backend** | Python 3.11, FastAPI, uvicorn; multiple services (auth, expense, audit, anomaly, rag, report, admin, file) |
| **DB** | PostgreSQL 14 + pgvector; async SQLAlchemy (asyncpg) |
| **Migrations** | SQL files in `backend/migrations/versions/`; `scripts/run_all_migrations.py` (schema_migrations table) |
| **Docker** | `infrastructure/docker-compose.yml` – postgres, auth, file-service, expense, report-service, admin, audit (no Redis/Kafka) |
| **Scheduling** | None currently – add in-process APScheduler in audit or a dedicated small job runner |
| **LLM** | Gemini / OpenAI; used in narrative_generator (audit), RAG agentic_copilot, llm_service |

## Existing Pieces Reused

- **Audit**: `AuditReport`, `AuditEvidence`, `AuditMetadata`, `AuditTrail`, `AuditSnapshot`; report_generator, narrative_generator, evidence_collector; ZIP download + SHA-256 hash in metadata.
- **Anomaly**: `AnomalyDetector` (Isolation Forest), `RiskScorer`; no persistence of risk_score_line / is_anomaly / anomaly_reasons on expenses yet.
- **RAG**: `document_embeddings` (pgvector), `qa_sessions`; `EmbeddingsPipeline`, `QAService`, `AgenticCoPilot`; no `knowledge_documents` table yet.
- **Frontend**: Audit reports list/detail, generate, narrative page; audit-copilot page (mock chat). Anomaly dashboard exists.

## Architecture Plan

1. **DB migrations (016_agentic_audit_compliance.sql)**  
   - Expenses: add `risk_score_line`, `is_anomaly`, `anomaly_reasons` (JSONB).  
   - `risk_scores` table: (tenant_id, entity_type, entity_id, risk_score, updated_at) for employee/merchant (and optional line-level snapshot).  
   - `knowledge_documents`: id, title, source_url, type, language, content, created_at (raw ingested content).  
   - Optional: `audit_report_narratives` if we want separate storage; else keep using `audit_reports.narrative_sections` JSONB.

2. **Continuous monitoring (5.2.1)**  
   - Lightweight scheduler (APScheduler) in audit service or a small `jobs` module: daily/weekly job.  
   - Job: profile spend by employee, cost_center (if present), merchant, category, period, VAT treatment; compute/update risk_scores for each expense line, employee, merchant via existing anomaly + risk_scorer; write back to DB (expenses + risk_scores).

3. **Anomaly detection (5.2.2)**  
   - Keep Isolation Forest in anomaly_service; add deterministic rules: e.g. MISSING_VAT, NEAR_APPROVAL_LIMIT, MISSING_RECEIPT, WEEKEND, LATE_NIGHT, END_OF_MONTH_CLUSTER, RECURRING_JUST_UNDER_LIMIT.  
   - Persist to expenses: risk_score_line, is_anomaly, anomaly_reasons; and to risk_scores for employee/merchant.

4. **Audit report generation (5.2.3)**  
   - Report generator: already has spend summary, policy violations, VAT summary; add executive summary, top risk employees/merchants with explanations.  
   - Narrative generator: already produces FR/EN sections; store in `audit_reports.narrative_sections`; optional audit_report_narratives table for versioning.  
   - LLM: no direct DB write; log generations for audit trail.

5. **Evidence pack (5.2.4)**  
   - Sampling: random + risk-based (top high-risk lines, employees, merchants).  
   - Include receipts, invoices, justifications; full audit trail with “who submitted/approved/modified”; use `SYSTEM_AUTO_RULE_ENGINE` for auto-approved steps.  
   - Export: existing ZIP + SHA-256 in DB; add optional password-based encryption (e.g. pyminizip or stdlib zip with password).  
   - Secure portal endpoint: signed URLs or short-lived token for external auditors (reuse existing signed-url pattern).

6. **Knowledge ingestion + RAG (5.2.5 prep)**  
   - Script: fetch 4 canonical URLs (URSSAF, Vanta GDPR, Cyplom VAT, Appvizer note de frais); clean & chunk; insert into `knowledge_documents`; then embed into `document_embeddings` (existing pipeline).  
   - Run offline/periodically; no live HTTP at inference.

7. **Audit Co-Pilot (5.2.5)**  
   - DB questions: intent parsing → safe parameterized SQL/ORM only (no raw prompt-to-SQL); return tabular data + LLM explanation.  
   - Policy/URSSAF/VAT/GDPR: RAG over document_embeddings (and knowledge_documents if needed).  
   - Existing `/api/v1/rag/copilot`; add role checks (Auditor, Compliance, Admin); log queries/responses.  
   - Frontend: replace mock chat with real API call to RAG copilot; show citations.

8. **Frontend**  
   - Audit & Compliance section: risk dashboards (employees, merchants, categories), audit report list/detail with narratives, evidence pack download (and optional encrypted), Co-Pilot chat UI wired to backend.

## Implementation Order

1. DB migrations (016)  
2. Backend: monitoring job + anomaly persistence (rules + ML)  
3. Audit report: executive summary, top risks, narratives (FR+EN)  
4. Evidence pack: sampling, encryption option, SYSTEM_AUTO_RULE_ENGINE  
5. Knowledge ingestion script + RAG retrieval from knowledge_documents  
6. Co-Pilot: safe query layer + chat endpoint + logging  
7. Frontend: risk views, report narratives, evidence download, real chat
