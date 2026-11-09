"""
Structured logging configuration
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from typing import Any

from app.core.settings import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging() -> None:
    """Setup application logging"""
    import os
    
    # Create logger
    logger = logging.getLogger("app")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.LOG_FORMAT == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
    logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        file_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        if settings.LOG_FORMAT == "json":
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
        logger.addHandler(file_handler)
    except Exception as e:
        # If file logging fails, continue with console logging only
        logger.warning(f"Failed to setup file logging: {e}")
    
    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(f"app.{name}")

