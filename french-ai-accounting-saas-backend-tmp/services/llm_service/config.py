# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Configuration settings for LLM service including provider settings and processing parameters
# -----------------------------------------------------------------------------

"""
Configuration for LLM Service
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "llm-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # LLM Provider
    LLM_PROVIDER: str = "gemini"  # gemini, openai, anthropic, local
    GEMINI_API_KEY: str = ""  # Get from https://aistudio.google.com/app/apikey
    GEMINI_MODEL: str = "models/gemini-2.0-flash"  # Current stable model (v1beta API)
    
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_BASE_URL: str = ""  # For Azure OpenAI EU endpoints
    OPENAI_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TIMEOUT: int = 30
    
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    ANTHROPIC_TIMEOUT: int = 30
    
    # Message Queue
    MESSAGE_QUEUE_PROVIDER: str = "rabbitmq"  # rabbitmq, kafka
    MESSAGE_QUEUE_URL: str = "amqp://localhost:5672"
    
    # Task Queue (for future Celery integration)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # Processing
    LLM_CONFIDENCE_THRESHOLD: float = 0.7
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: int = 1
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()









