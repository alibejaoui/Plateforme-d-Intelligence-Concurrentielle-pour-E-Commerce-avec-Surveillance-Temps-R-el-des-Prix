"""
CatalogSource model for internal catalog ingestion sources.
"""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CatalogSource(BaseModel):
    """
    Represents a source used to import the internal catalog.

    Examples:
    - sitemap.xml
    - Google Merchant / product feed (XML/CSV)
    - category crawling fallback
    """

    __tablename__ = "catalog_sources"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, index=True)  # sitemap | feed | crawl
    source_url = Column(String(2000), nullable=False)
    name = Column(String(255), nullable=True)
    config = Column(Text, nullable=True)  # JSON string for source-specific options

    # Relationships
    import_jobs = relationship(
        "ImportJob", back_populates="catalog_source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_catalog_source_user_type", "user_id", "source_type"),
    )

