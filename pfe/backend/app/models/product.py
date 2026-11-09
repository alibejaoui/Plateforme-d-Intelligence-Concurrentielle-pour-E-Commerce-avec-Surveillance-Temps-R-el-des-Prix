"""
Product model
"""
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Product(BaseModel):
    """Product model for tracking products"""
    __tablename__ = "products"
    
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, index=True, nullable=True)
    gtin = Column(String(32), nullable=True, index=True)  # optional GTIN/EAN
    category = Column(String(255), nullable=True, index=True)
    brand = Column(String(255), nullable=True, index=True)
    image_url = Column(String(1000), nullable=True)
    target_price = Column(Float, nullable=True)
    min_price_threshold = Column(Float, nullable=True)
    max_price_threshold = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relationships
    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_product_user_category", "user_id", "category"),
        Index("idx_product_sku_user", "sku", "user_id"),
    )

