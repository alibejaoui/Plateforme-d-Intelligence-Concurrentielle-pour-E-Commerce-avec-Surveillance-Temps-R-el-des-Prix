"""
CrawlSession models for competitor catalog crawling runs.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CrawlSessionStatus(str, enum.Enum):
    PENDING = "pending"
    DISCOVERING = "discovering"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlSession(BaseModel):
    __tablename__ = "crawl_sessions"

    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    status = Column(
        SQLEnum(
            CrawlSessionStatus,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            name="crawlsessionstatus",
        ),
        default=CrawlSessionStatus.PENDING,
        nullable=False,
        index=True,
    )
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    seed_url = Column(String(2000), nullable=True)  # starting category/listing URL
    config_snapshot = Column(Text, nullable=True)  # JSON string (competitor.scraping_config snapshot)

    stats = Column(JSON, nullable=True)  # discovered_count, extracted_count, errors_count
    celery_group_id = Column(String(255), nullable=True, index=True)

    items = relationship("CrawlSessionItem", back_populates="crawl_session", cascade="all, delete-orphan")
    errors = relationship("CrawlError", back_populates="crawl_session", cascade="all, delete-orphan")

    def mark_started(self, status: CrawlSessionStatus) -> None:
        self.status = status
        self.started_at = self.started_at or datetime.utcnow()

    def mark_completed(self, stats: dict | None = None) -> None:
        self.status = CrawlSessionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if stats is not None:
            self.stats = stats

    def mark_failed(self, error_message: str) -> None:
        self.status = CrawlSessionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()


class CrawlSessionItem(BaseModel):
    __tablename__ = "crawl_session_items"

    crawl_session_id = Column(Integer, ForeignKey("crawl_sessions.id"), nullable=False, index=True)
    competitor_product_id = Column(Integer, ForeignKey("competitor_products.id"), nullable=False, index=True)
    discovered_url = Column(String(2000), nullable=True)

    crawl_session = relationship("CrawlSession", back_populates="items")
    competitor_product = relationship("CompetitorProduct", back_populates="crawl_sessions")

    __table_args__ = (
        Index("idx_crawl_item_session_product", "crawl_session_id", "competitor_product_id"),
    )


class CrawlError(BaseModel):
    __tablename__ = "crawl_errors"

    crawl_session_id = Column(Integer, ForeignKey("crawl_sessions.id"), nullable=False, index=True)
    stage = Column(String(50), nullable=False, index=True)  # discovery | extraction
    url = Column(String(2000), nullable=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    crawl_session = relationship("CrawlSession", back_populates="errors")

    __table_args__ = (
        Index("idx_crawl_error_session_stage", "crawl_session_id", "stage"),
    )

