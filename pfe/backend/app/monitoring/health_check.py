"""
Health check utilities
"""
from datetime import datetime
from typing import Dict, Any

from app.cache.redis_client import RedisClient
from app.core.database import engine
from app.core.logging import get_logger

logger = get_logger(__name__)


def check_health() -> Dict[str, Any]:
    """Perform health check on all services"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = RedisClient.get_client()
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    return health_status

