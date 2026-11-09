"""
Redis client configuration
"""
import redis
from typing import Optional

from app.core.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client singleton"""
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get Redis client instance"""
        if cls._instance is None:
            try:
                if settings.REDIS_URL:
                    cls._instance = redis.from_url(settings.REDIS_URL)
                else:
                    cls._instance = redis.Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD,
                        decode_responses=True
                    )
                # Test connection
                cls._instance.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise
        
        return cls._instance
    
    @classmethod
    def close(cls):
        """Close Redis connection"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None

