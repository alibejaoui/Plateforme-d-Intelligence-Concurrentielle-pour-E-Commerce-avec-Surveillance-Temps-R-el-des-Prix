"""
Price model for historical price tracking
"""
from sqlalchemy import Column, Float, Integer, ForeignKey, DateTime, String, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Price(BaseModel):
    """Price model for tracking historical prices"""
    __tablename__ = "prices"
    
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="EUR", nullable=False)
    availability = Column(String(50), nullable=True)  # "in_stock", "out_of_stock", "preorder"
    url = Column(String(1000), nullable=True)
    scraped_at = Column(DateTime, default=None, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="prices")
    competitor = relationship("Competitor", back_populates="prices")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_price_product_competitor", "product_id", "competitor_id"),
        Index("idx_price_scraped_at", "scraped_at"),
        Index("idx_price_product_date", "product_id", "created_at"),
    )

