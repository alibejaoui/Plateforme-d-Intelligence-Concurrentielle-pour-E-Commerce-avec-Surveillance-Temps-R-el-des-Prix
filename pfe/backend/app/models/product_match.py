"""
ProductMatch model linking internal products to competitor products.
Stores confidence and explanation for auditability.
"""

from sqlalchemy import Column, String, Float, Integer, ForeignKey, Index, JSON, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ProductMatch(BaseModel):
    __tablename__ = "product_matches"

    internal_product_id = Column(Integer, ForeignKey("internal_products.id"), nullable=False, index=True)
    competitor_product_id = Column(Integer, ForeignKey("competitor_products.id"), nullable=False, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    confidence_score = Column(Float, nullable=False, index=True)
    matching_method = Column(String(50), nullable=False, index=True)  # gtin | sku | brand_tokens | fuzzy | hybrid
    explanation = Column(JSON, nullable=True)  # structured reasons: matched_fields, scores, normalized strings, etc.
    review_status = Column(String(30), nullable=False, default="auto", index=True)  # auto | accepted | rejected
    review_note = Column(String(1000), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    internal_product = relationship("InternalProduct", back_populates="matches")
    competitor_product = relationship("CompetitorProduct", back_populates="matches")

    __table_args__ = (
        Index("ux_match_internal_competitor_product", "internal_product_id", "competitor_product_id", unique=True),
        Index("idx_match_competitor_confidence", "competitor_id", "confidence_score"),
    )

