# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Administration service main application entry point with FastAPI
# -----------------------------------------------------------------------------

"""
Admin Service - Phase 1 Skeleton
Dou Expense & Audit AI – France Edition
"""
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .routes import router

# Explicit origins so credentials work (browsers reject "*" with credentials)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app = FastAPI(
    title="Dou Expense & Audit AI - Admin Service",
    description="Administration service for Dou Expense & Audit AI platform",
    version="1.0.0"
)

# CORS middleware – must allow frontend origin when using credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler so 4xx/5xx responses always include CORS headers
def _cors_headers(origin: Optional[str] = None):
    h = {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }
    if origin and origin in CORS_ORIGINS:
        h["Access-Control-Allow-Origin"] = origin
    else:
        h["Access-Control-Allow-Origin"] = CORS_ORIGINS[0]
    return h

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    origin = request.headers.get("origin")
    content = {"detail": exc.detail} if isinstance(exc.detail, (str, type(None))) else {"detail": exc.detail}
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=_cors_headers(origin),
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)},
        headers=_cors_headers(origin),
    )

# Include admin routes
app.include_router(router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "admin"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    # TODO: Check database connection, dependencies
    return {"status": "ready", "service": "admin"}

@app.get("/health/live")
async def liveness_check():
    """Liveness probe endpoint"""
    return {"status": "alive", "service": "admin"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)









