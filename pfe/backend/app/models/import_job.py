"""
ImportJob model for tracking internal catalog import runs.
"""

import enum

from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class ImportJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    catalog_source_id = Column(Integer, ForeignKey("catalog_sources.id"), nullable=False, index=True)

    status = Column(SQLEnum(ImportJobStatus), default=ImportJobStatus.PENDING, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Operational metadata
    celery_task_id = Column(String(255), nullable=True, index=True)
    stats = Column(JSON, nullable=True)  # counts, timings, etc.

    # Relationships
    catalog_source = relationship("CatalogSource", back_populates="import_jobs")

    __table_args__ = (
        Index("idx_import_job_user_status", "user_id", "status"),
    )

    def mark_running(self) -> None:
        self.status = ImportJobStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_completed(self, stats: dict | None = None) -> None:
        self.status = ImportJobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if stats is not None:
            self.stats = stats

    def mark_failed(self, error_message: str) -> None:
        self.status = ImportJobStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

