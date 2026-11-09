"""
Competitor model
"""
from sqlalchemy import Column, String, Text, Boolean, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Competitor(BaseModel):
    """Competitor model for tracking competitor websites"""
    __tablename__ = "competitors"
    
    name = Column(String(255), nullable=False, unique=True, index=True)
    website_url = Column(String(1000), nullable=False)
    base_url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    scraping_config = Column(Text, nullable=True)  # JSON string for scraping configuration
    rate_limit_per_minute = Column(Integer, default=10, nullable=False)
    
    # Relationships
    prices = relationship("Price", back_populates="competitor", cascade="all, delete-orphan")
    scraping_jobs = relationship("ScrapingJob", back_populates="competitor", cascade="all, delete-orphan")
    competitor_products = relationship(
        "CompetitorProduct", backref="competitor", cascade="all, delete-orphan"
    )
    crawl_sessions = relationship(
        "CrawlSession", backref="competitor", cascade="all, delete-orphan"
    )

