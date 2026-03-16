# -----------------------------------------------------------------------------
# File: cache_service.py
# Company: Euron (A Subsidiary of EngageSphere Technology Private Limited)
# Created On: 10-12-2025
# Description: Redis caching service for performance optimization
# -----------------------------------------------------------------------------

"""
Redis Caching Service
Provides caching layer for frequently accessed data
"""
from typing import Any, Optional, Dict
import json
import structlog
import redis.asyncio as redis
from datetime import timedelta

logger = structlog.get_logger()

class CacheService:
    """Redis caching service"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("redis_connected", url=self.redis_url)
        except Exception as e:
            logger.error("redis_connection_error", error=str(e))
            # Fallback to no-op if Redis is unavailable
            self.client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete keys matching pattern"""
        if not self.client:
            return 0
        
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("cache_delete_pattern_error", pattern=pattern, error=str(e))
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False
    
    # Cache key generators
    @staticmethod
    def expense_key(expense_id: str) -> str:
        return f"expense:{expense_id}"
    
    @staticmethod
    def user_key(user_id: str) -> str:
        return f"user:{user_id}"
    
    @staticmethod
    def policy_key(policy_id: str) -> str:
        return f"policy:{policy_id}"
    
    @staticmethod
    def receipt_key(receipt_id: str) -> str:
        return f"receipt:{receipt_id}"
    
    @staticmethod
    def tenant_key(tenant_id: str) -> str:
        return f"tenant:{tenant_id}"
    
    @staticmethod
    def expense_list_key(tenant_id: str, filters: Dict[str, Any]) -> str:
        """Generate cache key for expense list queries"""
        filter_str = json.dumps(filters, sort_keys=True, default=str)
        return f"expense_list:{tenant_id}:{filter_str}"




