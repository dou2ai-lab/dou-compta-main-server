# -----------------------------------------------------------------------------
# File: config.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Configuration for ERP service
# -----------------------------------------------------------------------------

"""
Configuration for ERP Integration Service
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Service
    SERVICE_NAME: str = "erp-service"
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    
    # ERP Provider
    ERP_PROVIDER: str = "odoo"  # sap, netsuite, odoo
    ERP_CONNECTION_TYPE: str = "api"  # api, sftp
    
    # SAP Configuration
    SAP_API_URL: Optional[str] = None
    SAP_USERNAME: Optional[str] = None
    SAP_PASSWORD: Optional[str] = None
    SAP_CLIENT: Optional[str] = None
    
    # NetSuite Configuration
    NETSUITE_ACCOUNT_ID: Optional[str] = None
    NETSUITE_CONSUMER_KEY: Optional[str] = None
    NETSUITE_CONSUMER_SECRET: Optional[str] = None
    NETSUITE_TOKEN_ID: Optional[str] = None
    NETSUITE_TOKEN_SECRET: Optional[str] = None
    
    # Odoo Configuration
    ODOO_URL: Optional[str] = None
    ODOO_DATABASE: Optional[str] = None
    ODOO_USERNAME: Optional[str] = None
    ODOO_PASSWORD: Optional[str] = None
    
    # SFTP Configuration
    SFTP_HOST: Optional[str] = None
    SFTP_PORT: int = 22
    SFTP_USERNAME: Optional[str] = None
    SFTP_PASSWORD: Optional[str] = None
    SFTP_KEY_FILE: Optional[str] = None
    SFTP_REMOTE_PATH: Optional[str] = None
    
    # Accounting Configuration
    DEFAULT_GL_ACCOUNT: Optional[str] = None
    VAT_ACCOUNT_MAPPING: dict = {}
    EXPENSE_ACCOUNT_MAPPING: dict = {}
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables not defined in Settings

settings = Settings()




