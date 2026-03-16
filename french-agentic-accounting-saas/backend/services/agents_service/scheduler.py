"""Agent Scheduler - Manages periodic agent execution."""
import structlog
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field

logger = structlog.get_logger()


@dataclass
class ScheduledTask:
    agent_code: str
    name: str
    cron_expression: str
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0


class AgentScheduler:
    """Simple in-memory scheduler for agent tasks."""

    def __init__(self):
        self.tasks: dict[str, ScheduledTask] = {}
        self._setup_default_tasks()

    def _setup_default_tasks(self):
        defaults = [
            ScheduledTask(agent_code="RELANCA", name="Relance documents manquants", cron_expression="0 9 * * 1-5"),
            ScheduledTask(agent_code="A2A_FISCAL", name="Surveillance echeances fiscales", cron_expression="0 8 * * *"),
            ScheduledTask(agent_code="A2A_BANK", name="Synchronisation bancaire", cron_expression="0 */4 * * *"),
            ScheduledTask(agent_code="COMPTAA", name="Generation ecritures auto", cron_expression="0 22 * * *"),
            ScheduledTask(agent_code="BANKA", name="Rapprochement bancaire auto", cron_expression="0 6 * * *"),
        ]
        for task in defaults:
            self.tasks[task.agent_code] = task

    def list_tasks(self) -> list[dict]:
        return [
            {
                "agent_code": t.agent_code,
                "name": t.name,
                "cron_expression": t.cron_expression,
                "is_active": t.is_active,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "run_count": t.run_count,
                "error_count": t.error_count,
            }
            for t in self.tasks.values()
        ]

    def toggle_task(self, agent_code: str) -> Optional[dict]:
        task = self.tasks.get(agent_code)
        if not task:
            return None
        task.is_active = not task.is_active
        return {"agent_code": task.agent_code, "is_active": task.is_active}

    def record_run(self, agent_code: str, success: bool):
        task = self.tasks.get(agent_code)
        if task:
            task.last_run = datetime.now(timezone.utc)
            task.run_count += 1
            if not success:
                task.error_count += 1


# Singleton
scheduler = AgentScheduler()
