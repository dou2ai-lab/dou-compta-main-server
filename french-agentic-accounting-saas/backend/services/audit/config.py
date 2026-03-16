# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Configuration for audit service
# -----------------------------------------------------------------------------

"""
Configuration for Audit Service
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "audit-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # LLM Provider (for narrative generation)
    LLM_PROVIDER: str = "gemini"  # gemini, openai, anthropic
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "models/gemini-2.0-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()




