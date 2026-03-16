"""Agents Service API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .scheduler import scheduler

logger = structlog.get_logger()
router = APIRouter()

@router.get("/tasks")
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all scheduled agent tasks."""
    return scheduler.list_tasks()

@router.post("/tasks/{agent_code}/toggle")
async def toggle_task(
    agent_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Enable/disable a scheduled task."""
    result = scheduler.toggle_task(agent_code)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent non trouve")
    return result

@router.get("/status")
async def agent_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overall agent system status."""
    tasks = scheduler.list_tasks()
    active = sum(1 for t in tasks if t["is_active"])
    total_runs = sum(t["run_count"] for t in tasks)
    total_errors = sum(t["error_count"] for t in tasks)
    return {
        "total_agents": len(tasks),
        "active_agents": active,
        "total_runs": total_runs,
        "total_errors": total_errors,
        "error_rate": round(total_errors / max(total_runs, 1) * 100, 1),
    }
