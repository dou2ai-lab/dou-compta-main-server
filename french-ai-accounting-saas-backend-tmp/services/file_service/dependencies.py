# -----------------------------------------------------------------------------
# File: dependencies.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: FastAPI dependencies for file service including service injection and authentication
# -----------------------------------------------------------------------------

"""
Dependencies for File Service
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .service import FileService
from .storage import StorageService
from .encryption import EncryptionService
from .events import EventPublisher
from common.database import get_db
from services.auth.dependencies import get_current_user as get_auth_user

def get_file_service(db: AsyncSession = Depends(get_db)) -> FileService:
    """Dependency for FileService"""
    storage = StorageService()
    encryption = EncryptionService()
    events = EventPublisher()
    return FileService(db, storage, encryption, events)

def get_current_user():
    """Dependency for current authenticated user"""
    return get_auth_user









