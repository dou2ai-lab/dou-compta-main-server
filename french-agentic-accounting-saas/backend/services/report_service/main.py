# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 01-12-2025
# Description: Expense report service main application entry point with FastAPI
# -----------------------------------------------------------------------------

"""
Expense Report Service
Dou Expense & Audit AI – France Edition
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .routes import router

logger = structlog.get_logger()

app = FastAPI(
    title="Dou Expense & Audit AI - Report Service",
    description="Expense report management service",
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

# Include report routes
app.include_router(router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "service": "report"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness probe endpoint"""
    return {"status": "ready", "service": "report"}



























