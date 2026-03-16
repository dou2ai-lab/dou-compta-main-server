"""
Agent Base Framework for DouCompta AI Agents.
All agents (COMPTAA, BANKA, FISCA, etc.) inherit from AgentBase.
"""
import uuid
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = structlog.get_logger()


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class AgentResult:
    agent_code: str
    status: AgentStatus
    data: Any = None
    error: Optional[str] = None
    confidence: float = 1.0
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    audit_log: list = field(default_factory=list)

    def add_log(self, message: str, level: str = "info"):
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        })

    def to_dict(self) -> dict:
        return {
            "agent_code": self.agent_code,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "confidence": self.confidence,
            "execution_id": self.execution_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
            "audit_log": self.audit_log,
        }


class AgentBase:
    """Base class for all DouCompta AI agents."""

    agent_code: str = "UNKNOWN"
    agent_name: str = "Unknown Agent"
    max_retries: int = 3

    async def execute(self, context: dict) -> AgentResult:
        result = AgentResult(
            agent_code=self.agent_code,
            status=AgentStatus.PENDING,
            started_at=datetime.utcnow(),
        )
        result.add_log(f"Agent {self.agent_code} started")

        for attempt in range(self.max_retries + 1):
            try:
                result.status = AgentStatus.RUNNING
                result.retry_count = attempt
                data = await self.run(context, result)
                result.data = data
                result.status = AgentStatus.SUCCESS
                result.completed_at = datetime.utcnow()
                result.add_log(f"Agent {self.agent_code} completed successfully")

                if not await self.validate(result):
                    result.status = AgentStatus.FAILED
                    result.add_log("Validation failed", level="error")

                return result

            except Exception as e:
                result.add_log(f"Attempt {attempt + 1} failed: {str(e)}", level="error")
                logger.error(
                    "agent_execution_failed",
                    agent=self.agent_code,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt == self.max_retries:
                    result.status = AgentStatus.FAILED
                    result.error = str(e)
                    result.completed_at = datetime.utcnow()
                    return result

        return result

    async def run(self, context: dict, result: AgentResult) -> Any:
        raise NotImplementedError("Agents must implement run()")

    async def validate(self, result: AgentResult) -> bool:
        return result.status == AgentStatus.SUCCESS
