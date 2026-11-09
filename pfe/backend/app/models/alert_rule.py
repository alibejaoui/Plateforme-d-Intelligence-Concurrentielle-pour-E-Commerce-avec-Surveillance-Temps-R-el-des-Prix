"""
Alert rules model for competitive intelligence alerts engine.
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, JSON, Index

from app.models.base import BaseModel


class AlertRule(BaseModel):
    __tablename__ = "alert_rules"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    competitor_id = Column(Integer, ForeignKey("competitors.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    rule_type = Column(String(80), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    threshold_value = Column(Float, nullable=True)
    config = Column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_alert_rules_user_type", "user_id", "rule_type"),
    )

