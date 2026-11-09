"""
InternalProduct model for the company catalog (imported automatically).
"""

from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class InternalProduct(BaseModel):
    __tablename__ = "internal_products"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String(500), nullable=False, index=True)
    brand = Column(String(255), nullable=True, index=True)
    sku = Column(String(100), nullable=True, index=True)
    gtin = Column(String(32), nullable=True, index=True)  # GTIN/EAN/UPC

    category = Column(String(255), nullable=True, index=True)
    url = Column(String(2000), nullable=False)
    image_url = Column(String(2000), nullable=True)

    price = Column(Float, nullable=True)
    currency = Column(String(10), default="EUR", nullable=False)
    availability = Column(String(50), nullable=True)

    description = Column(Text, nullable=True)

    # Relationships
    matches = relationship(
        "ProductMatch", back_populates="internal_product", cascade="all, delete-orphan"
    )
    unmatched_rows = relationship(
        "UnmatchedInternalProduct",
        back_populates="internal_product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_internal_product_user_sku", "user_id", "sku"),
        Index("idx_internal_product_user_gtin", "user_id", "gtin"),
        Index("idx_internal_product_user_category", "user_id", "category"),
    )

