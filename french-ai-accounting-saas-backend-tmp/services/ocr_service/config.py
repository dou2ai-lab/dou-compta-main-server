# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Configuration settings for OCR service including provider settings and processing parameters
# -----------------------------------------------------------------------------

"""
Configuration for OCR Service
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "ocr-service"
    ENVIRONMENT: str = "development"
    
    # Database
    # Default matches docker-compose.yml (host port 5433, password dou_password123)
    DATABASE_URL: str = Field(default="postgresql://dou_user:dou_password123@localhost:5433/dou_expense_audit")
    
    # OCR Provider (paddle | tesseract | google_document_ai | azure_form_recognizer)
    OCR_PROVIDER: str = "paddle"
    GOOGLE_PROJECT_ID: str = ""
    GOOGLE_LOCATION: str = "eu"  # EU region required
    GOOGLE_PROCESSOR_ID: str = ""
    GOOGLE_CREDENTIALS_PATH: str = ""
    
    AZURE_ENDPOINT: str = ""
    AZURE_KEY: str = ""
    AZURE_REGION: str = "westeurope"  # EU region required
    
    # Message Queue
    MESSAGE_QUEUE_PROVIDER: str = "rabbitmq"
    MESSAGE_QUEUE_URL: str = ""  # Will be read from env
    RABBITMQ_URL: str = ""  # Alternative env var name
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    CONSUMER_GROUP: str = "ocr-service-group"
    
    # Processing
    OCR_TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: int = 1  # seconds

    # Development behavior
    # If True, OCR errors will be recorded but the receipt will still be marked
    # as completed so the UI can proceed and the user can manually adjust fields.
    OCR_FAIL_OPEN: bool = Field(default=True)
    
    # Object Storage (for downloading files)
    STORAGE_PROVIDER: str = "s3"
    STORAGE_BUCKET: str = ""
    STORAGE_REGION: str = "eu-west-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()









