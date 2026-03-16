# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Monitoring service main application
# -----------------------------------------------------------------------------

"""
Monitoring Service
Production monitoring, SLOs, and alerting
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .routes import router

logger = structlog.get_logger()

app = FastAPI(
    title="Monitoring Service",
    description="Production monitoring, SLOs, and alerting service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("monitoring_service_starting")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {"status": "healthy", "service": "monitoring"}
    except Exception as e:
        logger.error("health_check_error", error=str(e))
        return {"status": "unhealthy", "service": "monitoring", "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Monitoring Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "metrics": "/api/v1/monitoring/metrics",
            "slos": "/api/v1/monitoring/slos",
            "alerts": "/api/v1/monitoring/alerts"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




