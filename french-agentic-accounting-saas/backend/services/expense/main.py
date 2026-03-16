# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Expense management service main application entry point with FastAPI
# -----------------------------------------------------------------------------

"""
Expense Service
Dou Expense & Audit AI – France Edition
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import structlog

from common.database import get_db
from .routes import router

logger = structlog.get_logger()

app = FastAPI(
    title="Dou Expense & Audit AI - Expense Service",
    description="Expense management service for Dou Expense & Audit AI platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include expense routes
app.include_router(router, prefix="/api/v1/expenses", tags=["expenses"])

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "expense"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            break
        return {"status": "ready", "service": "expense"}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return {"status": "not_ready", "service": "expense", "error": str(e)}

@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive", "service": "expense"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)









