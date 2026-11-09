"""
CompetitorProduct model for competitor catalog items discovered via crawling.
"""

from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CompetitorProduct(BaseModel):
    __tablename__ = "competitor_products"

    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)

    title = Column(String(500), nullable=False, index=True)
    brand = Column(String(255), nullable=True, index=True)
    sku = Column(String(100), nullable=True, index=True)
    gtin = Column(String(32), nullable=True, index=True)
    category = Column(String(255), nullable=True, index=True)

    url = Column(String(2000), nullable=False)
    image_url = Column(String(2000), nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    availability = Column(String(50), nullable=True)

    raw = Column(Text, nullable=True)  # JSON string snapshot of raw fields if needed

    # Relationships
    crawl_sessions = relationship(
        "CrawlSessionItem",
        back_populates="competitor_product",
        cascade="all, delete-orphan",
    )
    matches = relationship(
        "ProductMatch", back_populates="competitor_product", cascade="all, delete-orphan"
    )
    missing_rows = relationship(
        "MissingProduct", back_populates="competitor_product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "idx_competitor_product_competitor_url",
            "competitor_id",
            "url",
            mysql_length={"url": 255},
        ),
        Index("idx_competitor_product_competitor_sku", "competitor_id", "sku"),
        Index("idx_competitor_product_competitor_gtin", "competitor_id", "gtin"),
    )

