# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Performance service main application
# -----------------------------------------------------------------------------

"""
Performance Service
Handles performance optimizations including caching and OCR batching
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from services.performance.cache_service import CacheService
from services.performance.ocr_batcher import OCRBatcher

logger = structlog.get_logger()

app = FastAPI(
    title="Performance Service",
    description="Performance optimization service for caching and OCR batching",
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

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("performance_service_starting")
    # Cache service will be initialized per-request
    # OCR batcher will be initialized per-request

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "performance"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Performance Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "cache": "/api/v1/performance/cache",
            "ocr": "/api/v1/performance/ocr"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




