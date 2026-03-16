"""Collection Service API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import structlog
from common.database import get_db
from common.models import User
from services.auth.dependencies import get_current_user
from .classifier import classify_document

logger = structlog.get_logger()
router = APIRouter()

class ClassifyRequest(BaseModel):
    text_content: str
    filename: Optional[str] = None

class ClassifyResponse(BaseModel):
    document_type: str
    confidence: float
    route: Optional[str] = None
    alternatives: list = []

@router.post("/classify", response_model=ClassifyResponse)
async def classify(
    payload: ClassifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Classify a document and suggest routing."""
    result = classify_document(payload.text_content, payload.filename)
    return ClassifyResponse(**result)

@router.get("/document-types")
async def list_document_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List supported document types."""
    from .classifier import DOCUMENT_TYPES
    return [{"type": k, "route": v["route"], "keywords": v["keywords"]} for k, v in DOCUMENT_TYPES.items()]
