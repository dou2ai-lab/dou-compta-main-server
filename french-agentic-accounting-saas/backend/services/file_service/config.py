# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Configuration settings for file service including storage, encryption, and upload limits
# -----------------------------------------------------------------------------

"""
Configuration for File Service
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "file-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = Field(default="postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
    
    # Object Storage
    STORAGE_PROVIDER: str = Field(default="s3")  # s3, gcs, azure
    STORAGE_BUCKET: str = Field(default="dou-receipts-dev")  # Default bucket for development
    STORAGE_REGION: str = Field(default="eu-west-1")  # EU region required
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    
    # Encryption
    # For local development we disable encryption by default to avoid requiring
    # ENCRYPTION_MASTER_KEY / KMS setup. In production, override this via env.
    ENCRYPTION_ENABLED: bool = Field(default=False)
    KMS_KEY_ID: str = Field(default="")  # KMS key ID for encryption
    
    # Message Queue
    MESSAGE_QUEUE_PROVIDER: str = Field(default="rabbitmq")  # kafka, rabbitmq
    MESSAGE_QUEUE_URL: str = Field(default="")  # Will be read from env
    RABBITMQ_URL: str = Field(default="")  # Alternative env var name
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092")
    
    # File Upload Limits
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    ALLOWED_MIME_TYPES: List[str] = Field(default=[
        "image/jpeg",
        "image/png",
        "image/heic",
        "application/pdf"
    ])
    
    # Signed URLs
    SIGNED_URL_EXPIRATION: int = Field(default=3600)  # 1 hour in seconds
    MAX_SIGNED_URL_EXPIRATION: int = Field(default=86400)  # 24 hours
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

# Initialize settings with error handling
try:
    settings = Settings()
except Exception as e:
    import os
    # Fallback to environment variable or default
    default_db_url = os.getenv("DATABASE_URL", "postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
    settings = Settings(DATABASE_URL=default_db_url)









