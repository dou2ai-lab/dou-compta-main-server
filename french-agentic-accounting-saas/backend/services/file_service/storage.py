# -----------------------------------------------------------------------------
# File: storage.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 21-11-2025
# Description: Object storage service abstraction supporting S3, GCS, and Azure Blob (EU regions only)
# -----------------------------------------------------------------------------

"""
Object Storage Service
Supports S3, GCS, Azure Blob (EU regions only), and local file storage for development
"""
import os
from typing import Optional
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import structlog

from .config import settings

logger = structlog.get_logger()

class StorageService:
    """Abstraction for object storage"""
    
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER
        self.bucket = settings.STORAGE_BUCKET
        self.region = settings.STORAGE_REGION
        
        # Check if AWS credentials are provided
        has_aws_creds = settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY
        
        # For development: fallback to local storage if S3 credentials are missing
        if self.provider == "s3" and not has_aws_creds:
            logger.warning("AWS credentials not provided, using local file storage for development")
            self.provider = "local"
        if self.provider == "local":
            # Create local storage directory (Windows-compatible)
            import tempfile
            base_dir = os.environ.get("LOCAL_STORAGE_PATH") or str(Path(tempfile.gettempdir()) / "dou-receipts")
            self.local_storage_path = Path(base_dir)
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
        elif self.provider == "s3":
            # Validate EU region only for S3
            if not self._is_eu_region(self.region):
                raise ValueError(f"Storage region must be in EU. Current: {self.region}")
            
            self.client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        # TODO: Add GCS and Azure Blob clients
    
    def _is_eu_region(self, region: str) -> bool:
        """Validate region is in EU"""
        eu_regions = [
            "eu-west-1", "eu-west-2", "eu-west-3",
            "eu-central-1", "eu-central-2",
            "eu-north-1", "eu-south-1"
        ]
        return region in eu_regions
    
    async def upload_file(
        self,
        file_content: bytes,
        file_id: str,
        tenant_id: str,
        file_name: str
    ) -> str:
        """
        Upload file to object storage
        
        Returns: Storage path (S3 key, GCS path, etc.)
        """
        # Generate storage path: tenant_id/YYYY/MM/DD/file_id
        from datetime import datetime
        now = datetime.utcnow()
        storage_path = f"{tenant_id}/{now.year}/{now.month:02d}/{now.day:02d}/{file_id}"
        
        try:
            if self.provider == "s3":
                self.client.put_object(
                    Bucket=self.bucket,
                    Key=storage_path,
                    Body=file_content,
                    ServerSideEncryption='AES256'  # Additional encryption at storage level
                )
                return f"s3://{self.bucket}/{storage_path}"
            elif self.provider == "local":
                # Local file storage for development
                local_file_path = self.local_storage_path / storage_path
                try:
                    # Ensure parent directories exist
                    local_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write file content
                    with open(local_file_path, 'wb') as f:
                        f.write(file_content)
                    
                    logger.info("file_uploaded_to_local_storage", path=str(local_file_path), file_size=len(file_content))
                    return f"local://{storage_path}"
                except OSError as e:
                    logger.error("local_storage_write_failed", error=str(e), path=str(local_file_path), exc_info=True)
                    raise Exception(f"Failed to write file to local storage: {str(e)}")
                except Exception as e:
                    logger.error("local_storage_error", error=str(e), path=str(local_file_path), exc_info=True)
                    raise Exception(f"Local storage error: {str(e)}")
        except ClientError as e:
            logger.error("storage_upload_failed", error=str(e))
            raise Exception(f"Failed to upload file to storage: {e}")
        except Exception as e:
            logger.error("storage_upload_failed", error=str(e))
            raise Exception(f"Failed to upload file to storage: {e}")
    
    async def download_file(self, storage_path: str) -> bytes:
        """Download file from object storage"""
        try:
            if storage_path.startswith("s3://"):
                # Parse S3 path
                bucket, key = storage_path.replace("s3://", "").split("/", 1)
                response = self.client.get_object(Bucket=bucket, Key=key)
                return response['Body'].read()
            elif storage_path.startswith("local://"):
                # Local file storage
                key = storage_path.replace("local://", "")
                local_file_path = self.local_storage_path / key
                with open(local_file_path, 'rb') as f:
                    return f.read()
        except ClientError as e:
            logger.error("storage_download_failed", error=str(e))
            raise Exception(f"Failed to download file from storage: {e}")
        except Exception as e:
            logger.error("storage_download_failed", error=str(e))
            raise Exception(f"Failed to download file from storage: {e}")
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from object storage"""
        try:
            if storage_path.startswith("s3://"):
                bucket, key = storage_path.replace("s3://", "").split("/", 1)
                self.client.delete_object(Bucket=bucket, Key=key)
                return True
            elif storage_path.startswith("local://"):
                key = storage_path.replace("local://", "")
                local_file_path = self.local_storage_path / key
                if local_file_path.exists():
                    local_file_path.unlink()
                return True
        except ClientError as e:
            logger.error("storage_delete_failed", error=str(e))
            return False
        except Exception as e:
            logger.error("storage_delete_failed", error=str(e))
            return False
    
    def generate_presigned_url(
        self,
        storage_path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary file access
        
        Returns: Presigned URL
        """
        try:
            if self.provider == "s3":
                bucket, key = storage_path.replace("s3://", "").split("/", 1)
                url = self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket, 'Key': key},
                    ExpiresIn=expires_in
                )
                return url
        except ClientError as e:
            logger.error("presigned_url_generation_failed", error=str(e))
            raise Exception(f"Failed to generate presigned URL: {e}")









