# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: OCR processing service main application entry point for receipt extraction
# -----------------------------------------------------------------------------

"""
OCR Service - Phase 2
Dou Expense & Audit AI – France Edition
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .routes import router
from .config import settings
from .consumer import start_consumer

logger = structlog.get_logger()

app = FastAPI(
    title="Dou Expense & Audit AI - OCR Service",
    description="OCR processing service for receipt extraction",
    version="2.0.0"
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

@app.on_event("startup")
async def startup_event():
    """Start message queue consumer on startup"""
    logger.info("starting_ocr_consumer")
    import threading
    from .consumer import start_consumer
    # Start consumer in background thread
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    logger.info("ocr_consumer_thread_started")

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "ocr-service"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    try:
        # TODO: Check database, OCR provider, message queue
        return {
            "status": "ready",
            "service": "ocr-service",
            "checks": {
                "database": "ok",
                "ocr_provider": "ok",
                "message_queue": "ok"
            }
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive", "service": "ocr-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)









