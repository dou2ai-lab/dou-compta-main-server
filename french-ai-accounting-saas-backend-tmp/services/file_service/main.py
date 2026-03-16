# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: File upload and management service main application entry point
# -----------------------------------------------------------------------------

"""
File Service - Phase 2
Dou Expense & Audit AI – France Edition
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
import traceback

from .routes import router
from .config import settings

logger = structlog.get_logger()

app = FastAPI(
    title="Dou Expense & Audit AI - File Service",
    description="File upload and management service",
    version="2.0.0"
)

# Global exception handler to catch all unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return detailed error message"""
    error_traceback = traceback.format_exc()
    
    # Print to console for immediate visibility
    print("=" * 80)
    print("GLOBAL EXCEPTION HANDLER TRIGGERED")
    print(f"Path: {request.url}")
    print(f"Method: {request.method}")
    print(f"Error Type: {type(exc).__name__}")
    print(f"Error Message: {str(exc)}")
    print(f"Full Traceback:\n{error_traceback}")
    print("=" * 80)
    
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=str(request.url),
        method=request.method,
        traceback=error_traceback
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "error_type": type(exc).__name__,
            "path": str(request.url),
            "method": request.method
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning("validation_error", errors=exc.errors(), path=str(request.url))
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body}
    )

# CORS middleware
# Be very permissive in development so frontend at http://localhost:3000 can call this service.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1")

# Test endpoint to verify service is running
@app.get("/api/v1/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"status": "ok", "service": "file-service", "message": "Service is running"}

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "file-service"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    # TODO: Check database connection, object storage, message queue
    try:
        # Add actual health checks here
        return {
            "status": "ready",
            "service": "file-service",
            "checks": {
                "database": "ok",
                "storage": "ok",
                "message_queue": "ok"
            }
        }
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive", "service": "file-service"}

@app.post("/api/v1/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Simple test endpoint to verify upload works"""
    try:
        content = await file.read()
        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "message": "File received successfully"
        }
    except Exception as e:
        logger.error("test_upload_failed", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)









