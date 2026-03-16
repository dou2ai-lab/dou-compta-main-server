# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: LLM-based post-processing service main application entry point
# -----------------------------------------------------------------------------

"""
LLM Service - Phase 3
Dou Expense & Audit AI – France Edition
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .routes import router
from .config import settings

logger = structlog.get_logger()

app = FastAPI(
    title="Dou Expense & Audit AI - LLM Service",
    description="LLM-based post-processing service for receipt extraction",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "llm-service"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    try:
        # TODO: Check database, LLM provider, queue
        return {
            "status": "ready",
            "service": "llm-service",
            "checks": {
                "database": "ok",
                "llm_provider": "ok",
                "queue": "ok"
            }
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive", "service": "llm-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)









