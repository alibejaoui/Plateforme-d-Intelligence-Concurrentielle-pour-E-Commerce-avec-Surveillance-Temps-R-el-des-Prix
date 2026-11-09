"""
Database configuration and session management
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.settings import settings
from app.models.base import Base

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_users_role_column() -> None:
    """
    Existing MySQL databases may have been created before `users.role` existed.
    Without this column, any query on User fails with 500 (OperationalError 1054).
    """
    try:
        inspector = inspect(engine)
        if not inspector.has_table("users"):
            return
        columns = {c["name"].lower() for c in inspector.get_columns("users")}
        if "role" in columns:
            return
        with engine.begin() as conn:
            conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'analyst'"
                )
            )
    except Exception as e:
        import logging

        logging.getLogger("app.database").warning(
            "Could not ensure users.role column (add it manually if login fails): %s",
            e,
        )


def init_db() -> None:
    """
    Initialize database tables
    """
    try:
        # Import all models to register them with Base
        from app.models import (
            user,
            product,
            competitor,
            price,
            alert,
            scraping_job,
            source,
            catalog_source,
            import_job,
            internal_product,
            competitor_product,
            crawl_session,
            product_match,
            missing_detection,
            alert_rule,
            competitive_alert,
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        _ensure_users_role_column()
    except Exception as e:
        # Log error but don't crash the app
        import logging
        logger = logging.getLogger("app.database")
        logger.warning(f"Failed to initialize database tables: {e}")
        logger.info("Database tables will be created when database is available")
