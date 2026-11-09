"""
Cache service for Redis operations
"""
import json
from typing import Any, Optional
from datetime import timedelta

from app.cache.redis_client import RedisClient
from app.core.logging import get_logger

logger = get_logger(__name__)


class _NullRedis:
    def get(self, key: str):
        return None

    def setex(self, key: str, ttl: int, value: str) -> bool:
        return False

    def delete(self, *keys: str) -> int:
        return 0

    def exists(self, key: str) -> bool:
        return False

    def keys(self, pattern: str) -> list:
        return []


class CacheService:
    """Service for cache operations"""
    
    def __init__(self):
        self.logger = logger
        try:
            self.redis = RedisClient.get_client()
        except Exception as e:
            self.logger.warning(f"Redis unavailable; cache disabled: {str(e)}")
            self.redis = _NullRedis()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        try:
            serialized = json.dumps(value)
            return self.redis.setex(key, ttl, serialized)
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.redis.exists(key))
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            self.logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0

