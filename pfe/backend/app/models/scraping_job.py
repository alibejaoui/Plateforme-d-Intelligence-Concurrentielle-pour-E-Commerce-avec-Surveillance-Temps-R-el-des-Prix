"""
ScrapingJob model for tracking scraping tasks
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapingJob(BaseModel):
    """ScrapingJob model for tracking scraping tasks"""
    __tablename__ = "scraping_jobs"
    
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    job_type = Column(String(50), nullable=False)  # "single", "batch", "scheduled"
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)  # Store scraping results
    celery_task_id = Column(String(255), nullable=True, index=True)
    
    # Relationships
    competitor = relationship("Competitor", back_populates="scraping_jobs")

