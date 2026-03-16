# -----------------------------------------------------------------------------
# File: main.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: GDPR service main application
# -----------------------------------------------------------------------------

"""
GDPR Service Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title="GDPR Service",
    description="GDPR Compliance Service",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://127.0.0.1:3000"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1/gdpr", tags=["gdpr"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "gdpr-service"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "service": "gdpr-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)




