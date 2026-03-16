# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: RAG service main application
# -----------------------------------------------------------------------------

"""
RAG Service Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import router
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title="RAG Service",
    description="RAG Service for Audit Q&A",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if hasattr(settings, 'CORS_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1/rag", tags=["rag"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rag-service"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "service": "rag-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)




