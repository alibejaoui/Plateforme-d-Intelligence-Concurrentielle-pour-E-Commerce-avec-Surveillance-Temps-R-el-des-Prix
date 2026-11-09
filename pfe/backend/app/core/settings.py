"""
Configuration settings using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # -----------------------
    # Application
    # -----------------------
    APP_NAME: str = "Plateforme d'Intelligence Concurrentielle"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # -----------------------
    # Database
    # -----------------------
    # Host-run default: use 127.0.0.1:3307 (published Docker port).
    # In Docker containers, override via env to use host "mysql".
    DATABASE_URL: str = "mysql+pymysql://app_user:app_password@127.0.0.1:3307/competitive_intelligence"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # -----------------------
    # Redis
    # -----------------------
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    # -----------------------
    # RabbitMQ / Celery
    # -----------------------
    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # -----------------------
    # Security
    # -----------------------
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -----------------------
    # CORS
    # -----------------------
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173"

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from string"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    # -----------------------
    # Logging
    # -----------------------
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # -----------------------
    # Scraping
    # -----------------------
    SCRAPING_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    SCRAPING_TIMEOUT: int = 30
    SCRAPING_RETRY_ATTEMPTS: int = 3

    # -----------------------
    # Rate Limiting
    # -----------------------
    RATE_LIMIT_PER_MINUTE: int = 60

    # -----------------------
    # Pydantic Config
    # -----------------------
    class Config:
        env_file = ".env"
        case_sensitive = True


# Instantiate the settings
settings = Settings()