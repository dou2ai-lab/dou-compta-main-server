# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Configuration for GDPR service
# -----------------------------------------------------------------------------

"""
Configuration for GDPR Compliance Service
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "gdpr-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # Retention Rules
    ACCOUNTING_RETENTION_YEARS: int = 10  # 10-year retention for accounting data
    PERSONAL_DATA_RETENTION_YEARS: int = 3  # 3-year retention for personal data
    LOG_RETENTION_DAYS: int = 90  # 90-day retention for logs
    
    # Data Minimization
    ENABLE_DATA_MINIMIZATION: bool = True
    ANONYMIZE_AFTER_YEARS: int = 3  # Anonymize personal data after 3 years
    
    # Privacy Logging
    ENABLE_PRIVACY_LOGGING: bool = True
    LOG_PII_ACCESS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()




