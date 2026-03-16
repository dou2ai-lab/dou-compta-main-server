# -----------------------------------------------------------------------------
# File: test_encryption.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 14-12-2025
# Description: Unit tests for encryption service
# -----------------------------------------------------------------------------

"""
Unit Tests for Encryption Service
"""
import pytest
import os
from services.file_service.encryption import EncryptionService
from services.file_service.kms_client import DevelopmentKMSClient


@pytest.mark.asyncio
async def test_encryption_decryption_roundtrip():
    """Test encryption and decryption roundtrip"""
    # Use development KMS for testing
    os.environ["ENVIRONMENT"] = "development"
    os.environ["ENCRYPTION_MASTER_KEY"] = "test-master-key-12345"
    
    service = EncryptionService()
    tenant_id = "test-tenant-123"
    
    # Test data
    original_data = b"Test receipt data for encryption"
    
    # Encrypt
    key_id = await service.generate_key(tenant_id)
    encrypted = await service.encrypt(original_data, key_id, tenant_id)
    
    assert encrypted != original_data
    assert len(encrypted) > len(original_data)
    
    # Decrypt
    decrypted = await service.decrypt(encrypted, key_id, tenant_id)
    
    assert decrypted == original_data


@pytest.mark.asyncio
async def test_per_tenant_encryption():
    """Test that different tenants get different encryption keys"""
    os.environ["ENVIRONMENT"] = "development"
    os.environ["ENCRYPTION_MASTER_KEY"] = "test-master-key-12345"
    
    service = EncryptionService()
    
    test_data = b"Test data"
    
    # Encrypt for tenant 1
    encrypted1 = await service.encrypt(test_data, "tenant-1", "tenant-1")
    
    # Encrypt for tenant 2
    encrypted2 = await service.encrypt(test_data, "tenant-2", "tenant-2")
    
    # Encryptions should be different (different salts)
    assert encrypted1 != encrypted2
    
    # Each should decrypt correctly with its own tenant
    decrypted1 = await service.decrypt(encrypted1, "tenant-1", "tenant-1")
    decrypted2 = await service.decrypt(encrypted2, "tenant-2", "tenant-2")
    
    assert decrypted1 == test_data
    assert decrypted2 == test_data


@pytest.mark.asyncio
async def test_encryption_fails_with_wrong_tenant():
    """Test that decryption fails with wrong tenant"""
    os.environ["ENVIRONMENT"] = "development"
    os.environ["ENCRYPTION_MASTER_KEY"] = "test-master-key-12345"
    
    service = EncryptionService()
    
    test_data = b"Test data"
    
    # Encrypt for tenant 1
    encrypted = await service.encrypt(test_data, "tenant-1", "tenant-1")
    
    # Try to decrypt with wrong tenant (should fail)
    with pytest.raises(Exception):
        await service.decrypt(encrypted, "tenant-1", "tenant-2")

