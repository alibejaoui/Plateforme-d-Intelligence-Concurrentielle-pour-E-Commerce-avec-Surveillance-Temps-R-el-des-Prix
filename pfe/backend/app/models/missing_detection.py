"""
Models for missing/new product detection outputs.
"""

from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MissingProduct(BaseModel):
    """
    Competitor product that does not exist internally (no match).
    """

    __tablename__ = "missing_products"

    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    competitor_product_id = Column(Integer, ForeignKey("competitor_products.id"), nullable=False, index=True)

    opportunity_score = Column(Float, nullable=True, index=True)
    reason = Column(String(100), nullable=True, index=True)  # e.g. "no_candidate", "low_confidence"
    notes = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # extra scoring signals

    competitor_product = relationship("CompetitorProduct", back_populates="missing_rows")

    __table_args__ = (
        Index("ux_missing_competitor_product", "competitor_id", "competitor_product_id", unique=True),
    )


class UnmatchedInternalProduct(BaseModel):
    """
    Internal product that could not be found at a competitor (no match).
    """

    __tablename__ = "unmatched_internal_products"

    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    internal_product_id = Column(Integer, ForeignKey("internal_products.id"), nullable=False, index=True)

    coverage_status = Column(String(50), nullable=True, index=True)  # not_found | blocked | unknown
    details = Column(JSON, nullable=True)

    internal_product = relationship("InternalProduct", back_populates="unmatched_rows")

    __table_args__ = (
        Index("ux_unmatched_internal_competitor", "competitor_id", "internal_product_id", unique=True),
    )

