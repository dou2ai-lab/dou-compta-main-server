# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Configuration settings for anomaly detection service
# -----------------------------------------------------------------------------

"""
Configuration for Anomaly Detection Service
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""
    
    # Service configuration
    SERVICE_NAME: str = "anomaly-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = "postgresql://dou_user:dou_password@postgres:5432/dou_expense_audit"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Anomaly Detection Settings
    ISOLATION_FOREST_CONTAMINATION: float = 0.1  # Expected proportion of anomalies
    ISOLATION_FOREST_N_ESTIMATORS: int = 100
    RISK_SCORE_THRESHOLD_HIGH: float = 0.7
    RISK_SCORE_THRESHOLD_MEDIUM: float = 0.4
    
    # Feature Engineering
    LOOKBACK_DAYS: int = 90  # Days to look back for baseline
    MIN_EXPENSES_FOR_BASELINE: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()




