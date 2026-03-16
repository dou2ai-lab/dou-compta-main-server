# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Authentication service main application entry point with FastAPI
# -----------------------------------------------------------------------------

"""
Authentication Service
Dou Expense & Audit AI – France Edition
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import traceback

from common.database import get_db
from .routes import router

logger = structlog.get_logger()

app = FastAPI(
    title="Dou Expense & Audit AI - Auth Service",
    description="Authentication service for Dou Expense & Audit AI platform",
    version="1.0.0"
)

# CORS middleware - MUST be added before exception handlers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler to ensure CORS headers are always included
# Note: HTTPException and RequestValidationError are handled by FastAPI automatically
from fastapi import HTTPException as FastAPIHTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler that ensures CORS headers are included for unhandled exceptions"""
    # Don't handle HTTPException or RequestValidationError - let FastAPI handle them
    # They already include CORS headers via middleware
    if isinstance(exc, (FastAPIHTTPException, RequestValidationError)):
        raise exc
    
    # Log the exception
    try:
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=str(request.url.path),
            method=request.method,
            traceback=traceback.format_exc()
        )
    except Exception:
        # If logging fails, just continue
        pass
    
    # Return JSON response with CORS headers
    import os
    is_dev = os.getenv("ENVIRONMENT", "development") == "development"
    
    try:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error": str(exc) if is_dev else "An error occurred"
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception:
        # If even returning a response fails, re-raise the original exception
        raise exc

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Validation exception handler with CORS headers"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Include authentication routes
app.include_router(router, prefix="/api/v1/auth", tags=["authentication"])

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "auth"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    try:
        # Check database connection
        from sqlalchemy import text
        async for db in get_db():
            await db.execute(text("SELECT 1"))
            break
        return {"status": "ready", "service": "auth"}
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return {"status": "not_ready", "service": "auth", "error": str(e)}

@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive", "service": "auth"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)









