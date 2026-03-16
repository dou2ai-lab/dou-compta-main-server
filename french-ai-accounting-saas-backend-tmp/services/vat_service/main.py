# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: VAT service main application
# -----------------------------------------------------------------------------

"""
VAT Service Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .routes import router
from .config import settings

logger = structlog.get_logger()

app = FastAPI(
    title="VAT Service",
    description="VAT rules engine service for automatic VAT rate determination",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router, prefix="/api/v1/vat", tags=["vat"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "vat-service"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {"status": "ready", "service": "vat-service"}


@app.get("/health/live")
async def liveness_check():
    """Liveness check endpoint"""
    return {"status": "alive", "service": "vat-service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8017)

