# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: Configuration for URSSAF service
# -----------------------------------------------------------------------------

"""
Configuration for URSSAF Service
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "urssaf-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()

