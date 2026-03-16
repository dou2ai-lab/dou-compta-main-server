# -----------------------------------------------------------------------------
# File: encryption.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Encryption service for file encryption at rest using AES-256
# -----------------------------------------------------------------------------

"""
Encryption Service for File Encryption
AES-256 encryption at rest with KMS integration
"""
import os
from typing import Optional, Dict
import structlog
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import asyncio

from .config import settings
from .kms_client import get_kms_client, KMSClientInterface

logger = structlog.get_logger()

class EncryptionService:
    """File encryption service using AES-256 (Fernet) with KMS key management"""
    
    def __init__(self):
        self.kms_key_id = settings.KMS_KEY_ID
        self.kms_client: Optional[KMSClientInterface] = None
        self._tenant_ciphers: Dict[str, Fernet] = {}  # Cache ciphers per tenant
        self._init_kms()
    
    def _init_kms(self):
        """Initialize KMS client"""
        try:
            self.kms_client = get_kms_client()
            logger.info("kms_client_initialized", provider=type(self.kms_client).__name__)
        except Exception as e:
            logger.error("kms_init_failed", error=str(e))
            if os.getenv("ENVIRONMENT", "development") == "production":
                raise ValueError(f"KMS initialization failed in production: {e}")
            # Fallback for development
            self.kms_client = None
    
    async def _get_tenant_cipher(self, tenant_id: str) -> Fernet:
        """Get or create Fernet cipher for tenant"""
        if tenant_id in self._tenant_ciphers:
            return self._tenant_ciphers[tenant_id]
        
        # Get master key from KMS
        if self.kms_client:
            try:
                master_key = await self.kms_client.get_tenant_key(tenant_id)
            except Exception as e:
                logger.error("kms_get_tenant_key_failed", tenant_id=tenant_id, error=str(e))
                raise ValueError(f"Failed to get encryption key for tenant: {e}")
        else:
            # Development fallback - use environment variable
            master_key = os.getenv("ENCRYPTION_MASTER_KEY", "").encode()
            if not master_key:
                raise ValueError("ENCRYPTION_MASTER_KEY must be set in development")
        
        # Generate random salt per tenant
        if self.kms_client:
            salt = await self.kms_client.generate_random_bytes(16)
        else:
            import secrets
            salt = secrets.token_bytes(16)
        
        # Derive Fernet key from master key and salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        cipher = Fernet(key)
        
        # Cache cipher for this tenant
        self._tenant_ciphers[tenant_id] = cipher
        
        logger.info("tenant_cipher_created", tenant_id=tenant_id, salt_length=len(salt))
        return cipher
    
    async def generate_key(self, tenant_id: str) -> str:
        """
        Generate or retrieve encryption key for tenant
        
        Returns: Key ID (stored in KMS or database)
        """
        key_id = f"tenant-{tenant_id}"
        logger.info("encryption_key_generated", key_id=key_id, tenant_id=tenant_id)
        return key_id
    
    async def encrypt(self, data: bytes, key_id: str, tenant_id: Optional[str] = None) -> bytes:
        """
        Encrypt data using Fernet (AES-256)
        
        Args:
            data: Plaintext data to encrypt
            key_id: Encryption key ID (for backward compatibility)
            tenant_id: Tenant ID (required for per-tenant encryption)
        
        Returns: Encrypted data
        """
        try:
            # Extract tenant_id from key_id if not provided
            if not tenant_id and key_id.startswith("tenant-"):
                tenant_id = key_id.replace("tenant-", "")
            elif not tenant_id:
                # Fallback: try to extract from key_id format
                tenant_id = key_id.replace("key-", "")
            
            if not tenant_id:
                raise ValueError("tenant_id is required for encryption")
            
            cipher = await self._get_tenant_cipher(tenant_id)
            encrypted = cipher.encrypt(data)
            logger.info("data_encrypted", key_id=key_id, tenant_id=tenant_id, data_size=len(data), encrypted_size=len(encrypted))
            return encrypted
        except Exception as e:
            logger.error("encryption_failed", error=str(e), key_id=key_id, tenant_id=tenant_id)
            raise Exception(f"Failed to encrypt data: {e}")
    
    async def decrypt(self, encrypted_data: bytes, key_id: str, tenant_id: Optional[str] = None) -> bytes:
        """
        Decrypt data using Fernet
        
        Args:
            encrypted_data: Encrypted data
            key_id: Encryption key ID (for backward compatibility)
            tenant_id: Tenant ID (required for per-tenant decryption)
        
        Returns: Decrypted data
        """
        try:
            # Extract tenant_id from key_id if not provided
            if not tenant_id and key_id.startswith("tenant-"):
                tenant_id = key_id.replace("tenant-", "")
            elif not tenant_id:
                # Fallback: try to extract from key_id format
                tenant_id = key_id.replace("key-", "")
            
            if not tenant_id:
                raise ValueError("tenant_id is required for decryption")
            
            cipher = await self._get_tenant_cipher(tenant_id)
            decrypted = cipher.decrypt(encrypted_data)
            logger.info("data_decrypted", key_id=key_id, tenant_id=tenant_id, encrypted_size=len(encrypted_data), decrypted_size=len(decrypted))
            return decrypted
        except Exception as e:
            logger.error("decryption_failed", error=str(e), key_id=key_id, tenant_id=tenant_id)
            raise Exception(f"Failed to decrypt data: {e}")









