"""
Utility to wait for database to be ready
"""
import time
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def wait_for_db(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """
    Wait for database to be ready
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_interval: Seconds to wait between retries
    
    Returns:
        True if database is ready, False otherwise
    """
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5}
    )
    
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database is ready!")
            return True
        except OperationalError as e:
            if attempt < max_retries - 1:
                logger.info(f"Database not ready yet (attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_interval)
            else:
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error while waiting for database: {e}")
            return False
    
    return False


if __name__ == "__main__":
    success = wait_for_db()
    sys.exit(0 if success else 1)

