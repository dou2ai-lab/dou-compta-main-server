# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Anomaly Detection Service main application entry point
# -----------------------------------------------------------------------------

"""
Anomaly Detection Service - Phase 13 & 14
Dou Expense & Audit AI – France Edition
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import structlog

from common.database import get_db
from .routes import router
from .config import settings

logger = structlog.get_logger()

app = FastAPI(
    title="Dou Expense & Audit AI - Anomaly Detection Service",
    description="Anomaly detection, risk scoring, and finance dashboard service",
    version="13.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1/anomaly", tags=["anomaly-detection"])

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "anomaly-detection"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            break
        return {"status": "ready", "service": "anomaly-detection"}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return {"status": "not_ready", "service": "anomaly-detection", "error": str(e)}

@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive", "service": "anomaly-detection"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




