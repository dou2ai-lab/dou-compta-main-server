# -----------------------------------------------------------------------------
# File: kms_client.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: KMS client abstraction for encryption key management
# -----------------------------------------------------------------------------

"""
KMS Client Abstraction
Supports AWS KMS, Azure Key Vault, GCP KMS, and fallback for development
"""
import os
import secrets
from typing import Optional
import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger()


class KMSClientInterface(ABC):
    """Abstract interface for KMS clients"""
    
    @abstractmethod
    async def get_key(self, key_id: str) -> bytes:
        """Get encryption key from KMS"""
        pass
    
    @abstractmethod
    async def generate_random_bytes(self, length: int) -> bytes:
        """Generate random bytes (for salt)"""
        pass
    
    @abstractmethod
    async def get_tenant_key(self, tenant_id: str) -> bytes:
        """Get tenant-specific encryption key"""
        pass


class AWSKMSClient(KMSClientInterface):
    """AWS KMS client implementation"""
    
    def __init__(self, region: str = "eu-west-1"):
        try:
            import boto3
            self.kms_client = boto3.client('kms', region_name=region)
            self.region = region
        except ImportError:
            logger.warning("boto3_not_installed", message="AWS KMS not available, install boto3")
            self.kms_client = None
        except Exception as e:
            logger.error("aws_kms_init_error", error=str(e))
            self.kms_client = None
    
    async def get_key(self, key_id: str) -> bytes:
        """Get key from AWS KMS"""
        if not self.kms_client:
            raise ValueError("AWS KMS client not initialized")
        
        try:
            # For data keys, use generate_data_key
            response = self.kms_client.generate_data_key(
                KeyId=key_id,
                KeySpec='AES_256'
            )
            return response['Plaintext']
        except Exception as e:
            logger.error("aws_kms_get_key_error", key_id=key_id, error=str(e))
            raise
    
    async def generate_random_bytes(self, length: int) -> bytes:
        """Generate random bytes using AWS KMS"""
        if not self.kms_client:
            return secrets.token_bytes(length)
        
        try:
            response = self.kms_client.generate_random(NumberOfBytes=length)
            return response['Plaintext']
        except Exception as e:
            logger.warning("aws_kms_random_error", error=str(e))
            return secrets.token_bytes(length)
    
    async def get_tenant_key(self, tenant_id: str) -> bytes:
        """Get tenant-specific key"""
        key_id = f"alias/tenant-{tenant_id}"
        return await self.get_key(key_id)


class AzureKeyVaultClient(KMSClientInterface):
    """Azure Key Vault client implementation"""
    
    def __init__(self, vault_url: Optional[str] = None):
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.keys import KeyClient
            
            if vault_url:
                credential = DefaultAzureCredential()
                self.key_client = KeyClient(vault_url=vault_url, credential=credential)
                self.vault_url = vault_url
            else:
                self.key_client = None
                self.vault_url = None
        except ImportError:
            logger.warning("azure_keyvault_not_installed", message="Azure Key Vault not available")
            self.key_client = None
        except Exception as e:
            logger.error("azure_keyvault_init_error", error=str(e))
            self.key_client = None
    
    async def get_key(self, key_id: str) -> bytes:
        """Get key from Azure Key Vault"""
        if not self.key_client:
            raise ValueError("Azure Key Vault client not initialized")
        
        try:
            key = self.key_client.get_key(key_id)
            # Azure returns key material, convert to bytes
            return key.key.to_bytes()
        except Exception as e:
            logger.error("azure_keyvault_get_key_error", key_id=key_id, error=str(e))
            raise
    
    async def generate_random_bytes(self, length: int) -> bytes:
        """Generate random bytes"""
        return secrets.token_bytes(length)
    
    async def get_tenant_key(self, tenant_id: str) -> bytes:
        """Get tenant-specific key"""
        key_name = f"tenant-{tenant_id}-key"
        return await self.get_key(key_name)


class GCPKMSClient(KMSClientInterface):
    """GCP KMS client implementation"""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "europe-west1"):
        try:
            from google.cloud import kms
            
            if project_id:
                self.kms_client = kms.KeyManagementServiceClient()
                self.project_id = project_id
                self.location = location
            else:
                self.kms_client = None
                self.project_id = None
                self.location = location
        except ImportError:
            logger.warning("gcp_kms_not_installed", message="GCP KMS not available")
            self.kms_client = None
        except Exception as e:
            logger.error("gcp_kms_init_error", error=str(e))
            self.kms_client = None
    
    async def get_key(self, key_id: str) -> bytes:
        """Get key from GCP KMS"""
        if not self.kms_client or not self.project_id:
            raise ValueError("GCP KMS client not initialized")
        
        try:
            key_ring_name = f"projects/{self.project_id}/locations/{self.location}/keyRings/dou-keyring"
            key_name = f"{key_ring_name}/cryptoKeys/{key_id}"
            
            # Generate data key
            response = self.kms_client.generate_data_key(
                name=key_name,
                key_id=key_id,
                length=32
            )
            return response.plaintext
        except Exception as e:
            logger.error("gcp_kms_get_key_error", key_id=key_id, error=str(e))
            raise
    
    async def generate_random_bytes(self, length: int) -> bytes:
        """Generate random bytes"""
        return secrets.token_bytes(length)
    
    async def get_tenant_key(self, tenant_id: str) -> bytes:
        """Get tenant-specific key"""
        key_id = f"tenant-{tenant_id}"
        return await self.get_key(key_id)


class DevelopmentKMSClient(KMSClientInterface):
    """Development fallback KMS client (NOT FOR PRODUCTION)"""
    
    def __init__(self):
        logger.warning("using_development_kms", message="Development KMS client - NOT FOR PRODUCTION")
        # Store keys in memory (volatile, for development only)
        self._key_cache = {}
    
    async def get_key(self, key_id: str) -> bytes:
        """Get key from environment or generate"""
        if key_id in self._key_cache:
            return self._key_cache[key_id]
        
        # Try to get from environment
        env_key = os.getenv(f"ENCRYPTION_KEY_{key_id.replace('-', '_').upper()}")
        if env_key:
            key = env_key.encode()
            self._key_cache[key_id] = key
            return key
        
        # Generate a new key (development only)
        key = secrets.token_bytes(32)
        self._key_cache[key_id] = key
        logger.warning("generated_dev_key", key_id=key_id, message="Generated development key - NOT SECURE")
        return key
    
    async def generate_random_bytes(self, length: int) -> bytes:
        """Generate random bytes using secrets module"""
        return secrets.token_bytes(length)
    
    async def get_tenant_key(self, tenant_id: str) -> bytes:
        """Get tenant-specific key"""
        key_id = f"tenant-{tenant_id}"
        return await self.get_key(key_id)


def get_kms_client() -> KMSClientInterface:
    """
    Factory function to get appropriate KMS client based on environment
    
    Priority:
    1. AWS KMS (if AWS_KMS_KEY_ID and AWS_REGION set)
    2. Azure Key Vault (if AZURE_KEY_VAULT_URL set)
    3. GCP KMS (if GCP_PROJECT_ID and GCP_KMS_LOCATION set)
    4. Development fallback (NOT FOR PRODUCTION)
    """
    kms_provider = os.getenv("KMS_PROVIDER", "").lower()
    
    if kms_provider == "aws" or (os.getenv("AWS_KMS_KEY_ID") and os.getenv("AWS_REGION")):
        key_id = os.getenv("AWS_KMS_KEY_ID", "")
        region = os.getenv("AWS_REGION", "eu-west-1")
        if key_id:
            return AWSKMSClient(region=region)
    
    if kms_provider == "azure" or os.getenv("AZURE_KEY_VAULT_URL"):
        vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        if vault_url:
            return AzureKeyVaultClient(vault_url=vault_url)
    
    if kms_provider == "gcp" or (os.getenv("GCP_PROJECT_ID") and os.getenv("GCP_KMS_LOCATION")):
        project_id = os.getenv("GCP_PROJECT_ID")
        location = os.getenv("GCP_KMS_LOCATION", "europe-west1")
        if project_id:
            return GCPKMSClient(project_id=project_id, location=location)
    
    # Development fallback
    if os.getenv("ENVIRONMENT", "development") == "production":
        logger.error("no_kms_configured_production", message="PRODUCTION ENVIRONMENT MUST USE KMS")
        raise ValueError("Production environment requires KMS configuration")
    
    return DevelopmentKMSClient()

