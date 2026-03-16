"""RELANCA Agent - Missing document chasing with escalation."""
import structlog
from datetime import date, timedelta
from common.agent_base import AgentBase, AgentResult, AgentStatus

logger = structlog.get_logger()

ESCALATION_SCHEDULE = [
    {"days": 3, "level": 1, "action": "email_reminder"},
    {"days": 7, "level": 2, "action": "email_urgent"},
    {"days": 14, "level": 3, "action": "email_manager"},
    {"days": 21, "level": 4, "action": "email_final_notice"},
]


class RELANCAAgent(AgentBase):
    """RELANCA - Autonomous document chasing agent."""
    agent_code = "RELANCA"
    agent_name = "Agent de Relance"

    async def run(self, context: dict, result: AgentResult) -> dict:
        tenant_id = context["tenant_id"]
        result.add_log("Checking for missing documents")

        # In production, this would query expenses without receipts,
        # declarations without supporting docs, etc.
        missing_docs = context.get("missing_documents", [])
        actions_taken = []

        for doc in missing_docs:
            days_missing = (date.today() - date.fromisoformat(doc.get("due_date", str(date.today())))).days
            escalation = None
            for esc in ESCALATION_SCHEDULE:
                if days_missing >= esc["days"]:
                    escalation = esc

            if escalation:
                actions_taken.append({
                    "document": doc.get("title", "Unknown"),
                    "days_missing": days_missing,
                    "escalation_level": escalation["level"],
                    "action": escalation["action"],
                })
                result.add_log(f"Escalation L{escalation['level']} for {doc.get('title')}")

        result.confidence = 0.9
        return {
            "documents_checked": len(missing_docs),
            "actions_taken": len(actions_taken),
            "details": actions_taken,
        }
