"""
Enhanced Notification Service - Main application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import structlog

from common.database import get_db
from .routes import router

logger = structlog.get_logger()

app = FastAPI(
    title="DouCompta - Notification Service",
    description="Enhanced notification engine with rules and in-app delivery",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1/notifications", tags=["notifications"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification"}


@app.get("/health/ready")
async def readiness_check():
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            break
        return {"status": "ready", "service": "notification"}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return {"status": "not_ready", "service": "notification", "error": str(e)}


@app.get("/health/live")
async def liveness_check():
    return {"status": "alive", "service": "notification"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8024)
